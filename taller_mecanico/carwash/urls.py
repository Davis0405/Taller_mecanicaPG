# carwash/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard_carwash, name='dashboard_carwash'),
    path('tablero/', views.tablero_tiempo_real, name='tablero_carwash'),
    
    # Paquetes
    path('paquetes/', views.lista_paquetes, name='lista_paquetes_carwash'),
    path('paquetes/agregar/', views.agregar_paquete, name='agregar_paquete_carwash'),
    path('paquetes/<int:paquete_id>/editar/', views.editar_paquete, name='editar_paquete_carwash'),
    
    # Tipos de vehículo
    path('tipos-vehiculo/', views.lista_tipos_vehiculo, name='lista_tipos_vehiculo'),
    path('tipos-vehiculo/agregar/', views.agregar_tipo_vehiculo, name='agregar_tipo_vehiculo'),
    
    # Citas de carwash
    path('citas/', views.lista_citas_carwash, name='lista_citas_carwash'),
    path('citas/<int:cita_id>/', views.detalle_cita_carwash, name='detalle_cita_carwash'),
    path('citas/<int:cita_id>/gestionar/', views.gestionar_cita_carwash, name='gestionar_cita_carwash'),
    
    # Calificaciones
    path('calificar/<int:cita_id>/', views.calificar_servicio, name='calificar_carwash'),
    
    # Reportes
    path('reportes/ventas/', views.reporte_ventas_carwash, name='reporte_ventas_carwash'),
    
    # API
    path('api/precio/<int:paquete_id>/<int:tipo_vehiculo_id>/', views.api_precio_paquete, name='api_precio_paquete'),
    path('tipos-vehiculo/', views.lista_tipos_vehiculo, name='lista_tipos_vehiculo'),
    path('tipos-vehiculo/agregar/', views.agregar_tipo_vehiculo, name='agregar_tipo_vehiculo'),
    path('tipos-vehiculo/<int:tipo_id>/editar/', views.editar_tipo_vehiculo, name='editar_tipo_vehiculo'),  # Agregar esta línea
]