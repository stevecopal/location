from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns  # ← import pour i18n


urlpatterns = i18n_patterns(
    path('admin/', admin.site.urls),
    path('auth/', include('apploc.authentication.urls')),
    path('', include('apploc.urls')),
)

# Pour servir les fichiers statiques ou médias en mode debug
if settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
