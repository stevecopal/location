from datetime import timedelta
from django.utils import timezone
import logging
import random
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User  # Import default User model
from django.utils.translation import gettext_lazy as _
from apploc.tasks import send_reset_password_email, send_verification_email
from .forms import PasswordResetForm, PasswordResetRequestForm, TenantSignupForm, LoginForm, VerificationCodeForm
from ..models import Owner, Tenant, PendingUser, Property
from .utils import login_user, logout_user

logger = logging.getLogger(__name__)

def tenant_signup(request):
    if request.method == 'POST':
        form = TenantSignupForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            if Tenant.objects.filter(email=email).exists() or Owner.objects.filter(email=email).exists() or PendingUser.objects.filter(email=email).exists():
                messages.error(request, _('Email already exists or is pending verification.'))
                logger.warning(f"Signup attempt with existing email: {email}")
                return render(request, 'authentication/signup.html', {'form': form})

            # Generate 4-digit verification code
            verification_code = str(random.randint(1000, 9999))
            expires_at = timezone.now() + timedelta(minutes=10)

            # Store pending user data
            pending_user = PendingUser(
                name=form.cleaned_data['name'],
                email=email,
                phone=form.cleaned_data['phone'],
                password=make_password(form.cleaned_data['password']),
                verification_code=verification_code,
                expires_at=expires_at,
                user_type='tenant'  # Indicate this is for a Tenant
            )
            pending_user.save()
            logger.info(f"Pending user created: {email}, code: {verification_code}")

            # Send verification email in the background
            try:
                send_verification_email.delay(email, verification_code)
                messages.success(request, _('A verification code has been sent to your email. Please check your inbox (and spam folder).'))
                logger.info(f"Verification email queued for: {email}")
                return redirect('verify_email', email=email)
            except Exception as e:
                pending_user.delete()
                messages.error(request, _('Failed to send verification email. Please try again.'))
                logger.error(f"Failed to send verification email to {email}: {str(e)}")
                return render(request, 'authentication/signup.html', {'form': form})
    else:
        form = TenantSignupForm()
    return render(request, 'authentication/signup.html', {'form': form})

def verify_email(request, email):
    try:
        pending_user = PendingUser.objects.get(email=email)
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
                    # Create Tenant
                    tenant = Tenant(
                        name=pending_user.name,
                        email=pending_user.email,
                        phone=pending_user.phone,
                        password=pending_user.password
                    )
                    tenant.save()
                    # Optionally create a User for admin compatibility
                    try:
                        user = User.objects.create_user(
                            username=pending_user.email,
                            email=pending_user.email,
                            password=form.cleaned_data['password']
                        )
                        user.save()
                    except Exception as e:
                        logger.warning(f"Failed to create User for {email}: {str(e)}")
                    pending_user.delete()
                    messages.success(request, _('Email verified successfully. Please log in.'))
                    logger.info(f"Email verified and tenant created: {email}")
                    return redirect('login')
                else:
                    messages.error(request, _('Invalid verification code.'))
                    logger.warning(f"Invalid verification code attempt for: {email}, entered: {code}")
        else:
            form = VerificationCodeForm()
        return render(request, 'authentication/verify_email.html', {'form': form, 'email': email})
    except PendingUser.DoesNotExist:
        messages.error(request, _('Invalid verification request.'))
        logger.error(f"Invalid verification request for email: {email}")
        return redirect('signup')

def login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            # Chercher un utilisateur Django avec cet email
            try:
                user_obj = User.objects.get(email=email)
                user = authenticate(request, username=user_obj.username, password=password)
                if user is not None and user.is_staff:
                    auth_login(request, user)
                    messages.success(request, _('Logged in successfully as Admin.'))
                    return redirect('admin:index')
            except User.DoesNotExist:
                pass  # Pas un admin, continuer avec Tenant/Owner

            # Login pour Tenant
            try:
                tenant = Tenant.objects.get(email=email)
                if not tenant.is_active:
                    messages.error(request, _('Tenant account is disabled.'))
                    return render(request, 'authentication/login.html', {'form': form})
                if check_password(password, tenant.password):
                    login_user(request, tenant, 'tenant')
                    messages.success(request, _('Logged in successfully as Tenant.'))
                    return redirect('tenant_dashboard')
                else:
                    messages.error(request, _('Invalid email or password.'))
            except Tenant.DoesNotExist:
                # Login pour Owner
                try:
                    owner = Owner.objects.get(email=email)
                    if not owner.is_active:
                        messages.error(request, _('Owner account is disabled.'))
                        return render(request, 'authentication/login.html', {'form': form})
                    if check_password(password, owner.password):
                        login_user(request, owner, 'owner')
                        messages.success(request, _('Logged in successfully as Owner.'))
                        return redirect('owner_dashboard')
                    else:
                        messages.error(request, _('Invalid email or password.'))
                except Owner.DoesNotExist:
                    messages.error(request, _('Invalid email or password.'))
    else:
        form = LoginForm()
    return render(request, 'authentication/login.html', {'form': form})

def logout(request):
    logout_user(request)
    auth_logout(request)
    messages.success(request, _('You have been logged out successfully.'))
    logger.info("User logged out")
    return redirect('login')

def owner_dashboard(request):
    if not request.session.get('user_id') or request.session.get('user_type') != 'owner':
        messages.error(request, _('Please log in as an owner to access the dashboard.'))
        logger.warning("Unauthorized owner dashboard access attempt")
        return redirect('login')
    owner = Owner.objects.get(id=request.session['user_id'])
    properties = Property.objects.filter(owner_id=request.session['user_id'])
    return render(request, 'owner_dashboard.html', {'owner': owner, 'properties': properties})

