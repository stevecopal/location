# Create your models here.
from datetime import timedelta
import random
import string
from django.db import models
import uuid
from django.utils import timezone
from django.utils.translation import gettext_lazy as _  # ← import pour i18n
from django.utils.text import slugify
import unicodedata

class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

class Owner(BaseModel):
    name = models.CharField(_("Name"), max_length=100)
    phone = models.CharField(_("Phone"), max_length=15)
    email = models.EmailField(_("Email"), unique=True)
    password = models.CharField(_("Password"), max_length=128)
    location = models.CharField(_("Location"), max_length=200)
    is_active = models.BooleanField(_("Is Active"), default=True)

    def __str__(self):
        return self.name  # on ne traduit pas le nom propre

class Tenant(BaseModel):
    name = models.CharField(_("Name"), max_length=100)
    email = models.EmailField(_("Email"), unique=True)
    phone = models.CharField(_("Phone"), max_length=15)
    password = models.CharField(_("Password"), max_length=128)
    is_active = models.BooleanField(_("Is Active"), default=True)

    def __str__(self):
        return self.name

class Category(BaseModel):
    name = models.CharField(_("Name"), max_length=50, unique=True)

    def __str__(self):
        return self.name

class Property(BaseModel):
    owner = models.ForeignKey(Owner, on_delete=models.CASCADE, related_name='properties', verbose_name=_("Owner"))
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='properties', verbose_name=_("Category"))
    location = models.CharField(_("Location"), max_length=200)
    price_per_month = models.DecimalField(_("Price per Month"), max_digits=10, decimal_places=2)
    description = models.TextField(_("Description"))
    contact_phone = models.CharField(_("Contact Phone"), max_length=15)
    is_available = models.BooleanField(_("Is Available"), default=True)

    def __str__(self):
        return _("{category} - {location}").format(category=self.category.name, location=self.location)

def photo_upload_path(instance, filename):
    # Génère un nom de fichier unique basé sur l'ID de la propriété et un UUID
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
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='reviews', verbose_name=_("Tenant"))
    message = models.TextField(_("Message"))
    date_posted = models.DateTimeField(_("Date Posted"), default=timezone.now)

    def __str__(self):
        return _("Review by {tenant} for {property}").format(tenant=self.tenant.name, property=self.property)

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



class PendingUser(BaseModel):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    password = models.CharField(max_length=128)
    verification_code = models.CharField(max_length=4)
    expires_at = models.DateTimeField()
    user_type = models.CharField(max_length=20, choices=[('tenant', 'Tenant'), ('owner', 'Owner'), ('user', 'User')], default='tenant')

    def __str__(self):
        return f"Pending {self.name} ({self.email})"