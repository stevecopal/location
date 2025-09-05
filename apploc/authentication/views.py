from datetime import timedelta
from django.db import IntegrityError
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
            email = form.cleaned_data['email'].lower().strip()
            phone = form.cleaned_data.get('phone', '')
            user_type = form.cleaned_data['user_type'].lower()
            password = form.cleaned_data['password1']

            # Vérifier si l'email existe déjà
            if CustomUser.objects.filter(email=email).exists():
                messages.error(request, _("Cet email est déjà utilisé. Veuillez vous connecter."))
                logger.warning(f"Tentative d'inscription avec email existant : {email}")
                return render(request, 'authentication/signup.html', {'form': form})

            # Vérifier si un PendingUser existe déjà
            pending_user = PendingUser.objects.filter(email=email).first()
            if pending_user:
                if pending_user.updated_at and timezone.now() < pending_user.updated_at + timedelta(minutes=3):
                    messages.error(request, _("Vous devez attendre 3 minutes avant de demander un nouveau code."))
                    logger.warning(f"Délai de 3 minutes non écoulé pour : {email}")
                    return render(request, 'authentication/signup.html', {'form': form})
                pending_user.verification_code = str(random.randint(1000, 9999))
                pending_user.expires_at = timezone.now() + timedelta(minutes=10)
                pending_user.save()
                messages.info(request, _("Un nouveau code de vérification a été envoyé à votre email."))
            else:
                # Générer un username unique
                base_username = email.split('@')[0].replace('.', '').replace('_', '')[:30]
                username = base_username
                counter = 1
                while CustomUser.objects.filter(username=username).exists() or PendingUser.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1

                # Vérifier user_type
                if user_type not in ['tenant', 'owner']:
                    messages.error(request, _("Type d'utilisateur invalide."))
                    logger.error(f"Type d'utilisateur invalide lors de l'inscription : {user_type}")
                    return render(request, 'authentication/signup.html', {'form': form})

                # Créer un nouveau pending user
                verification_code = str(random.randint(1000, 9999))
                expires_at = timezone.now() + timedelta(minutes=10)
                pending_user = PendingUser.objects.create(
                    username=username,
                    email=email,
                    phone=phone,
                    password=password,  # Stocké en clair temporairement
                    verification_code=verification_code,
                    expires_at=expires_at,
                    user_type=user_type,
                )
                messages.success(request, _("Un code de vérification a été envoyé à votre email."))

            # Envoyer l'email de vérification
            try:
                send_verification_email.delay(email, verification_code)  # Utilisation de Celery
                logger.info(f"Code OTP envoyé pour : {email}")
            except Exception as e:
                pending_user.delete()
                messages.error(request, _("Erreur lors de l'envoi de l'email. Veuillez réessayer."))
                logger.error(f"Erreur envoi email pour {email} : {str(e)}")
                return render(request, 'authentication/signup.html', {'form': form})

            return redirect('verify_email', email=email)
    else:
        form = SignupForm()
    return render(request, 'authentication/signup.html', {'form': form})

def verify_email(request, email):
    email = email.lower().strip()  # Normaliser l'email
    try:
        pending_user = get_object_or_404(PendingUser, email=email)
    except PendingUser.DoesNotExist:
        messages.error(request, _("Aucun utilisateur en attente trouvé avec cet email."))
        logger.warning(f"Tentative de vérification pour un email non existant : {email}")
        return redirect('signup')

    # Vérifier l'expiration du code
    if pending_user.expires_at < timezone.now():
        pending_user.delete()
        messages.error(request, _("Le code de vérification a expiré. Veuillez vous réinscrire."))
        logger.warning(f"Code de vérification expiré pour : {email}")
        return redirect('signup')

    if request.method == 'POST':
        form = VerificationCodeForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            if code == pending_user.verification_code:
                try:
                    # Vérifier l'unicité de l'email et du username
                    if CustomUser.objects.filter(email=pending_user.email).exists():
                        pending_user.delete()
                        messages.error(request, _("Un compte avec cet email existe déjà. Veuillez vous connecter."))
                        logger.error(f"Tentative de création d'un utilisateur existant : {email}")
                        return redirect('login')
                    if CustomUser.objects.filter(username=pending_user.username).exists():
                        pending_user.delete()
                        messages.error(request, _("Ce nom d'utilisateur est déjà pris. Veuillez vous réinscrire."))
                        logger.error(f"Tentative de création avec un nom d'utilisateur existant : {pending_user.username}")
                        return redirect('signup')

                    # Normaliser user_type pour correspondre à role
                    user_type = pending_user.user_type.lower()
                    if user_type not in ['tenant', 'owner']:
                        pending_user.delete()
                        messages.error(request, _("Type d'utilisateur invalide. Veuillez vous réinscrire."))
                        logger.error(f"Type d'utilisateur invalide pour {email}: {pending_user.user_type}")
                        return redirect('signup')

                    # Créer l'utilisateur final
                    user = CustomUser.objects.create_user(
                        username=pending_user.username,
                        email=pending_user.email.lower().strip(),
                        password=pending_user.password,  # Le mot de passe sera hashé
                        phone=pending_user.phone or '',
                        role=user_type,
                        is_approved=(user_type == 'tenant'),
                        is_active=(user_type == 'tenant')
                    )

                    # Supprimer l'utilisateur en attente
                    pending_user.delete()

                    # Connexion automatique pour les locataires
                    if user.role == 'tenant':
                        auth_login(request, user)
                        messages.success(request, _("Email vérifié avec succès. Vous êtes maintenant connecté."))
                        logger.info(f"Email vérifié et locataire connecté : {email}")
                        return redirect('home')
                    else:
                        messages.success(request, _("Email vérifié avec succès. Votre compte est en attente d'approbation par l'administrateur."))
                        logger.info(f"Email vérifié et compte propriétaire créé (en attente d'approbation) : {email}")
                        return redirect('login')

                except IntegrityError as e:
                    messages.error(request, _("Erreur : Cet email ou nom d'utilisateur est déjà utilisé."))
                    logger.error(f"IntegrityError lors de la création de l'utilisateur pour {email} : {str(e)}")
                    pending_user.delete()
                    return redirect('signup')
                except ValueError as e:
                    messages.error(request, _("Erreur : Données invalides pour la création de l'utilisateur."))
                    logger.error(f"ValueError lors de la création de l'utilisateur pour {email} : {str(e)}")
                    pending_user.delete()
                    return redirect('signup')
                except Exception as e:
                    messages.error(request, _("Erreur inattendue lors de la création de l'utilisateur. Veuillez réessayer."))
                    logger.error(f"Erreur inattendue lors de la création de l'utilisateur pour {email} : {str(e)}")
                    return redirect('signup')
            else:
                messages.error(request, _("Code de vérification invalide."))
                logger.warning(f"Tentative de code invalide pour : {email}, code saisi : {code}")
        else:
            messages.error(request, _("Formulaire invalide. Veuillez vérifier les informations saisies."))
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