from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import PendingUser
from .tasks import send_verification_email, send_reset_password_email
from django.utils.translation import gettext_lazy as _

@receiver(post_save, sender=PendingUser)
def handle_pending_user_verification(sender, instance, created, **kwargs):
    if created:
        if instance.user_type == 'reset_password':
            send_reset_password_email.delay(
                instance.email,
                str(_('Votre code de réinitialisation est : {code}\nCe code expire dans 10 minutes.').format(code=instance.verification_code))
            )
        else:
            send_verification_email.delay(
                instance.email,
                str(_('Votre code de vérification est : {code}\nCe code expire dans 10 minutes.').format(code=instance.verification_code))
            )