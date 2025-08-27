from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils.translation import gettext_lazy as _

@shared_task
def send_verification_email(email, code):
    subject = 'Verify Your Email Address'
    message = f'Your verification code is: {code}\nThis code expires in 10 minutes.'
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )

@shared_task
def send_reset_password_email(email, code):
    subject = 'Password Reset Code'
    message = f'Your password reset code is: {code}\nThis code expires in 10 minutes.'
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )
    
@shared_task
def send_contact_email(name, email, subject, message):
    email_subject = str(_('New Contact Message: {subject}').format(subject=subject))
    email_message = str(_('You have received a new contact message:\n\nName: {name}\nEmail: {email}\nMessage: {message}').format(
        name=name, email=email, message=message
    ))
    send_mail(
        email_subject,
        email_message,
        settings.DEFAULT_FROM_EMAIL,
        [settings.CONTACT_EMAIL],  # Configurez CONTACT_EMAIL dans settings.py
        fail_silently=False,
    )