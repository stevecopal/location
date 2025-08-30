from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from apploc import views


urlpatterns = i18n_patterns(
    path('admin/', admin.site.urls),
    path('auth/', include('apploc.authentication.urls')),
    path('pro/', include('apploc.reviews.urls')),
    path('rev/', include('apploc.property.urls')),
    path('', include('apploc.urls')),
    path('create-superuser/', views.create_superuser, name='create_superuser'),
)

# Pour servir les fichiers statiques ou médias en mode debug
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)  # ← ajouter ceci
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
