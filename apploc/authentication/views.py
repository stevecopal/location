from datetime import timedelta
from django.utils import timezone
import logging
import random
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.utils.translation import gettext_lazy as _
from apploc.tasks import send_reset_password_email, send_verification_email
from .forms import PasswordResetForm, PasswordResetRequestForm, SignupForm, LoginForm, VerificationCodeForm
from ..models import CustomUser, PendingUser, Property
from django.contrib.auth import login as auth_login


logger = logging.getLogger(__name__)

def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']

            # Vérifier si un PendingUser existe déjà
            pending_user = PendingUser.objects.filter(email=email).first()
            if pending_user:
                # Vérifier le délai de 3 minutes
                if pending_user.updated_at and timezone.now() < pending_user.updated_at + timedelta(minutes=3):
                    messages.error(request, _('You must wait 3 minutes before requesting a new code.'))
                    return render(request, 'authentication/signup.html', {'form': form})
                # Mettre à jour le code et l'expiration
                pending_user.verification_code = str(random.randint(1000, 9999))
                pending_user.expires_at = timezone.now() + timedelta(minutes=10)
                pending_user.save()
                messages.info(request, _('A new verification code has been sent to your email.'))
            else:
                # Créer un nouveau pending user
                username = email.split('@')[0] + str(random.randint(100, 999))
                verification_code = str(random.randint(1000, 9999))
                expires_at = timezone.now() + timedelta(minutes=10)

                pending_user = PendingUser.objects.create(
                    username=username,
                    email=email,
                    phone=form.cleaned_data.get('phone', ''),
                    password=form.cleaned_data['password1'],
                    verification_code=verification_code,
                    expires_at=expires_at,
                    user_type=form.cleaned_data['user_type'],
                )
                messages.success(request, _('A verification code has been sent to your email.'))

            return redirect('verify_email', email=email)

    else:
        form = SignupForm()
    return render(request, 'authentication/signup.html', {'form': form})

def verify_email(request, email):
    pending_user = get_object_or_404(PendingUser, email=email)

    # Vérifier l'expiration du code
    if pending_user.expires_at < timezone.now():
        pending_user.delete()
        messages.error(request, _('Verification code has expired. Please sign up again.'))
        logger.warning(f"Expired verification code for: {email}")
        return redirect('signup')

    if request.method == 'POST':
        form = VerificationCodeForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            if code == pending_user.verification_code:
                # Créer l'utilisateur final
                user = CustomUser.objects.create_user(
                    username=pending_user.username,
                    email=pending_user.email,
                    password=pending_user.password,  # sera hashé correctement
                    phone=pending_user.phone,
                    role=pending_user.user_type,
                    is_approved=(pending_user.user_type == 'tenant'),
                    is_active=(pending_user.user_type == 'tenant')
                )

                # Supprimer le pending_user après création
                pending_user.delete()

                # Connexion auto si locataire
                if user.role == 'tenant':
                    auth_login(request, user)
                    messages.success(request, _('Email verified successfully. You are now logged in.'))
                    logger.info(f"Email verified and tenant created: {email}")
                    return redirect('home')
                else:
                    messages.success(request, _('Email verified successfully. Your account is pending admin approval.'))
                    logger.info(f"Email verified and owner created (pending approval): {email}")
                    return redirect('login')
            else:
                messages.error(request, _('Invalid verification code.'))
                logger.warning(f"Invalid verification code attempt for: {email}, entered: {code}")
    else:
        form = VerificationCodeForm()

    return render(request, 'authentication/verify_email.html', {'form': form, 'email': email})

def login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            # Authenticate using CustomUser
            try:
                user = CustomUser.objects.get(email=email)
                if not user.is_active:
                    messages.error(request, _('Account is disabled.'))
                    logger.warning(f"Login attempt with disabled account: {email}")
                    return render(request, 'authentication/login.html', {'form': form})
                authenticated_user = authenticate(request, username=user.username, password=password)
                if authenticated_user is not None:
                    auth_login(request, authenticated_user)
                    if authenticated_user.role == 'admin':
                        messages.success(request, _('Logged in successfully as Admin.'))
                        logger.info(f"Admin login: {email}")
                        return redirect('admin:index')
                    elif authenticated_user.role == 'owner':
                        if not authenticated_user.is_approved:
                            messages.error(request, _('Owner account is not yet approved.'))
                            logger.warning(f"Unapproved owner login attempt: {email}")
                            return render(request, 'authentication/login.html', {'form': form})
                        messages.success(request, _('Logged in successfully as Owner.'))
                        logger.info(f"Owner login: {email}")
                        return redirect('owner_dashboard')
                    else:
                        messages.success(request, _('Logged in successfully as Tenant.'))
                        logger.info(f"Tenant login: {email}")
                        return redirect('tenant_dashboard')
                else:
                    messages.error(request, _('Invalid email or password.'))
                    logger.warning(f"Invalid password for: {email}")
            except CustomUser.DoesNotExist:
                messages.error(request, _('Invalid email or password.'))
                logger.warning(f"Login attempt with non-existent email: {email}")
    else:
        form = LoginForm()
    return render(request, 'authentication/login.html', {'form': form})

