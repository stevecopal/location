
# Register your models here.
from django.contrib import admin
from .models import ContactMessage, Owner, Tenant, Category, Property, Photo, Video, Review, Contact
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from .models import Owner, Tenant


class PhotoInline(admin.TabularInline):
    model = Photo
    extra = 1

class VideoInline(admin.TabularInline):
    model = Video
    extra = 1

@admin.register(Owner)
class OwnerAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'location', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'email', 'phone')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    
    def save_model(self, request, obj, form, change):
        # Hash the password if it has been modified
        if 'password' in form.changed_data:
            obj.password = make_password(form.cleaned_data['password'])
        super().save_model(request, obj, form, change)
        
        def save_model(self, request, obj, form, change):
            super().save_model(request, obj, form, change)
            create_linked_user(obj.email, obj.password)


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'email', 'phone')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        create_linked_user(obj.email, obj.password)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)
    ordering = ('name',)

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('category', 'owner', 'location', 'price_per_month', 'is_available', 'created_at')
    list_filter = ('category', 'is_available', 'created_at')
    search_fields = ('location', 'description')
    list_select_related = ('category', 'owner')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    inlines = [PhotoInline, VideoInline]

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('property', 'tenant', 'date_posted')
    list_filter = ('date_posted',)
    search_fields = ('message', 'tenant__name')
    list_select_related = ('property', 'tenant')
    date_hierarchy = 'date_posted'
    ordering = ('-date_posted',)

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'date_contact')
    list_filter = ('date_contact',)
    search_fields = ('name', 'email', 'message')
    date_hierarchy = 'date_contact'
    ordering = ('-date_contact',)
    
@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    list_filter = ('created_at',)

def create_linked_user(email, password):
    """
    Crée un compte User de base pour le reset et l'auth standard.
    Si le User existe déjà, on ne fait rien.
    """
    if not User.objects.filter(email=email).exists():
        User.objects.create_user(
            username=email,
            email=email,
            password=password  # sera automatiquement haché
        )


