from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('properties/all/', views.all_properties, name='all_properties'),
    path('properties/<uuid:property_id>/', views.property_detail, name='property_detail'),
    path('properties/create/', views.property_create, name='property_create'),
    path('properties/<uuid:property_id>/update/', views.property_update, name='property_update'),
    path('properties/<uuid:property_id>/delete/', views.property_delete, name='property_delete'),
    path('reviews/all/', views.all_reviews, name='all_reviews'),
    path('reviews/list/', views.review_list, name='review_list'),
    path('properties/<uuid:property_id>/review/create/', views.review_create, name='review_create'),
    path('reviews/<uuid:review_id>/update/', views.review_update, name='review_update'),
    path('reviews/<uuid:review_id>/delete/', views.review_delete, name='review_delete'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('set-language/', views.set_language, name='set_language'),
]