def logout(request):
    auth_logout(request)
    messages.success(request, _('You have been logged out successfully.'))
    logger.info("User logged out")
    return redirect('login')

def owner_dashboard(request):
    if not request.user.is_authenticated or request.user.role != 'owner' or not request.user.is_approved:
        messages.error(request, _('Please log in as an approved owner to access the dashboard.'))
        logger.warning("Unauthorized owner dashboard access attempt")
        return redirect('login')
    properties = Property.objects.filter(owner=request.user, deleted_at__isnull=True)
    return render(request, 'owner_dashboard.html', {'user': request.user, 'properties': properties})

def tenant_dashboard(request):
    if not request.user.is_authenticated or request.user.role != 'tenant':
        messages.error(request, _('Please log in as a tenant.'))
        logger.warning("Unauthorized tenant dashboard access attempt")
        return redirect('login')
    properties = Property.objects.filter(is_available=True, deleted_at__isnull=True)
    return render(request, 'tenant_dashboard.html', {'user': request.user, 'properties': properties})

def dashboard_redirect(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            logger.info("Admin redirected to admin panel")
            return redirect('admin:index')
        elif request.user.role == 'owner':
            if not request.user.is_approved:
                messages.error(request, _('Owner account is not yet approved.'))
                logger.warning(f"Unapproved owner access attempt: {request.user.email}")
                return redirect('login')
            logger.info("Owner redirected to owner dashboard")
            return redirect('owner_dashboard')
        elif request.user.role == 'tenant':
            logger.info("Tenant redirected to tenant dashboard")
            return redirect('tenant_dashboard')
        else:
            messages.error(request, _('Invalid user role.'))
            logger.warning(f"Invalid role for user: {request.user.email}")
            return redirect('login')
    messages.error(request, _('Please log in to access your dashboard.'))
    logger.warning("Unauthorized dashboard access attempt")
    return redirect('login')

def password_reset_request(request):
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']

            try:
                user = CustomUser.objects.get(email=email)
                pending_user = PendingUser.objects.filter(email=email).first()

                if pending_user:
                    # Vérifier le délai de 3 minutes
                    if pending_user.updated_at and timezone.now() < pending_user.updated_at + timedelta(minutes=3):
                        messages.error(request, _('You must wait 3 minutes before requesting a new reset code.'))
                        return render(request, 'authentication/password_reset_request.html', {'form': form})

                    # Mettre à jour le code et l'expiration
                    pending_user.verification_code = str(random.randint(1000, 9999))
                    pending_user.expires_at = timezone.now() + timedelta(minutes=10)
                    pending_user.user_type = 'reset_password'
                    pending_user.save()
                    messages.info(request, _('A new reset code has been sent to your email.'))
                else:
                    # Créer un nouveau pending user
                    verification_code = str(random.randint(1000, 9999))
                    expires_at = timezone.now() + timedelta(minutes=10)

                    pending_user = PendingUser.objects.create(
                        username=user.username,
                        email=email,
                        phone=user.phone,
                        password=user.password,
                        verification_code=verification_code,
                        expires_at=expires_at,
                        user_type='reset_password'
                    )
                    messages.success(request, _('A password reset code has been sent to your email.'))

                return redirect('password_reset_verify', email=email)

            except CustomUser.DoesNotExist:
                messages.error(request, _('No account found with this email.'))

    else:
        form = PasswordResetRequestForm()
    return render(request, 'authentication/password_reset_request.html', {'form': form})

def password_reset_verify(request, email):
    try:
        pending_user = PendingUser.objects.get(email=email)
        if pending_user.expires_at < timezone.now():
            pending_user.delete()
            messages.error(request, _('Reset code has expired. Please request a new one.'))
            logger.warning(f"Expired reset code for: {email}")
            return redirect('password_reset_request')

        if request.method == 'POST':
            form = PasswordResetForm(request.POST)
            if form.is_valid():
                code = form.cleaned_data['code']
                if code == pending_user.verification_code:
                    try:
                        user = CustomUser.objects.get(email=email)
                        user.set_password(form.cleaned_data['new_password'])
                        user.save()
                        pending_user.delete()
                        messages.success(request, _('Password reset successfully. Please log in.'))
                        logger.info(f"Password reset successful for: {email}")
                        return redirect('login')
                    except CustomUser.DoesNotExist:
                        messages.error(request, _('No account found with this email.'))
                        logger.warning(f"No account found for reset: {email}")
                else:
                    messages.error(request, _('Invalid verification code.'))
                    logger.warning(f"Invalid reset code attempt for: {email}, entered: {code}")
        else:
            form = PasswordResetForm()
        return render(request, 'authentication/password_reset_verify.html', {'form': form, 'email': email})
    except PendingUser.DoesNotExist:
        messages.error(request, _('Invalid reset request.'))
        logger.error(f"Invalid reset request for email: {email}")
        return redirect('password_reset_request')