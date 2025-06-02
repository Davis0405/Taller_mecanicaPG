# carwash/admin.py
from django.contrib import admin
from .models import PaqueteCarwash, TipoVehiculo, CitaCarwash, CalificacionCarwash, ProductoCarwash

@admin.register(PaqueteCarwash)
class PaqueteCarwashAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'precio_base', 'duracion_estimada', 'activo')
    list_filter = ('tipo', 'activo')
    search_fields = ('nombre', 'descripcion')

@admin.register(TipoVehiculo)
class TipoVehiculoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'factor_precio')
    search_fields = ('nombre',)

@admin.register(CitaCarwash)
class CitaCarwashAdmin(admin.ModelAdmin):
    list_display = ('cita', 'paquete', 'tipo_vehiculo', 'estado_proceso', 'precio_total', 'lavador_asignado')
    list_filter = ('estado_proceso', 'paquete', 'tipo_vehiculo')
    search_fields = ('cita__cliente__username', 'cita__vehiculo__placa')

@admin.register(CalificacionCarwash)
class CalificacionCarwashAdmin(admin.ModelAdmin):
    list_display = ('cita_carwash', 'puntuacion', 'fecha_calificacion')
    list_filter = ('puntuacion', 'fecha_calificacion')

@admin.register(ProductoCarwash)
class ProductoCarwashAdmin(admin.ModelAdmin):
    list_display = ('cita_carwash', 'producto', 'cantidad_utilizada', 'costo_total')
    search_fields = ('producto__nombre',)