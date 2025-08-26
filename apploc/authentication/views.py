from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth import authenticate
from .forms import TenantSignupForm, LoginForm
from ..models import Owner, Property, Tenant
from .utils import login_user, logout_user

def tenant_signup(request):
    if request.method == 'POST':
        form = TenantSignupForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            if Tenant.objects.filter(email=email).exists() or Owner.objects.filter(email=email).exists():
                messages.error(request, 'Email already exists.')
                return render(request, 'authentication/signup.html', {'form': form})
            tenant = form.save(commit=False)
            tenant.password = make_password(form.cleaned_data['password'])
            tenant.save()
            messages.success(request, 'Account created successfully. Please log in.')
            return redirect('login')
    else:
        form = TenantSignupForm()
    return render(request, 'authentication/signup.html', {'form': form})

def login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            
            # Check if the user is an admin (superuser)
            user = authenticate(request, username=email, password=password)
            if user is not None and user.is_staff:
                from django.contrib.auth import login as auth_login
                auth_login(request, user)
                messages.success(request, 'Logged in successfully as Admin.')
                return redirect('admin:index')  # Redirect to Django admin
            
            # Try Tenant first
            try:
                tenant = Tenant.objects.get(email=email)
                if not tenant.is_active:
                    messages.error(request, 'Tenant account is disabled.')
                    return render(request, 'authentication/login.html', {'form': form})
                if check_password(password, tenant.password):
                    login_user(request, tenant, 'tenant')
                    messages.success(request, 'Logged in successfully as Tenant.')
                    return redirect('tenant_dashboard')
                else:
                    messages.error(request, 'Invalid email or password.')
            except Tenant.DoesNotExist:
                # Try Owner
                try:
                    owner = Owner.objects.get(email=email)
                    if not owner.is_active:
                        messages.error(request, 'Owner account is disabled.')
                        return render(request, 'authentication/login.html', {'form': form})
                    if check_password(password, owner.password):
                        login_user(request, owner, 'owner')
                        messages.success(request, 'Logged in successfully as Owner.')
                        return redirect('owner_dashboard')
                    else:
                        messages.error(request, 'Invalid email or password.')
                except Owner.DoesNotExist:
                    messages.error(request, 'Invalid email or password.')
    else:
        form = LoginForm()
    return render(request, 'authentication/login.html', {'form': form})

def logout(request):
    logout_user(request)
    from django.contrib.auth import logout as auth_logout
    auth_logout(request)  # Also clear Django auth session for admins
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')

def owner_dashboard(request):
    if not request.session.get('user_id') or request.session.get('user_type') != 'owner':
        messages.error(request, 'Please log in as an owner to access the dashboard.')
        return redirect('login')
    
    owner = Owner.objects.get(id=request.session['user_id'])
    properties = Property.objects.filter(owner_id=request.session['user_id'])
    return render(request, 'owner_dashboard.html', {'owner': owner, 'properties': properties})

def tenant_dashboard(request):
    if not request.session.get('user_id') or request.session.get('user_type') != 'tenant':
        messages.error(request, 'Please log in as a tenant.')
        return redirect('login')
    
    tenant = Tenant.objects.get(id=request.session['user_id'])
    properties = Property.objects.filter(is_available=True)
    return render(request, 'tenant_dashboard.html', {'tenant':tenant, 'properties': properties})

