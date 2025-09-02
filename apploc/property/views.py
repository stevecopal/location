from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from .forms import PhotoFormSet, VideoFormSet, PropertyForm
from ..models import Category, Property, Photo, Video , Review

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
    photos = Photo.objects.filter(property=property, deleted_at__isnull=True).order_by('order')
    videos = Video.objects.filter(property=property, deleted_at__isnull=True).order_by('order')
    reviews = Review.objects.filter(property=property, deleted_at__isnull=True)
    context = {
        'property': property,
        'photos': photos,
        'videos': videos,
        'reviews': reviews,
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
        photo_formset = PhotoFormSet(request.POST, request.FILES, prefix='photos', queryset=Photo.objects.none())
        video_formset = VideoFormSet(request.POST, request.FILES, prefix='videos', queryset=Video.objects.none())

        if property_form.is_valid() and photo_formset.is_valid() and video_formset.is_valid():
            prop = property_form.save(commit=False)
            prop.owner = request.user
            prop.save()

            # --- Photos ---
            photos_added = 0
            for form in photo_formset:
                if form.cleaned_data.get('image'):
                    if photos_added >= 5:
                        messages.warning(request, _("You can upload a maximum of 5 photos per property."))
                        break
                    photo = form.save(commit=False)
                    photo.property = prop
                    photo.save()
                    photos_added += 1

            # --- Videos ---
            videos_added = 0
            for form in video_formset:
                if form.cleaned_data.get('video_file'):
                    if videos_added >= 2:
                        messages.warning(request, _("You can upload a maximum of 2 videos per property."))
                        break
                    video = form.save(commit=False)
                    video.property = prop
                    video.save()
                    videos_added += 1

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


import logging

logger = logging.getLogger(__name__)

@login_required
def property_update(request, property_id):
    if request.user.role != 'owner' or not request.user.is_approved:
        messages.error(request, _('Only approved owners can update properties.'))
        return redirect('login')

    prop = get_object_or_404(Property, id=property_id, owner=request.user, deleted_at__isnull=True)

    if request.method == 'POST':
        property_form = PropertyForm(request.POST, request.FILES, instance=prop)
        photo_formset = PhotoFormSet(
            request.POST, 
            request.FILES, 
            prefix='photos',
            queryset=Photo.objects.filter(property=prop, deleted_at__isnull=True)
        )
        video_formset = VideoFormSet(
            request.POST, 
            request.FILES, 
            prefix='videos',
            queryset=Video.objects.filter(property=prop, deleted_at__isnull=True)
        )

        if property_form.is_valid() and photo_formset.is_valid() and video_formset.is_valid():
            property_form.save()

            # --- Photos ---
            existing_photos_count = Photo.objects.filter(property=prop, deleted_at__isnull=True).count()
            for form in photo_formset:
                if form.cleaned_data:
                    if form.cleaned_data.get('DELETE') and form.instance.pk:
                        logger.info(f"Soft-deleting photo {form.instance.id} for property {prop.id}")
                        form.instance.soft_delete()
                        existing_photos_count -= 1
                    elif form.cleaned_data.get('image'):
                        if existing_photos_count >= 5:
                            messages.warning(request, _("Maximum 5 photos allowed per property."))
                            continue
                        photo = form.save(commit=False)
                        photo.property = prop
                        photo.save()
                        existing_photos_count += 1

            # --- Videos ---
            existing_videos_count = Video.objects.filter(property=prop, deleted_at__isnull=True).count()
            for form in video_formset:
                if form.cleaned_data:
                    if form.cleaned_data.get('DELETE') and form.instance.pk:
                        logger.info(f"Soft-deleting video {form.instance.id} for property {prop.id}")
                        form.instance.soft_delete()
                        existing_videos_count -= 1
                    elif form.cleaned_data.get('video_file'):
                        if existing_videos_count >= 2:
                            messages.warning(request, _("Maximum 2 videos allowed per property."))
                            continue
                        video = form.save(commit=False)
                        video.property = prop
                        video.save()
                        existing_videos_count += 1

            messages.success(request, _('Property updated successfully.'))
            return redirect('owner_dashboard')
    else:
        property_form = PropertyForm(instance=prop)
        photo_formset = PhotoFormSet(
            queryset=Photo.objects.filter(property=prop, deleted_at__isnull=True),
            prefix='photos'
        )
        video_formset = VideoFormSet(
            queryset=Video.objects.filter(property=prop, deleted_at__isnull=True),
            prefix='videos'
        )

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