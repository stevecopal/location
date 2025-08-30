from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

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
import logging

logger = logging.getLogger(__name__)

@shared_task
def send_contact_email(name, email, subject, message):
    try:
        context = {
            'name': name,
            'email': email,
            'subject': subject,
            'message': message,
        }
        
        html_content = render_to_string('emails/contact_email.html', context)
        logger.info(f"HTML content rendered: {html_content[:100]}...")  # Log premier 100 caractères
        
        email_message = EmailMultiAlternatives(
            subject=subject,
            body=f"Message de {name} ({email}):\n\n{message}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.CONTACT_EMAIL],
        )
        
        email_message.attach_alternative(html_content, "text/html")
        email_message.send()
        logger.info(f"Email sent to {settings.CONTACT_EMAIL} from {email}")
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        raise