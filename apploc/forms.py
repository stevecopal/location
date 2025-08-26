from django import forms
from .models import ContactMessage, Property, Photo, Video, Review
from django.forms import modelformset_factory

class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = ['category', 'location', 'price_per_month', 'description', 'contact_phone', 'is_available']

class PhotoForm(forms.ModelForm):
    class Meta:
        model = Photo
        fields = ['image']

class VideoForm(forms.ModelForm):
    class Meta:
        model = Video
        fields = ['video_file']

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['message']

PhotoFormSet = modelformset_factory(Photo, form=PhotoForm, extra=3)
VideoFormSet = modelformset_factory(Video, form=VideoForm, extra=2)

class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full p-3 border border-gray-300 rounded-lg', 'placeholder': 'Your Name'}),
            'email': forms.EmailInput(attrs={'class': 'w-full p-3 border border-gray-300 rounded-lg', 'placeholder': 'Your Email'}),
            'subject': forms.TextInput(attrs={'class': 'w-full p-3 border border-gray-300 rounded-lg', 'placeholder': 'Subject'}),
            'message': forms.Textarea(attrs={'class': 'w-full p-3 border border-gray-300 rounded-lg', 'rows': 5, 'placeholder': 'Your Message'}),
        }