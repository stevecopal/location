from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from .forms import PhotoFormSet, VideoFormSet, PropertyForm
from ..models import Category, Property, Photo, Video

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
    return render(request, 'property/all_properties.html', context)

def property_detail(request, property_id):
    property = get_object_or_404(Property, id=property_id, deleted_at__isnull=True)
    context = {
        'property': property,
        'show_sensitive_info': request.user.is_authenticated
    }
    return render(request, 'property/property_detail.html', context)

@login_required
def property_create(request):
    if request.user.role != 'owner' or not request.user.is_approved:
        messages.error(request, _('Only approved owners can create properties.'))
        return redirect('login')

    if request.method == 'POST':
        property_form = PropertyForm(request.POST, request.FILES)
        photo_formset = PhotoFormSet(request.POST, request.FILES, prefix='photos')
        video_formset = VideoFormSet(request.POST, request.FILES, prefix='videos')

        if property_form.is_valid() and photo_formset.is_valid() and video_formset.is_valid():
            # Sauvegarder la propriété
            property = property_form.save(commit=False)
            property.owner = request.user
            property.save()

            # Sauvegarder les photos
            for form in photo_formset:
                if form.cleaned_data and form.cleaned_data.get('image'):
                    photo = form.save(commit=False)
                    photo.property = property
                    photo.save()

            # Sauvegarder les vidéos
            for form in video_formset:
                if form.cleaned_data and form.cleaned_data.get('video_file'):
                    video = form.save(commit=False)
                    video.property = property
                    video.save()

            messages.success(request, _('Property created successfully.'))
            return redirect('owner_dashboard')
    else:
        property_form = PropertyForm()
        photo_formset = PhotoFormSet(queryset=Photo.objects.none(), prefix='photos')
        video_formset = VideoFormSet(queryset=Video.objects.none(), prefix='videos')

    return render(request, 'property/property_form.html', {
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
        property_form = PropertyForm(request.POST, request.FILES, instance=property)
        photo_formset = PhotoFormSet(request.POST, request.FILES, prefix='photos', queryset=Photo.objects.filter(property=property, deleted_at__isnull=True))
        video_formset = VideoFormSet(request.POST, request.FILES, prefix='videos', queryset=Video.objects.filter(property=property, deleted_at__isnull=True))

        if property_form.is_valid() and photo_formset.is_valid() and video_formset.is_valid():
            property_form.save()

            # Sauvegarder ou supprimer les photos
            for form in photo_formset:
                if form.cleaned_data:
                    if form.cleaned_data.get('DELETE'):
                        if form.instance.pk:
                            form.instance.soft_delete()
                    elif form.cleaned_data.get('image'):
                        photo = form.save(commit=False)
                        photo.property = property
                        photo.save()

            # Sauvegarder ou supprimer les vidéos
            for form in video_formset:
                if form.cleaned_data:
                    if form.cleaned_data.get('DELETE'):
                        if form.instance.pk:
                            form.instance.soft_delete()
                    elif form.cleaned_data.get('video_file'):
                        video = form.save(commit=False)
                        video.property = property
                        video.save()

            messages.success(request, _('Property updated successfully.'))
            return redirect('owner_dashboard')
    else:
        property_form = PropertyForm(instance=property)
        photo_formset = PhotoFormSet(queryset=Photo.objects.filter(property=property, deleted_at__isnull=True), prefix='photos')
        video_formset = VideoFormSet(queryset=Video.objects.filter(property=property, deleted_at__isnull=True), prefix='videos')

    return render(request, 'property/property_form.html', {
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
    return render(request, 'property/property_confirm_delete.html', {'property': property})