# vehiculos/models.py (expandir el modelo existente en citas/models.py)
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Nota: Este sería el modelo expandido. El actual en citas/models.py se puede extender

class HistorialServicio(models.Model):
    """Historial detallado de servicios por vehículo"""
    vehiculo = models.ForeignKey('citas.Vehiculo', on_delete=models.CASCADE, related_name='historial_servicios')
    cita = models.ForeignKey('citas.Cita', on_delete=models.CASCADE, related_name='historial_detallado')
    
    # Detalles del servicio
    fecha_servicio = models.DateField()
    descripcion_trabajo = models.TextField()
    observaciones_mecanico = models.TextField(blank=True)
    kilometraje = models.PositiveIntegerField(null=True, blank=True)
    
    # Costos
    costo_mano_obra = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    costo_repuestos = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    costo_total = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Control
    mecanico_responsable = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='servicios_realizados'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        # Calcular costo total automáticamente
        self.costo_total = self.costo_mano_obra + self.costo_repuestos
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.vehiculo} - {self.fecha_servicio} - {self.cita.servicio.nombre}"
    
    class Meta:
        ordering = ['-fecha_servicio']
        verbose_name = "Historial de Servicio"
        verbose_name_plural = "Historiales de Servicios"

class RepuestoUtilizado(models.Model):
    """Repuestos utilizados en cada servicio"""
    historial_servicio = models.ForeignKey(
        HistorialServicio, 
        on_delete=models.CASCADE,
        related_name='repuestos_utilizados'
    )
    producto = models.ForeignKey('inventario.Producto', on_delete=models.CASCADE)
    cantidad_utilizada = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    
    @property
    def subtotal(self):
        return self.cantidad_utilizada * self.precio_unitario
    
    def __str__(self):
        return f"{self.producto.nombre} x{self.cantidad_utilizada}"

class MantenimientoRecomendado(models.Model):
    """Mantenimientos recomendados por vehículo"""
    PRIORIDAD_CHOICES = (
        ('BAJA', 'Baja'),
        ('MEDIA', 'Media'),
        ('ALTA', 'Alta'),
        ('URGENTE', 'Urgente'),
    )
    
    vehiculo = models.ForeignKey('citas.Vehiculo', on_delete=models.CASCADE, related_name='mantenimientos_recomendados')
    servicio_recomendado = models.ForeignKey('citas.TipoServicio', on_delete=models.CASCADE)
    
    fecha_recomendacion = models.DateField(auto_now_add=True)
    fecha_vencimiento = models.DateField()
    kilometraje_recomendado = models.PositiveIntegerField(null=True, blank=True)
    
    prioridad = models.CharField(max_length=10, choices=PRIORIDAD_CHOICES, default='MEDIA')
    descripcion = models.TextField()
    completado = models.BooleanField(default=False)
    fecha_completado = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.vehiculo} - {self.servicio_recomendado.nombre}"
    
    @property
    def esta_vencido(self):
        return timezone.now().date() > self.fecha_vencimiento
    
    class Meta:
        ordering = ['fecha_vencimiento', '-prioridad']