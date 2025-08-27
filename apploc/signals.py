from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Tenant

@receiver(post_save, sender=User)
def create_tenant_for_admin_user(sender, instance, created, **kwargs):
    if created and instance.email:
        Tenant.objects.get_or_create(
            email=instance.email,
            defaults={
                'name': instance.username,
                'phone': '',
                'password': instance.password,
                'is_active': True
            }
        )