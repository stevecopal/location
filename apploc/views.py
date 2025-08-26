from django import forms
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from location import settings
from .models import Property, Review, Photo, Video
from .forms import ContactForm, PhotoFormSet, PropertyForm, PhotoForm, VideoForm, ReviewForm, VideoFormSet
from django.contrib.auth.decorators import login_required
from django.forms import modelformset_factory
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

def home(request):
    properties = Property.objects.filter(is_available=True)
    reviews = Review.objects.select_related('tenant').order_by('-date_posted')[:3]  # Get 3 latest reviews
    is_authenticated = request.session.get('user_id') or (request.user.is_authenticated and request.user.is_staff)
    return render(request, 'home.html', {'properties': properties, 'reviews': reviews, 'is_authenticated': is_authenticated})

# def all_properties(request):
#     properties = Property.objects.all()
#     return render(request, 'all_properties.html', {'properties': properties})

def all_properties(request):
    location = request.GET.get('location', '')
    property_type = request.GET.get('property_type', '')
    price_range = request.GET.get('price_range', '')
    
    # Start with all properties
    properties = Property.objects.all()
    
    # Filter by location (case-insensitive partial match)
    if location:
        properties = properties.filter(location__icontains=location)
    
    # Filter by property type
    if property_type:
        properties = properties.filter(category__name=property_type)
    
    # Filter by price range
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
    if request.session.get('user_id'):
        context['show_sensitive_info'] = True
    else:
        context['show_sensitive_info'] = False
    return render(request, 'property_detail.html', context)

def all_reviews(request):
    reviews = Review.objects.select_related('tenant', 'property').order_by('-date_posted')
    is_authenticated = request.session.get('user_id') or (request.user.is_authenticated and request.user.is_staff)
    return render(request, 'all_reviews.html', {'reviews': reviews, 'is_authenticated': is_authenticated})


def property_create(request):
    if request.session.get('user_type') != 'owner':
        messages.error(request, 'Only owners can create properties.')
        return redirect('login')
    
    if request.method == 'POST':
        property_form = PropertyForm(request.POST)
        photo_formset = PhotoFormSet(request.POST, request.FILES, prefix='photos')
        video_formset = VideoFormSet(request.POST, request.FILES, prefix='videos')
        
        if property_form.is_valid() and photo_formset.is_valid() and video_formset.is_valid():
            property = property_form.save(commit=False)
            property.owner_id = request.session['user_id']
            property.save()
            
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
            
            messages.success(request, 'Property created successfully.')
            return redirect('owner_dashboard')
    else:
        property_form = PropertyForm()
        photo_formset = PhotoFormSet(prefix='photos')
        video_formset = VideoFormSet(prefix='videos')
    
    return render(request, 'property_form.html', {
        'property_form': property_form,
        'photo_formset': photo_formset,
        'video_formset': video_formset,
        'action': 'Create'
    })


def property_update(request, property_id):
    if request.session.get('user_type') != 'owner':
        messages.error(request, 'Only owners can update properties.')
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
            
            messages.success(request, 'Property updated successfully.')
            return redirect('owner_dashboard')
    else:
        property_form = PropertyForm(instance=property)
        photo_formset = PhotoFormSet(prefix='photos')
        video_formset = VideoFormSet(prefix='videos')
    
    return render(request, 'property_form.html', {
        'property_form': property_form,
        'photo_formset': photo_formset,
        'video_formset': video_formset,
        'action': 'Update'
    })


def property_delete(request, property_id):
    if request.session.get('user_type') != 'owner':
        messages.error(request, 'Only owners can delete properties.')
        return redirect('login')
    
    property = get_object_or_404(Property, id=property_id, owner_id=request.session['user_id'])
    if request.method == 'POST':
        property.delete()
        messages.success(request, 'Property deleted successfully.')
        return redirect('owner_dashboard')
    return render(request, 'property_confirm_delete.html', {'property': property})


def review_list(request):
    if request.session.get('user_type') != 'tenant':
        messages.error(request, 'Only tenants can manage reviews.')
        return redirect('login')
    
    reviews = Review.objects.filter(tenant_id=request.session['user_id'])
    return render(request, 'review_list.html', {'reviews': reviews})


def review_create(request, property_id):
    if request.session.get('user_type') != 'tenant':
        messages.error(request, 'Only tenants can create reviews.')
        return redirect('login')
    
    property = get_object_or_404(Property, id=property_id)
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.tenant_id = request.session['user_id']
            review.property = property
            review.save()
            messages.success(request, 'Review created successfully.')
            return redirect('review_list')
    else:
        form = ReviewForm()
    return render(request, 'review_form.html', {'form': form, 'property': property, 'action': 'Create'})


def review_update(request, review_id):
    if request.session.get('user_type') != 'tenant':
        messages.error(request, 'Only tenants can update reviews.')
        return redirect('login')
    
    review = get_object_or_404(Review, id=review_id, tenant_id=request.session['user_id'])
    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, 'Review updated successfully.')
            return redirect('review_list')
    else:
        form = ReviewForm(instance=review)
    return render(request, 'review_form.html', {'form': form, 'property': review.property, 'action': 'Update'})

def review_delete(request, review_id):
    if request.session.get('user_type') != 'tenant':
        messages.error(request, 'Only tenants can delete reviews.')
        return redirect('login')
    
    review = get_object_or_404(Review, id=review_id, tenant_id=request.session['user_id'])
    if request.method == 'POST':
        review.delete()
        messages.success(request, 'Review deleted successfully.')
        return redirect('review_list')
    return render(request, 'review_confirm_delete.html', {'review': review})

def about(request):
    from .forms import ContactForm  # Import explicite pour éviter NameError
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
    messages.error(request, 'Please log in to access your dashboard.')
    return redirect('login')


def contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            data = form.cleaned_data
            subject = f"New Contact Message: {data['subject']}"
            from_email = settings.DEFAULT_FROM_EMAIL
            to_email = [settings.EMAIL_HOST_USER]

            # Render HTML content
            html_content = render_to_string("emails/contact_email.html", {"data": data})
            text_content = f"Name: {data['name']}\nEmail: {data['email']}\nMessage: {data['message']}"

            email = EmailMultiAlternatives(subject, text_content, from_email, to_email)
            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=False)

            messages.success(request, "Votre message a été envoyé avec succès !")
            return redirect('contact')
    else:
        form = ContactForm()

    return render(request, "about.html", {"contact_form": form})