def tenant_dashboard(request):
    if not request.session.get('user_id') or request.session.get('user_type') != 'tenant':
        messages.error(request, _('Please log in as a tenant.'))
        logger.warning("Unauthorized tenant dashboard access attempt")
        return redirect('login')
    tenant = Tenant.objects.get(id=request.session['user_id'])
    properties = Property.objects.filter(is_available=True)
    return render(request, 'tenant_dashboard.html', {'tenant': tenant, 'properties': properties})

def dashboard_redirect(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            logger.info("Admin redirected to admin panel")
            return redirect('admin:index')
        # Check if the user is linked to Tenant or Owner
        try:
            tenant = Tenant.objects.get(email=request.user.email)
            login_user(request, tenant, 'tenant')
            logger.info("User redirected to tenant dashboard")
            return redirect('tenant_dashboard')
        except Tenant.DoesNotExist:
            try:
                owner = Owner.objects.get(email=request.user.email)
                login_user(request, owner, 'owner')
                logger.info("User redirected to owner dashboard")
                return redirect('owner_dashboard')
            except Owner.DoesNotExist:
                messages.error(request, _('No Tenant or Owner account linked to this user.'))
                logger.warning(f"No Tenant/Owner account linked for user: {request.user.email}")
                return redirect('login')
    elif request.session.get('user_id'):
        user_type = request.session.get('user_type')
        if user_type == 'owner':
            logger.info("Owner redirected to owner dashboard")
            return redirect('owner_dashboard')
        elif user_type == 'tenant':
            logger.info("Tenant redirected to tenant dashboard")
            return redirect('tenant_dashboard')
    messages.error(request, _('Please log in to access your dashboard.'))
    logger.warning("Unauthorized dashboard access attempt")
    return redirect('login')

def password_reset_request(request):
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']

            # Chercher si un PendingUser existe déjà
            pending_user = PendingUser.objects.filter(email=email).first()
            verification_code = str(random.randint(1000, 9999))
            expires_at = timezone.now() + timedelta(minutes=10)

            # Fonction utilitaire pour envoyer le mail
            def send_reset(pu, name_type):
                try:
                    send_reset_password_email.delay(email, verification_code)
                    messages.success(request, _('A password reset code has been sent to your email.'))
                    logger.info(f"Password reset email queued for {name_type}: {email}")
                    return redirect('password_reset_verify', email=email)
                except Exception as e:
                    messages.error(request, _('Failed to send reset email. Please try again.'))
                    logger.error(f"Failed to send reset email to {email}: {str(e)}")
                    return None

            # Si un PendingUser existe déjà, on le met à jour
            if pending_user:
                pending_user.verification_code = verification_code
                pending_user.expires_at = expires_at
                pending_user.save()
                return send_reset(pending_user, "PendingUser")

            # Sinon, chercher dans User, Tenant, Owner
            try:
                user = User.objects.get(email=email)
                pending_user = PendingUser.objects.create(
                    email=email,
                    verification_code=verification_code,
                    expires_at=expires_at,
                    name=user.username,
                    phone='',
                    password=user.password,
                    user_type='user'
                )
                return send_reset(pending_user, "User")

            except User.DoesNotExist:
                try:
                    tenant = Tenant.objects.get(email=email)
                    pending_user = PendingUser.objects.create(
                        email=email,
                        verification_code=verification_code,
                        expires_at=expires_at,
                        name=tenant.name,
                        phone=tenant.phone,
                        password=tenant.password,
                        user_type='tenant'
                    )
                    return send_reset(pending_user, "Tenant")

                except Tenant.DoesNotExist:
                    try:
                        owner = Owner.objects.get(email=email)
                        pending_user = PendingUser.objects.create(
                            email=email,
                            verification_code=verification_code,
                            expires_at=expires_at,
                            name=owner.name,
                            phone=owner.phone,
                            password=owner.password,
                            user_type='owner'
                        )
                        return send_reset(pending_user, "Owner")

                    except Owner.DoesNotExist:
                        messages.error(request, _('No account found with this email.'))
                        logger.warning(f"Password reset attempt with non-existent email: {email}")
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
                    # Update password based on user_type
                    if pending_user.user_type == 'user':
                        try:
                            user = User.objects.get(email=email)
                            user.set_password(form.cleaned_data['new_password'])
                            user.save()
                            pending_user.delete()
                            messages.success(request, _('Password reset successfully. Please log in.'))
                            logger.info(f"Password reset successful for User: {email}")
                            return redirect('login')
                        except User.DoesNotExist:
                            messages.error(request, _('No account found with this email.'))
                            logger.warning(f"No User account found for reset: {email}")
                    elif pending_user.user_type == 'tenant':
                        try:
                            tenant = Tenant.objects.get(email=email)
                            tenant.password = make_password(form.cleaned_data['new_password'])
                            tenant.save()
                            pending_user.delete()
                            messages.success(request, _('Password reset successfully. Please log in.'))
                            logger.info(f"Password reset successful for Tenant: {email}")
                            return redirect('login')
                        except Tenant.DoesNotExist:
                            messages.error(request, _('No account found with this email.'))
                            logger.warning(f"No Tenant account found for reset: {email}")
                    elif pending_user.user_type == 'owner':
                        try:
                            owner = Owner.objects.get(email=email)
                            owner.password = make_password(form.cleaned_data['new_password'])
                            owner.save()
                            pending_user.delete()
                            messages.success(request, _('Password reset successfully. Please log in.'))
                            logger.info(f"Password reset successful for Owner: {email}")
                            return redirect('login')
                        except Owner.DoesNotExist:
                            messages.error(request, _('No account found with this email.'))
                            logger.warning(f"No Owner account found for reset: {email}")
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