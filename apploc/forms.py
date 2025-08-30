from django import forms
from django.forms import modelformset_factory
from django.utils.translation import gettext_lazy as _
from .models import ContactMessage, Property, Photo, Video, Review, Category

class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']
        labels = {
            'name': _('Nom'),
            'email': _('Email'),
            'subject': _('Sujet'),
            'message': _('Message'),
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full p-3 border border-gray-300 rounded-lg', 'placeholder': _('Votre nom')}),
            'email': forms.EmailInput(attrs={'class': 'w-full p-3 border border-gray-300 rounded-lg', 'placeholder': _('Votre email')}),
            'subject': forms.TextInput(attrs={'class': 'w-full p-3 border border-gray-300 rounded-lg', 'placeholder': _('Sujet')}),
            'message': forms.Textarea(attrs={'class': 'w-full p-3 border border-gray-300 rounded-lg', 'rows': 5, 'placeholder': _('Votre message')}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise forms.ValidationError(_("L'email est requis."))
        return email

    def clean_message(self):
        message = self.cleaned_data.get('message')
        if len(message) < 10:
            raise forms.ValidationError(_("Le message doit contenir au moins 10 caractères."))
        return message