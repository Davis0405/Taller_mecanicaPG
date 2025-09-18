# carwash/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Dashboard y vistas principales
    path('', views.dashboard_carwash, name='dashboard_carwash'),
    path('calendario/', views.calendario_carwash, name='calendario_carwash'),
    
    # Citas de carwash
    path('nueva-cita/', views.nueva_cita_carwash, name='nueva_cita_carwash'),
    path('mis-citas/', views.mis_citas_carwash, name='mis_citas_carwash'),
    
    # Servicios
    path('servicios/', views.servicios_carwash, name='servicios_carwash'),
    
    # Estadísticas
    path('estadisticas/', views.estadisticas_carwash, name='estadisticas_carwash'),
]