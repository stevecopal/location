from datetime import timedelta
import random
import string
from django.db import models
import uuid
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.contrib.auth.models import AbstractUser
import unicodedata

class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def soft_delete(self):
        self.deleted_at = timezone.now()
        self.save()

from django.contrib.auth.models import AbstractUser, BaseUserManager

class CustomUserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, username, email, password=None, role='tenant', **extra_fields):
        """
        Crée un utilisateur normal.
        """
        if not email:
            raise ValueError("L'utilisateur doit avoir un email")
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        """
        Crée un superuser avec le rôle admin et toutes les permissions.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_approved', True)  # superuser est approuvé
        return self.create_user(username, email, password, role='admin', **extra_fields)


class CustomUser(AbstractUser, BaseModel):
    ROLE_CHOICES = (
        ('admin', 'Administrateur'),
        ('owner', 'Propriétaire'),
        ('tenant', 'Locataire'),
    )
    email = models.EmailField(_("Email"), unique=True)
    phone = models.CharField(_("Phone"), max_length=15, blank=True)
    location = models.CharField(_("Location"), max_length=200, blank=True)
    role = models.CharField(_("Role"), max_length=20, choices=ROLE_CHOICES, default='tenant')
    is_approved = models.BooleanField(_("Is Approved"), default=False)
    objects = CustomUserManager() 

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")

class PendingUser(BaseModel):
    username = models.CharField(_("Username"), max_length=150, unique=True)
    email = models.EmailField(_("Email"), unique=True)
    phone = models.CharField(_("Phone"), max_length=20)
    password = models.CharField(_("Password"), max_length=128)
    verification_code = models.CharField(_("Verification Code"), max_length=4)
    expires_at = models.DateTimeField(_("Expires At"))
    user_type = models.CharField(_("User Type"), max_length=20, choices=[('tenant', 'Tenant'), ('owner', 'Owner')], default='tenant')
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Pending {self.username} ({self.email})"

    class Meta:
        verbose_name = _("Pending User")
        verbose_name_plural = _("Pending Users")

class Category(BaseModel):
    name = models.CharField(_("Name"), max_length=50, unique=True)

    def __str__(self):
        return self.name

class Property(BaseModel):
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='properties', limit_choices_to={'role': 'owner'}, verbose_name=_("Owner"))
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='properties', verbose_name=_("Category"))
    location = models.CharField(_("Location"), max_length=200)
    price_per_month = models.DecimalField(_("Price per Month"), max_digits=10, decimal_places=2)
    description = models.TextField(_("Description"))
    contact_phone = models.CharField(_("Contact Phone"), max_length=15)
    is_available = models.BooleanField(_("Is Available"), default=True)

    def __str__(self):
        return _("{category} - {location}").format(category=self.category.name if self.category else "No Category", location=self.location)

def photo_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    return f'property_photos/{instance.property.id}_{uuid.uuid4()}.{ext}'

class Photo(BaseModel):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='photos', verbose_name=_("Property"))
    image = models.ImageField(upload_to=photo_upload_path, verbose_name=_('Image'))

    def __str__(self):
        return _("Photo for {property}").format(property=self.property)

class Video(BaseModel):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='videos', verbose_name=_("Property"))
    video_file = models.FileField(_("Video File"), upload_to='property_videos/')

    def __str__(self):
        return _("Video for {property}").format(property=self.property)

class Review(BaseModel):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='reviews', verbose_name=_("Property"))
    tenant = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='reviews', limit_choices_to={'role': 'tenant'}, verbose_name=_("Tenant"))
    message = models.TextField(_("Message"))
    date_posted = models.DateTimeField(_("Date Posted"), default=timezone.now)

    def __str__(self):
        return _("Review by {tenant} for {property}").format(tenant=self.tenant.username, property=self.property)

class Contact(BaseModel):
    name = models.CharField(_("Name"), max_length=100)
    email = models.EmailField(_("Email"))
    phone = models.CharField(_("Phone"), max_length=15, blank=True)
    message = models.TextField(_("Message"))
    date_contact = models.DateTimeField(_("Date Contact"), default=timezone.now)

    def __str__(self):
        return _("Contact from {name}").format(name=self.name)

class ContactMessage(BaseModel):
    name = models.CharField(_("Name"), max_length=255)
    email = models.EmailField(_("Email"))
    subject = models.CharField(_("Subject"), max_length=255)
    message = models.TextField(_("Message"))

    def __str__(self):
        return _("Message from {name} - {subject}").format(name=self.name, subject=self.subject)