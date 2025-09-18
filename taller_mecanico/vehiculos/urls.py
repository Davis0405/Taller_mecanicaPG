from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_vehiculos, name='dashboard_vehiculos'),
    path('<int:vehiculo_id>/', views.detalle_vehiculo_completo, name='detalle_vehiculo_completo'),
    path('<int:vehiculo_id>/historial/', views.historial_servicios_vehiculo, name='historial_servicios_vehiculo'),
    path('<int:vehiculo_id>/estadisticas/', views.estadisticas_vehiculo, name='estadisticas_vehiculo'),
    path('cita/<int:cita_id>/historial/', views.crear_historial_detallado, name='crear_historial_detallado'),
    path('por-cliente/', views.vehiculos_por_cliente, name='vehiculos_por_cliente'),
]