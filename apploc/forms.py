from django import forms
from .models import ContactMessage, Property, Photo, Video, Review
from django.forms import modelformset_factory
from django.utils.translation import gettext_lazy as _  # ← import pour i18n

class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = ['category', 'location', 'price_per_month', 'description', 'contact_phone', 'is_available']
        labels = {
            'category': _('Category'),
            'location': _('Location'),
            'price_per_month': _('Price per Month'),
            'description': _('Description'),
            'contact_phone': _('Contact Phone'),
            'is_available': _('Is Available'),
        }

class PhotoForm(forms.ModelForm):
    class Meta:
        model = Photo
        fields = ['image']
        labels = {
            'image': _('Image'),
        }

class VideoForm(forms.ModelForm):
    class Meta:
        model = Video
        fields = ['video_file']
        labels = {
            'video_file': _('Video File'),
        }

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['message']
        labels = {
            'message': _('Message'),
        }

PhotoFormSet = modelformset_factory(Photo, form=PhotoForm, extra=3)
VideoFormSet = modelformset_factory(Video, form=VideoForm, extra=2)

class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']
        labels = {
            'name': _('Name'),
            'email': _('Email'),
            'subject': _('Subject'),
            'message': _('Message'),
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full p-3 border border-gray-300 rounded-lg', 'placeholder': _('Your Name')}),
            'email': forms.EmailInput(attrs={'class': 'w-full p-3 border border-gray-300 rounded-lg', 'placeholder': _('Your Email')}),
            'subject': forms.TextInput(attrs={'class': 'w-full p-3 border border-gray-300 rounded-lg', 'placeholder': _('Subject')}),
            'message': forms.Textarea(attrs={'class': 'w-full p-3 border border-gray-300 rounded-lg', 'rows': 5, 'placeholder': _('Your Message')}),
        }
