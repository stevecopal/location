from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.forms import modelformset_factory
from apploc.tasks import send_contact_email
from location import settings
from .models import Category, Property, Review, Photo, Video
from .forms import ContactForm, PhotoFormSet, PropertyForm, VideoFormSet, ReviewForm
from django.utils.translation import activate

def home(request):
    properties = Property.objects.filter(is_available=True, deleted_at__isnull=True)
    reviews = Review.objects.select_related('tenant', 'property').filter(deleted_at__isnull=True).order_by('-date_posted')[:3]
    return render(request, 'home.html', {
        'properties': properties,
        'reviews': reviews,
        'is_authenticated': request.user.is_authenticated
    })

def all_properties(request):
    location = request.GET.get('location', '').strip()
    property_type = request.GET.get('property_type', '')
    price_range = request.GET.get('price_range', '')

    properties = Property.objects.select_related('category', 'owner').prefetch_related('photos').filter(deleted_at__isnull=True)

    if location:
        properties = properties.filter(location__icontains=location)
    if property_type:
        properties = properties.filter(category__name__iexact=property_type)
    if price_range:
        if price_range == 'under_100k':
            properties = properties.filter(price_per_month__lt=100000)
        elif price_range == '100k_200k':
            properties = properties.filter(price_per_month__gte=100000, price_per_month__lte=200000)
        elif price_range == '200k_500k':
            properties = properties.filter(price_per_month__gte=200000, price_per_month__lte=500000)
        elif price_range == 'over_500k':
            properties = properties.filter(price_per_month__gt=500000)

    context = {
        'properties': properties,
        'location': location,
        'property_type': property_type,
        'price_range': price_range,
        'categories': Category.objects.filter(deleted_at__isnull=True)
    }
    return render(request, 'all_properties.html', context)

def property_detail(request, property_id):
    property = get_object_or_404(Property, id=property_id, deleted_at__isnull=True)
    context = {
        'property': property,
        'show_sensitive_info': request.user.is_authenticated
    }
    return render(request, 'property_detail.html', context)

def all_reviews(request):
    reviews = Review.objects.select_related('tenant', 'property').filter(deleted_at__isnull=True).order_by('-date_posted')
    return render(request, 'all_reviews.html', {
        'reviews': reviews,
        'is_authenticated': request.user.is_authenticated
    })

@login_required
def property_create(request):
    if request.user.role != 'owner' or not request.user.is_approved:
        messages.error(request, _('Only approved owners can create properties.'))
        return redirect('login')

    if request.method == 'POST':
        property_form = PropertyForm(request.POST)
        photo_formset = PhotoFormSet(request.POST, request.FILES, prefix='photos')
        video_formset = VideoFormSet(request.POST, request.FILES, prefix='videos')

        if property_form.is_valid() and photo_formset.is_valid() and video_formset.is_valid():
            property = property_form.save(commit=False)
            property.owner = request.user
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

            messages.success(request, _('Property created successfully.'))
            return redirect('owner_dashboard')
    else:
        property_form = PropertyForm()
        photo_formset = PhotoFormSet(queryset=Photo.objects.none(), prefix='photos')
        video_formset = VideoFormSet(queryset=Video.objects.none(), prefix='videos')

    return render(request, 'property_form.html', {
        'property_form': property_form,
        'photo_formset': photo_formset,
        'video_formset': video_formset,
        'action': _('Create')
    })

@login_required
def property_update(request, property_id):
    if request.user.role != 'owner' or not request.user.is_approved:
        messages.error(request, _('Only approved owners can update properties.'))
        return redirect('login')

    property = get_object_or_404(Property, id=property_id, owner=request.user, deleted_at__isnull=True)

    if request.method == 'POST':
        property_form = PropertyForm(request.POST, instance=property)
        photo_formset = PhotoFormSet(request.POST, request.FILES, prefix='photos', queryset=Photo.objects.filter(property=property, deleted_at__isnull=True))
        video_formset = VideoFormSet(request.POST, request.FILES, prefix='videos', queryset=Video.objects.filter(property=property, deleted_at__isnull=True))

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
        photo_formset = PhotoFormSet(queryset=Photo.objects.filter(property=property, deleted_at__isnull=True), prefix='photos')
        video_formset = VideoFormSet(queryset=Video.objects.filter(property=property, deleted_at__isnull=True), prefix='videos')

    return render(request, 'property_form.html', {
        'property_form': property_form,
        'photo_formset': photo_formset,
        'video_formset': video_formset,
        'action': _('Update')
    })

@login_required
def property_delete(request, property_id):
    if request.user.role != 'owner' or not request.user.is_approved:
        messages.error(request, _('Only approved owners can delete properties.'))
        return redirect('login')

    property = get_object_or_404(Property, id=property_id, owner=request.user, deleted_at__isnull=True)
    if request.method == 'POST':
        property.soft_delete()
        messages.success(request, _('Property deleted successfully.'))
        return redirect('owner_dashboard')
    return render(request, 'property_confirm_delete.html', {'property': property})

@login_required
def review_list(request):
    if request.user.role != 'tenant':
        messages.error(request, _('Only tenants can manage reviews.'))
        return redirect('login')

    reviews = Review.objects.filter(tenant=request.user, deleted_at__isnull=True)
    return render(request, 'review_list.html', {'reviews': reviews})

@login_required
def review_create(request, property_id):
    if request.user.role != 'tenant':
        messages.error(request, _('Only tenants can create reviews.'))
        return redirect('login')

    property = get_object_or_404(Property, id=property_id, deleted_at__isnull=True)
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.tenant = request.user
            review.property = property
            review.save()
            messages.success(request, _('Review created successfully.'))
            return redirect('review_list')
    else:
        form = ReviewForm()
    return render(request, 'review_form.html', {'form': form, 'property': property, 'action': _('Create')})

@login_required
def review_update(request, review_id):
    if request.user.role != 'tenant':
        messages.error(request, _('Only tenants can update reviews.'))
        return redirect('login')

    review = get_object_or_404(Review, id=review_id, tenant=request.user, deleted_at__isnull=True)
    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, _('Review updated successfully.'))
            return redirect('review_list')
    else:
        form = ReviewForm(instance=review)
    return render(request, 'review_form.html', {'form': form, 'property': review.property, 'action': _('Update')})

@login_required
def review_delete(request, review_id):
    if request.user.role != 'tenant':
        messages.error(request, _('Only tenants can delete reviews.'))
        return redirect('login')

    review = get_object_or_404(Review, id=review_id, tenant=request.user, deleted_at__isnull=True)
    if request.method == 'POST':
        review.soft_delete()
        messages.success(request, _('Review deleted successfully.'))
        return redirect('review_list')
    return render(request, 'review_confirm_delete.html', {'review': review})

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