
from django.urls import path
from . import views

urlpatterns = [
    path('reviews/all/', views.all_reviews, name='all_reviews'),
    path('reviews/list/', views.review_list, name='review_list'),
    path('properties/<uuid:property_id>/review/create/', views.review_create, name='review_create'),
    path('reviews/<uuid:review_id>/update/', views.review_update, name='review_update'),
    path('reviews/<uuid:review_id>/delete/', views.review_delete, name='review_delete'),
    
]