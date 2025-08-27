from django.utils import translation  # ← bien le module, pas la fonction set_languagefrom django import forms
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _  # ← import pour i18n
from apploc.tasks import send_contact_email
from location import settings
from .models import Property, Review, Photo, Video
from .forms import ContactForm, PhotoFormSet, PropertyForm, PhotoForm, VideoForm, ReviewForm, VideoFormSet
from django.contrib.auth.decorators import login_required
from django.forms import modelformset_factory
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.translation import activate  # Importation corrigée

LANGUAGE_SESSION_KEY = 'django_language'

def home(request):
    properties = Property.objects.filter(is_available=True)
    reviews = Review.objects.select_related('tenant').order_by('-date_posted')[:3]
    is_authenticated = request.session.get('user_id') or (request.user.is_authenticated and request.user.is_staff)
    return render(request, 'home.html', {'properties': properties, 'reviews': reviews, 'is_authenticated': is_authenticated})

def all_properties(request):
    location = request.GET.get('location', '')
    property_type = request.GET.get('property_type', '')
    price_range = request.GET.get('price_range', '')
    
    properties = Property.objects.select_related('category', 'owner').prefetch_related('photos').all()
    
    if location:
        properties = properties.filter(location__icontains=location)
    
    if property_type:
        properties = properties.filter(category__name=property_type)
    
    if price_range:
        if price_range == '0-100000':
            properties = properties.filter(price__lte=100000)
        elif price_range == '100000-200000':
            properties = properties.filter(price__gte=100000, price__lte=200000)
        elif price_range == '200000-500000':
            properties = properties.filter(price__gte=200000, price__lte=500000)
        elif price_range == '500000+':
            properties = properties.filter(price__gte=500000)
    
    context = {
        'properties': properties,
        'location': location,
        'property_type': property_type,
        'price_range': price_range,
    }
    return render(request, 'all_properties.html', context)

def property_detail(request, property_id):
    property = get_object_or_404(Property, id=property_id)
    context = {'property': property}
    context['show_sensitive_info'] = bool(request.session.get('user_id'))
    return render(request, 'property_detail.html', context)

def all_reviews(request):
    reviews = Review.objects.select_related('tenant', 'property').order_by('-date_posted')
    is_authenticated = request.session.get('user_id') or (request.user.is_authenticated and request.user.is_staff)
    return render(request, 'all_reviews.html', {'reviews': reviews, 'is_authenticated': is_authenticated})

def property_create(request):
    if request.session.get('user_type') != 'owner':
        messages.error(request, _('Only owners can create properties.'))
        return redirect('login')
    
    if request.method == 'POST':
        property_form = PropertyForm(request.POST)
        photo_formset = PhotoFormSet(request.POST, request.FILES, prefix='photos')
        video_formset = VideoFormSet(request.POST, request.FILES, prefix='videos')
        
        print("request.FILES:", request.FILES)  # Débogage
        print("Photo formset valid:", photo_formset.is_valid())  # Débogage
        print("Photo formset errors:", photo_formset.errors)  # Débogage
        
        if property_form.is_valid() and photo_formset.is_valid() and video_formset.is_valid():
            property = property_form.save(commit=False)
            property.owner_id = request.session['user_id']
            property.save()
            
            for form in photo_formset:
                if form.cleaned_data.get('image'):
                    photo = form.save(commit=False)
                    photo.property = property
                    photo.save()
                    print(f"Photo saved: {photo.image.name}")  # Débogage
            
            for form in video_formset:
                if form.cleaned_data.get('video_file'):
                    video = form.save(commit=False)
                    video.property = property
                    video.save()
            
            messages.success(request, _('Property created successfully.'))
            return redirect('owner_dashboard')
    else:
        property_form = PropertyForm()
        # Initialiser PhotoFormSet avec un queryset vide
        photo_formset = PhotoFormSet(queryset=Photo.objects.none(), prefix='photos')
        video_formset = VideoFormSet(queryset=Video.objects.none(), prefix='videos')
    
    return render(request, 'property_form.html', {
        'property_form': property_form,
        'photo_formset': photo_formset,
        'video_formset': video_formset,
        'action': _('Create')
    })

def property_delete(request, property_id):
    if request.session.get('user_type') != 'owner':
        messages.error(request, _('Only owners can delete properties.'))
        return redirect('login')
    
    property = get_object_or_404(Property, id=property_id, owner_id=request.session['user_id'])
    if request.method == 'POST':
        property.delete()
        messages.success(request, _('Property deleted successfully.'))
        return redirect('owner_dashboard')
    return render(request, 'property_confirm_delete.html', {'property': property})

