from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django import forms
from django.contrib.auth.hashers import make_password
from .models import CustomUser, PendingUser, Category, Property, Photo, Video, Review, Contact, ContactMessage

# Formulaire Admin personnalisé pour CustomUser
class CustomUserAdminForm(forms.ModelForm):
    password = forms.CharField(
        label='Mot de passe',
        widget=forms.PasswordInput,
        required=False,  # facultatif lors de l'édition
        help_text='Laissez vide pour conserver le mot de passe existant.'
    )

    class Meta:
        model = CustomUser
        fields = '__all__'

    def clean_password(self):
        password = self.cleaned_data.get('password1')
        if password:
            return make_password(password)
        return self.instance.password  

# Admin personnalisé pour CustomUser
class CustomUserAdmin(BaseUserAdmin):
    form = CustomUserAdminForm
    list_display = ('username', 'email', 'role', 'phone', 'location', 'is_approved', 'is_active', 'created_at')
    list_filter = ('role', 'is_approved', 'is_active', 'created_at')
    search_fields = ('username', 'email', 'phone')

    # Exclure les champs non éditables
    readonly_fields = ('created_at', 'updated_at', 'last_login', 'date_joined')

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Informations personnelles', {'fields': ('first_name', 'last_name', 'email', 'phone', 'location', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_approved', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates importantes', {'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')}),  # readonly_fields prend le relais
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'phone', 'location', 'role', 'password', 'is_approved', 'is_active', 'is_staff'),
        }),
    )

    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

# Inline pour Photo et Video
class PhotoInline(admin.TabularInline):
    model = Photo
    extra = 1

class VideoInline(admin.TabularInline):
    model = Video
    extra = 1

# Admin pour PendingUser
@admin.register(PendingUser)
class PendingUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'phone', 'user_type', 'created_at')
    list_filter = ('user_type', 'created_at')
    search_fields = ('username', 'email', 'phone')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

    def save_model(self, request, obj, form, change):
        # Hacher le mot de passe si modifié
        if 'password' in form.changed_data:
            obj.password = make_password(form.cleaned_data['password'])
        super().save_model(request, obj, form, change)

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
    search_fields = ('message', 'tenant__username')
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

# Enregistrer le modèle CustomUser avec l'Admin personnalisé
# admin.site.unregister(User)
admin.site.register(CustomUser, CustomUserAdmin)