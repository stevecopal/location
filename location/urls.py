from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns  # ← import pour i18n

urlpatterns = [
    # URLs non-traduites (ex: admin, auth) peuvent rester ici
    path('admin/', admin.site.urls),
]

urlpatterns += i18n_patterns(
    
    path('auth/', include('apploc.authentication.urls')),
    path('', include('apploc.urls')),
    path('set-language/', include('apploc.urls')),  # Inclure set_language dans i18n_patterns
)

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
