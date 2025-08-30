from django.urls import path
from . import views

urlpatterns = [
    path('properties/all/', views.all_properties, name='all_properties'),
    path('properties/<uuid:property_id>/', views.property_detail, name='property_detail'),
    path('properties/create/', views.property_create, name='property_create'),
    path('properties/<uuid:property_id>/update/', views.property_update, name='property_update'),
    path('properties/<uuid:property_id>/delete/', views.property_delete, name='property_delete'),
    
]