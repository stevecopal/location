from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _
from ..models import CustomUser, PendingUser

class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True, label=_("Email"))
    user_type = forms.ChoiceField(choices=[('tenant', 'Locataire'), ('owner', 'Propriétaire')], label=_("Type d'utilisateur"))
    phone = forms.CharField(max_length=15, required=False, label=_("Téléphone"))
    location = forms.CharField(max_length=200, required=False, label=_("Localisation"))

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'user_type', 'phone', 'location', 'password1', 'password2']

    def clean(self):
        cleaned_data = super().clean()
        user_type = cleaned_data.get('user_type')
        phone = cleaned_data.get('phone')
        location = cleaned_data.get('location')

        if user_type == 'owner':
            if not phone:
                self.add_error('phone', _("Le téléphone est requis pour les propriétaires."))
            if not location:
                self.add_error('location', _("La localisation est requise pour les propriétaires."))
        return cleaned_data

    def clean_email(self):
        email = self.cleaned_data['email']
        if CustomUser.objects.filter(email=email).exists() or PendingUser.objects.filter(email=email).exists():
            raise forms.ValidationError(_("Cet email est déjà utilisé."))
        return email

    def clean_username(self):
        username = self.cleaned_data['username']
        if CustomUser.objects.filter(username=username).exists() or PendingUser.objects.filter(username=username).exists():
            raise forms.ValidationError(_("Ce nom d'utilisateur est déjà pris."))
        return username

    def clean_user_type(self):
        user_type = self.cleaned_data['user_type']
        if user_type not in ['tenant', 'owner']:
            raise forms.ValidationError(_("Type d'utilisateur invalide."))
        return user_type

class LoginForm(forms.Form):
    email = forms.EmailField(label=_('Email'), max_length=254)
    password = forms.CharField(widget=forms.PasswordInput, label=_('Password'))

class VerificationCodeForm(forms.Form):
    code = forms.CharField(max_length=4, min_length=4, widget=forms.TextInput(attrs={'placeholder': _('Enter 4-digit code')}), label=_('Code de vérification'))

    def clean_code(self):
        code = self.cleaned_data['code']
        if not code.isdigit() or len(code) != 4:
            raise forms.ValidationError(_("Le code doit être un nombre à 4 chiffres."))
        return code

class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(label=_('Email'))

    def clean_email(self):
        email = self.cleaned_data['email']
        if not CustomUser.objects.filter(email=email, is_active=True).exists():
            raise forms.ValidationError(_("Aucun utilisateur actif avec cet email."))
        return email

class PasswordResetForm(forms.Form):
    code = forms.CharField(max_length=4, min_length=4, widget=forms.TextInput(attrs={'placeholder': _('Enter 4-digit code')}), label=_('Code de vérification'))
    new_password = forms.CharField(widget=forms.PasswordInput, label=_('Nouveau mot de passe'), min_length=8)
    confirm_new_password = forms.CharField(widget=forms.PasswordInput, label=_('Confirmer le nouveau mot de passe'), min_length=8)

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_new_password = cleaned_data.get('confirm_new_password')
        if new_password and confirm_new_password and new_password != confirm_new_password:
            raise forms.ValidationError(_("Les nouveaux mots de passe ne correspondent pas."))
        return cleaned_data

    def clean_code(self):
        code = self.cleaned_data['code']
        if not code.isdigit() or len(code) != 4:
            raise forms.ValidationError(_("Le code doit être un nombre à 4 chiffres."))
        return code
    
class SignupForm(UserCreationForm):
    email = forms.EmailField(label=_("Email"))
    phone = forms.CharField(label=_("Téléphone"), required=False)
    location = forms.CharField(label=_("Location"), required=False)
    user_type = forms.ChoiceField(
        label=_("Type d'utilisateur"),
        choices=[('tenant', 'Locataire'), ('owner', 'Propriétaire')]
    )

    password1 = forms.CharField(
        label=_("Mot de passe"),
        widget=forms.PasswordInput,
        help_text=_("8 caractères minimum, ne peut pas être trop simple ou entièrement numérique")
    )
    password2 = forms.CharField(
        label=_("Confirmation du mot de passe"),
        widget=forms.PasswordInput
    )

    class Meta:
        model = CustomUser
        fields = ('email', 'user_type', 'phone', 'location', 'password1', 'password2')