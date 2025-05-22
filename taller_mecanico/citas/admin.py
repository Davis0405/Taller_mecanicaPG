# citas/admin.py
from django.contrib import admin
from .models import Vehiculo, Cita, TipoServicio, Notificacion

class VehiculoAdmin(admin.ModelAdmin):
    list_display = ('marca', 'modelo', 'año', 'placa', 'propietario')
    search_fields = ('marca', 'modelo', 'placa')
    list_filter = ('marca', 'año')

class CitaAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'servicio', 'fecha', 'hora_inicio', 'estado')
    list_filter = ('estado', 'fecha', 'servicio__categoria')
    search_fields = ('cliente__username', 'vehiculo__placa')
    date_hierarchy = 'fecha'

class TipoServicioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'duracion', 'precio')
    list_filter = ('categoria',)
    search_fields = ('nombre', 'descripcion')

class NotificacionAdmin(admin.ModelAdmin):
    list_display = ('cita', 'tipo', 'fecha_envio', 'enviado')
    list_filter = ('tipo', 'enviado')

admin.site.register(Vehiculo, VehiculoAdmin)
admin.site.register(Cita, CitaAdmin)
admin.site.register(TipoServicio, TipoServicioAdmin)
admin.site.register(Notificacion, NotificacionAdmin)