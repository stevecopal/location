from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django import forms
from django.contrib.auth.hashers import make_password
from .models import CustomUser, PendingUser, Category, Property, Photo, Video, Review, Contact, ContactMessage

# Formulaire Admin personnalisé pour CustomUser
class CustomUserAdminForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Mot de passe',
        widget=forms.PasswordInput,
        required=True,  # Requis pour la création
        help_text='Entrez le mot de passe pour le nouvel utilisateur.'
    )
    password2 = forms.CharField(
        label='Confirmation du mot de passe',
        widget=forms.PasswordInput,
        required=True,
        help_text='Confirmez le mot de passe.'
    )

    class Meta:
        model = CustomUser
        fields = ('email', 'phone', 'location', 'role', 'is_approved', 'is_active', 'is_staff')

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])  # Hacher le mot de passe
        if commit:
            user.save()
        return user

# Admin personnalisé pour CustomUser
class CustomUserAdmin(BaseUserAdmin):
    form = CustomUserAdminForm
    list_display = ('username', 'email', 'role', 'phone', 'location', 'is_approved', 'is_active', 'created_at')
    list_filter = ('role', 'is_approved', 'is_active', 'created_at')
    search_fields = ('username', 'email', 'phone')
    readonly_fields = ('username', 'created_at', 'updated_at', 'last_login', 'date_joined')

    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Informations personnelles', {'fields': ('phone', 'location', 'role')}),
        ('Permissions', {'fields': ('is_approved', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates importantes', {'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'phone', 'location', 'role', 'is_approved', 'is_active', 'is_staff'),
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
    list_display = ('username', 'email', 'phone', 'user_type', 'created_at', 'updated_at')
    list_filter = ('user_type', 'created_at')
    search_fields = ('username', 'email', 'phone')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

    def save_model(self, request, obj, form, change):
        if 'password' in form.changed_data:
            obj.password = make_password(form.cleaned_data['password'])
        super().save_model(request, obj, form, change)

# Admin pour les autres modèles
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

# Enregistrer CustomUser
admin.site.register(CustomUser, CustomUserAdmin)