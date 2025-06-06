# taller_mecanico/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('usuarios/', include('usuarios.urls')),
    path('citas/', include('citas.urls')),
    path('inventario/', include('inventario.urls')), 
    path('carwash/', include('carwash.urls')),
    path('', RedirectView.as_view(url='usuarios/dashboard/', permanent=True)),  # Redirección a dashboard
]

# Sirve los archivos estáticos y de media durante el desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)