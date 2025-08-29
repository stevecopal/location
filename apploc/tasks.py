from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils.translation import gettext_lazy as _

@shared_task
def send_verification_email(email, message):
    subject = str(_('Vérification de votre compte'))
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )

@shared_task
def send_reset_password_email(email, code):
    subject = str(_('Code de réinitialisation du mot de passe'))
    message = str(_('Votre code de réinitialisation est : {code}\nCe code expire dans 10 minutes.').format(code=code))
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )

@shared_task
def send_contact_email(name, email, subject, message):
    email_subject = str(_('Nouveau message de contact : {subject}').format(subject=subject))
    email_message = str(_('Nouveau message de contact :\n\nNom : {name}\nEmail : {email}\nMessage : {message}').format(
        name=name, email=email, message=message
    ))
    send_mail(
        email_subject,
        email_message,
        settings.DEFAULT_FROM_EMAIL,
        [settings.CONTACT_EMAIL],
        fail_silently=False,
    )