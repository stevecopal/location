from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def send_verification_email(email, message):
    """
    Envoie un email de vérification avec le message complet déjà généré.
    """
    subject = 'Vérification de votre compte'
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )

@shared_task
def send_reset_password_email(email, message):
    """
    Envoie un email de réinitialisation avec le message complet déjà généré.
    """
    subject = 'Code de réinitialisation du mot de passe'
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )

@shared_task
def send_contact_email(name, email, subject, message):
    email_subject = f'Nouveau message de contact : {subject}'
    email_message = f'Nouveau message de contact :\n\nNom : {name}\nEmail : {email}\nMessage : {message}'
    send_mail(
        email_subject,
        email_message,
        settings.DEFAULT_FROM_EMAIL,
        [settings.CONTACT_EMAIL],
        fail_silently=False,
    )
