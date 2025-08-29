from django import forms
from django.forms import modelformset_factory
from django.utils.translation import gettext_lazy as _
from .models import ContactMessage, Property, Photo, Video, Review, Category

class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = ['category', 'location', 'price_per_month', 'description', 'contact_phone', 'is_available']
        labels = {
            'category': _('Catégorie'),
            'location': _('Localisation'),
            'price_per_month': _('Prix par mois'),
            'description': _('Description'),
            'contact_phone': _('Téléphone de contact'),
            'is_available': _('Disponible'),
        }
        widgets = {
            'category': forms.Select(attrs={'class': 'w-full p-3 border border-gray-300 rounded-lg'}),
            'location': forms.TextInput(attrs={'class': 'w-full p-3 border border-gray-300 rounded-lg', 'placeholder': _('Entrez la localisation')}),
            'price_per_month': forms.NumberInput(attrs={'class': 'w-full p-3 border border-gray-300 rounded-lg', 'placeholder': _('Entrez le prix par mois')}),
            'description': forms.Textarea(attrs={'class': 'w-full p-3 border border-gray-300 rounded-lg', 'rows': 5, 'placeholder': _('Décrivez la propriété')}),
            'contact_phone': forms.TextInput(attrs={'class': 'w-full p-3 border border-gray-300 rounded-lg', 'placeholder': _('Entrez le numéro de contact')}),
            'is_available': forms.CheckboxInput(attrs={'class': 'h-5 w-5 text-blue-600'}),
        }

    def clean_price_per_month(self):
        price = self.cleaned_data.get('price_per_month')
        if price <= 0:
            raise forms.ValidationError(_("Le prix par mois doit être supérieur à 0."))
        return price

    def clean_contact_phone(self):
        phone = self.cleaned_data.get('contact_phone')
        if not phone.isdigit() or len(phone) < 8:
            raise forms.ValidationError(_("Le numéro de téléphone doit contenir au moins 8 chiffres."))
        return phone

class PhotoForm(forms.ModelForm):
    class Meta:
        model = Photo
        fields = ['image']
        labels = {
            'image': _('Image'),
        }
        widgets = {
            'image': forms.ClearableFileInput(attrs={'class': 'w-full p-3 border border-gray-300 rounded-lg'}),
        }

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            # Vérifier que c'est bien un fichier uploadé
            if hasattr(image, 'content_type'):
                valid_formats = ['image/jpeg', 'image/png', 'image/jpg']
                if image.content_type not in valid_formats:
                    raise forms.ValidationError("Format d'image non valide. Utilisez JPEG ou PNG.")
                if image.size > 5 * 1024 * 1024:
                    raise forms.ValidationError("L'image ne doit pas dépasser 5 Mo.")

class VideoForm(forms.ModelForm):
    class Meta:
        model = Video
        fields = ['video_file']
        labels = {
            'video_file': _('Fichier vidéo'),
        }
        widgets = {
            'video_file': forms.ClearableFileInput(attrs={'class': 'w-full p-3 border border-gray-300 rounded-lg'}),
        }

    def clean_video_file(self):
        video = self.cleaned_data.get('video_file')
        if video:
            # Vérifier si c'est un nouveau fichier uploadé
            if hasattr(video, 'content_type'):
                valid_formats = ['video/mp4', 'video/webm', 'video/ogg']
                if video.content_type not in valid_formats:
                    raise forms.ValidationError("Format de vidéo non valide. Utilisez MP4, WEBM ou OGG.")
                if video.size > 50 * 1024 * 1024:  # 50 Mo max
                    raise forms.ValidationError("La vidéo ne doit pas dépasser 50 Mo.")
        return video
        return video

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

PhotoFormSet = modelformset_factory(Photo, form=PhotoForm, extra=3, can_delete=True)
VideoFormSet = modelformset_factory(Video, form=VideoForm, extra=2, can_delete=True)

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