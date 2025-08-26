# Create your models here.
from django.db import models
import uuid
from django.utils import timezone

class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

class Owner(BaseModel):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    location = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Tenant(BaseModel):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    password = models.CharField(max_length=128)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Category(BaseModel):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class Property(BaseModel):
    owner = models.ForeignKey(Owner, on_delete=models.CASCADE, related_name='properties')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='properties')
    location = models.CharField(max_length=200)
    price_per_month = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    contact_phone = models.CharField(max_length=15)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.category.name} - {self.location}"

class Photo(BaseModel):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='property_photos/')

    def __str__(self):
        return f"Photo for {self.property}"

class Video(BaseModel):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='videos')
    video_file = models.FileField(upload_to='property_videos/')

    def __str__(self):
        return f"Video for {self.property}"

class Review(BaseModel):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='reviews')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='reviews')
    message = models.TextField()
    date_posted = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Review by {self.tenant.name} for {self.property}"

class Contact(BaseModel):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15, blank=True)
    message = models.TextField()
    date_contact = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Contact from {self.name}"
    
class ContactMessage(BaseModel):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    subject = models.CharField(max_length=255)
    message = models.TextField()

    def __str__(self):
        return f"Message from {self.name} - {self.subject}"