def review_list(request):
    if request.session.get('user_type') != 'tenant':
        messages.error(request, _('Only tenants can manage reviews.'))
        return redirect('login')
    
    reviews = Review.objects.filter(tenant_id=request.session['user_id'])
    return render(request, 'review_list.html', {'reviews': reviews})

def review_create(request, property_id):
    if request.session.get('user_type') != 'tenant':
        messages.error(request, _('Only tenants can create reviews.'))
        return redirect('login')
    
    property = get_object_or_404(Property, id=property_id)
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.tenant_id = request.session['user_id']
            review.property = property
            review.save()
            messages.success(request, _('Review created successfully.'))
            return redirect('review_list')
    else:
        form = ReviewForm()
    return render(request, 'review_form.html', {'form': form, 'property': property, 'action': _('Create')})

def review_update(request, review_id):
    if request.session.get('user_type') != 'tenant':
        messages.error(request, _('Only tenants can update reviews.'))
        return redirect('login')
    
    review = get_object_or_404(Review, id=review_id, tenant_id=request.session['user_id'])
    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, _('Review updated successfully.'))
            return redirect('review_list')
    else:
        form = ReviewForm(instance=review)
    return render(request, 'review_form.html', {'form': form, 'property': review.property, 'action': _('Update')})

def review_delete(request, review_id):
    if request.session.get('user_type') != 'tenant':
        messages.error(request, _('Only tenants can delete reviews.'))
        return redirect('login')
    
    review = get_object_or_404(Review, id=review_id, tenant_id=request.session['user_id'])
    if request.method == 'POST':
        review.delete()
        messages.success(request, _('Review deleted successfully.'))
        return redirect('review_list')
    return render(request, 'review_confirm_delete.html', {'review': review})

def about(request):
    from .forms import ContactForm
    form = ContactForm()
    return render(request, 'about.html', {'contact_form': form})

def dashboard_redirect(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin:index')
    elif request.session.get('user_id'):
        user_type = request.session.get('user_type')
        if user_type == 'owner':
            return redirect('owner_dashboard')
        elif user_type == 'tenant':
            return redirect('tenant_dashboard')
    messages.error(request, _('Please log in to access your dashboard.'))
    return redirect('login')


def contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            data = form.cleaned_data

            # Envoi en arrière-plan via Celery
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

    return render(request, "about.html", {"contact_form": form})

def set_language(request):
    if request.method == 'POST':
        language = request.POST.get('language')
        # On récupère l'URL précédente ou "/" par défaut
        next_url = request.POST.get('next', request.META.get('HTTP_REFERER', '/'))

        if language in dict(settings.LANGUAGES):
            # Active la langue pour la session en cours
            activate(language)
            request.session['django_language'] = language

            # Supprime l'ancien préfixe de langue dans l'URL
            for lang_code, _ in settings.LANGUAGES:
                if next_url.startswith(f'/{lang_code}/'):
                    next_url = next_url[len(lang_code) + 1:] or '/'
                    break

            # Ajoute le nouveau préfixe de langue
            next_url = f'/{language}{next_url}'

        return redirect(next_url)

    return redirect('/')

def property_update(request, property_id):
    if request.session.get('user_type') != 'owner':
        messages.error(request, _('Only owners can update properties.'))
        return redirect('login')
    
    property = get_object_or_404(Property, id=property_id, owner_id=request.session['user_id'])
    
    if request.method == 'POST':
        property_form = PropertyForm(request.POST, instance=property)
        photo_formset = PhotoFormSet(request.POST, request.FILES, prefix='photos')
        video_formset = VideoFormSet(request.POST, request.FILES, prefix='videos')
        
        if property_form.is_valid() and photo_formset.is_valid() and video_formset.is_valid():
            property_form.save()
            
            for form in photo_formset:
                if form.cleaned_data.get('image'):
                    photo = form.save(commit=False)
                    photo.property = property
                    photo.save()
            
            for form in video_formset:
                if form.cleaned_data.get('video_file'):
                    video = form.save(commit=False)
                    video.property = property
                    video.save()
            
            messages.success(request, _('Property updated successfully.'))
            return redirect('owner_dashboard')
    else:
        property_form = PropertyForm(instance=property)
        photo_formset = PhotoFormSet(prefix='photos')
        video_formset = VideoFormSet(prefix='videos')
    
    return render(request, 'property_form.html', {
        'property_form': property_form,
        'photo_formset': photo_formset,
        'video_formset': video_formset,
        'action': _('Update')
    })