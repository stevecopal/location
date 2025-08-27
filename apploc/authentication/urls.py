from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.tenant_signup, name='signup'),
    path('verify-email/<str:email>/', views.verify_email, name='verify_email'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('password-reset/', views.password_reset_request, name='password_reset_request'),
    path('password-reset/verify/<str:email>/', views.password_reset_verify, name='password_reset_verify'),
    path('owner/dashboard/', views.owner_dashboard, name='owner_dashboard'),
    path('tenant/dashboard/', views.tenant_dashboard, name='tenant_dashboard'),
]