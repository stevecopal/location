from django import forms
from ..models import Tenant
from django.utils.translation import gettext_lazy as _  # ← import pour i18n


class TenantSignupForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, min_length=8)
    confirm_password = forms.CharField(widget=forms.PasswordInput, min_length=8)

    class Meta:
        model = Tenant
        fields = ['name', 'email', 'phone', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data

class LoginForm(forms.Form):
    email = forms.EmailField(label=_('Email'), max_length=254)
    password = forms.CharField(widget=forms.PasswordInput, label=_('Password'))

class VerificationCodeForm(forms.Form):
    code = forms.CharField(max_length=4, min_length=4, widget=forms.TextInput(attrs={'placeholder': 'Enter 4-digit code'}))

class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField()

class PasswordResetForm(forms.Form):
    code = forms.CharField(max_length=4, min_length=4, widget=forms.TextInput(attrs={'placeholder': 'Enter 4-digit code'}))
    new_password = forms.CharField(widget=forms.PasswordInput)
    confirm_new_password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_new_password = cleaned_data.get('confirm_new_password')
        if new_password != confirm_new_password:
            raise forms.ValidationError("New passwords do not match.")
        return cleaned_data