# citas/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # URLs para vehículos
    path('vehiculos/', views.lista_vehiculos, name='lista_vehiculos'),
    path('vehiculos/agregar/', views.agregar_vehiculo, name='agregar_vehiculo'),
    path('vehiculos/<int:vehiculo_id>/editar/', views.editar_vehiculo, name='editar_vehiculo'),
    path('vehiculos/<int:vehiculo_id>/eliminar/', views.eliminar_vehiculo, name='eliminar_vehiculo'),
    
    # URLs para citas
    path('mis-citas/', views.mis_citas, name='mis_citas'),
    path('nueva-cita/', views.seleccionar_fecha_hora, name='seleccionar_fecha_hora'),
    path('nueva-cita/<str:fecha>/<str:categoria>/', views.nueva_cita, name='nueva_cita'),
    path('cita/<int:cita_id>/', views.detalle_cita, name='detalle_cita'),
    path('cita/<int:cita_id>/cancelar/', views.cancelar_cita, name='cancelar_cita'),
    
    # API para horas disponibles
    path('horas-disponibles/', views.horas_disponibles, name='horas_disponibles'),
    
    # URLs para personal (admin, mecánicos, recepcionistas)
    path('calendario/', views.calendario_citas, name='calendario_citas'),
    path('cita/<int:cita_id>/gestionar/', views.gestionar_cita, name='gestionar_cita'),
    
    # URLs para tipos de servicio
    path('servicios/', views.lista_servicios, name='lista_servicios'),
    path('servicios/agregar/', views.agregar_servicio, name='agregar_servicio'),
    path('servicios/<int:servicio_id>/editar/', views.editar_servicio, name='editar_servicio'),
    path('servicios/<int:servicio_id>/eliminar/', views.eliminar_servicio, name='eliminar_servicio'),
]