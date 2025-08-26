from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.tenant_signup, name='signup'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('tenant_dashboard/', views.tenant_dashboard, name='tenant_dashboard'),
    path('owner_dashboard/', views.owner_dashboard, name= 'owner_dashboard'),
]