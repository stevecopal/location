from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Tenant

@receiver(post_save, sender=User)
def create_tenant_for_admin_user(sender, instance, created, **kwargs):
    if created and instance.email and not Tenant.objects.filter(email=instance.email).exists():
        Tenant.objects.create(
            name=instance.username,
            email=instance.email,
            phone='',
            password=instance.password,  # Mot de passe déjà haché par CustomUserAdminForm
            is_active=instance.is_active
        )