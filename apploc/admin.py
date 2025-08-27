from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django import forms
from django.contrib.auth.hashers import make_password, is_password_usable
from .models import ContactMessage, Owner, Tenant, Category, Property, Photo, Video, Review, Contact

# Formulaire Admin personnalisé pour User
class CustomUserAdminForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label='Mot de passe')

    class Meta:
        model = User
        fields = '__all__'

    def clean_password(self):
        password = self.cleaned_data['password']
        # Ne hacher que si le mot de passe n'est pas déjà haché
        if not is_password_usable(password):
            return make_password(password)
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        user.password = self.cleaned_data['password']
        if commit:
            user.save()
        return user

# Admin personnalisé pour User
class CustomUserAdmin(BaseUserAdmin):
    form = CustomUserAdminForm
    list_display = ('username', 'email', 'is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Informations personnelles', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates importantes', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password', 'is_staff', 'is_active'),
        }),
    )

# Inline pour Photo et Video
class PhotoInline(admin.TabularInline):
    model = Photo
    extra = 1

class VideoInline(admin.TabularInline):
    model = Video
    extra = 1

def create_linked_user(email, password):
    """
    Crée un compte User si nécessaire, en évitant le double hachage.
    """
    if not User.objects.filter(email=email).exists():
        # Si le mot de passe est déjà haché, passer le texte brut à create_user
        if is_password_usable(password):
            # On suppose que le mot de passe est déjà haché, donc on crée sans re-hacher
            user = User.objects.create_user(
                username=email,
                email=email,
                password=None  # On définira le mot de passe après
            )
            user.password = password
            user.save()
        else:
            # Mot de passe non haché, create_user le hachera
            User.objects.create_user(
                username=email,
                email=email,
                password=password
            )

@admin.register(Owner)
class OwnerAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'location', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'email', 'phone')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

    def save_model(self, request, obj, form, change):
        # Hacher le mot de passe si modifié
        if 'password' in form.changed_data:
            obj.password = make_password(form.cleaned_data['password'])
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
        # Hacher le mot de passe si modifié
        if 'password' in form.changed_data:
            obj.password = make_password(form.cleaned_data['password'])
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

# Enregistrer le modèle User avec l'Admin personnalisé
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)