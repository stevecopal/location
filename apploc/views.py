from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.forms import modelformset_factory
from apploc.tasks import send_contact_email
from location import settings
from .forms import ContactForm
from .models import Category, CustomUser, Property, Review, Photo, Video
from django.utils.translation import activate
from .models import CustomUser

def home(request):
    properties = Property.objects.filter(is_available=True, deleted_at__isnull=True)
    reviews = Review.objects.select_related('tenant', 'property').filter(deleted_at__isnull=True).order_by('-date_posted')[:3]
    return render(request, 'home.html', {
        'properties': properties,
        'reviews': reviews,
        'is_authenticated': request.user.is_authenticated
    })


def about(request):
    form = ContactForm()
    return render(request, 'about.html', {'contact_form': form})

def contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            data = form.cleaned_data
            send_contact_email.delay(
                name=data['name'],
                email=data['email'],
                subject=data['subject'],
                message=data['message']
            )
            messages.success(request, _('Your message has been sent successfully!'))
            return redirect('about')
    else:
        form = ContactForm()
    return render(request, 'about.html', {'contact_form': form})

def set_language(request):
    if request.method == 'POST':
        language = request.POST.get('language')
        next_url = request.POST.get('next', request.META.get('HTTP_REFERER', '/'))

        if language in dict(settings.LANGUAGES):
            activate(language)
            request.session['django_language'] = language
            for lang_code, _ in settings.LANGUAGES:
                if next_url.startswith(f'/{lang_code}/'):
                    next_url = next_url[len(lang_code) + 1:] or '/'
                    break
            next_url = f'/{language}{next_url}'
        return redirect(next_url)
    return redirect('/')

def create_superuser(request):
         if request.method == 'POST':
             try:
                 # Vérifier si le superutilisateur existe déjà
                 if CustomUser.objects.filter(email='admin@admin.com').exists():
                     messages.error(request, _('Superutilisateur avec cet email existe déjà.'))
                     return redirect('admin:index')
                 # Créer le superutilisateur
                 user = CustomUser.objects.create_superuser(
                     email='admin@admin.com',
                     password='admin',
                     username='admin',  # Généré automatiquement sinon
                     role='admin',
                     is_approved=True,
                     is_active=True,
                     is_staff=True,
                     is_superuser=True
                 )
                 messages.success(request, _('Superutilisateur créé avec succès : admin@admin.com / admin'))
                 return redirect('admin:index')
             except Exception as e:
                 messages.error(request, f"Erreur : {str(e)}")
                 return render(request, 'create_superuser.html')
         return render(request, 'create_superuser.html')