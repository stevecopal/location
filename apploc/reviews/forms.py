from django import forms
from django.forms import modelformset_factory
from django.utils.translation import gettext_lazy as _
from ..models import ContactMessage, Property, Photo, Video, Review, Category


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['message']
        labels = {
            'message': _('Commentaire'),
        }
        widgets = {
            'message': forms.Textarea(attrs={'class': 'w-full p-3 border border-gray-300 rounded-lg', 'rows': 5, 'placeholder': _('Entrez votre commentaire')}),
        }

    def clean_message(self):
        message = self.cleaned_data.get('message')
        if len(message) < 10:
            raise forms.ValidationError(_("Le commentaire doit contenir au moins 10 caractères."))
        return message
