from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('property/<uuid:property_id>/', views.property_detail, name='property_detail'),
    path('property/create/', views.property_create, name='property_create'),
    path('property/<uuid:property_id>/update/', views.property_update, name='property_update'),
    path('property/<uuid:property_id>/delete/', views.property_delete, name='property_delete'),
    path('reviews/', views.review_list, name='review_list'),
    path('property/<uuid:property_id>/review/create/', views.review_create, name='review_create'),
    path('review/<uuid:review_id>/update/', views.review_update, name='review_update'),
    path('review/<uuid:review_id>/delete/', views.review_delete, name='review_delete'),
    path('properties/all/', views.all_properties, name='all_properties'),
    path('about/', views.about, name='about'),
    path('dashboard/', views.dashboard_redirect, name='dashboard_redirect'),
    path('reviews/all/', views.all_reviews, name='all_reviews'),
    path('contact/', views.contact, name='contact'),
    path('set-language/', views.set_language, name='set_language'),
]