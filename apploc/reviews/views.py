from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.forms import modelformset_factory
from apploc.tasks import send_contact_email
from location import settings
from ..models import Category, Property, Review, Photo, Video
from ..reviews.forms import  ReviewForm
from django.utils.translation import activate

def all_reviews(request):
    reviews = Review.objects.select_related('tenant', 'property').filter(deleted_at__isnull=True).order_by('-date_posted')
    return render(request, 'reviews/all_reviews.html', {
        'reviews': reviews,
        'is_authenticated': request.user.is_authenticated
    })
    
@login_required
def review_list(request):
    if request.user.role != 'tenant':
        messages.error(request, _('Only tenants can manage reviews.'))
        return redirect('login')

    reviews = Review.objects.filter(tenant=request.user, deleted_at__isnull=True)
    return render(request, 'reviews/review_list.html', {'reviews': reviews})

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
    return render(request, 'reviews/review_form.html', {'form': form, 'property': property, 'action': _('Create')})

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
    return render(request, 'reviews/review_form.html', {'form': form, 'property': review.property, 'action': _('Update')})

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
    return render(request, 'reviews/review_confirm_delete.html', {'review': review})