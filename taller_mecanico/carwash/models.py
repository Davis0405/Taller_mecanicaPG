# carwash/models.py
from django.db import models
from django.contrib.auth.models import User
from citas.models import Cita, TipoServicio
from inventario.models import Producto
from django.utils import timezone

class PaqueteCarwash(models.Model):
    TIPOS_LAVADO = (
        ('BASICO', 'Lavado Básico'),
        ('COMPLETO', 'Lavado Completo'),
        ('PREMIUM', 'Lavado Premium'),
        ('DETALLADO', 'Detallado Completo'),
    )
    
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=10, choices=TIPOS_LAVADO)
    descripcion = models.TextField()
    precio_base = models.DecimalField(max_digits=8, decimal_places=2)
    duracion_estimada = models.IntegerField(help_text="Duración en minutos")
    activo = models.BooleanField(default=True)
    
    # Servicios incluidos
    incluye_lavado_exterior = models.BooleanField(default=True)
    incluye_lavado_interior = models.BooleanField(default=False)
    incluye_aspirado = models.BooleanField(default=False)
    incluye_encerado = models.BooleanField(default=False)
    incluye_llantas = models.BooleanField(default=False)
    incluye_motor = models.BooleanField(default=False)
    incluye_proteccion_uv = models.BooleanField(default=False)
    incluye_aromatizacion = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.nombre} - Q{self.precio_base}"
    
    def get_servicios_incluidos(self):
        """Retorna lista de servicios incluidos"""
        servicios = []
        if self.incluye_lavado_exterior:
            servicios.append("Lavado exterior")
        if self.incluye_lavado_interior:
            servicios.append("Lavado interior")
        if self.incluye_aspirado:
            servicios.append("Aspirado")
        if self.incluye_encerado:
            servicios.append("Encerado")
        if self.incluye_llantas:
            servicios.append("Limpieza de llantas")
        if self.incluye_motor:
            servicios.append("Lavado de motor")
        if self.incluye_proteccion_uv:
            servicios.append("Protección UV")
        if self.incluye_aromatizacion:
            servicios.append("Aromatización")
        return servicios
    
    class Meta:
        verbose_name_plural = "Paquetes de Carwash"

class TipoVehiculo(models.Model):
    nombre = models.CharField(max_length=50)  # Sedán, SUV, Pickup, etc.
    factor_precio = models.DecimalField(max_digits=4, decimal_places=2, default=1.0)
    descripcion = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name_plural = "Tipos de Vehículo"

class CitaCarwash(models.Model):
    ESTADOS_PROCESO = (
        ('EN_ESPERA', 'En Espera'),
        ('LAVANDO', 'En Proceso de Lavado'),
        ('SECANDO', 'Secando'),
        ('FINALIZANDO', 'Finalizando Detalles'),
        ('TERMINADO', 'Terminado'),
        ('ENTREGADO', 'Entregado'),
    )
    
    cita = models.OneToOneField(Cita, on_delete=models.CASCADE, related_name='carwash_detalle')
    paquete = models.ForeignKey(PaqueteCarwash, on_delete=models.CASCADE)
    tipo_vehiculo = models.ForeignKey(TipoVehiculo, on_delete=models.CASCADE)
    estado_proceso = models.CharField(max_length=15, choices=ESTADOS_PROCESO, default='EN_ESPERA')
    
    # Precios calculados
    precio_base = models.DecimalField(max_digits=8, decimal_places=2)
    precio_total = models.DecimalField(max_digits=8, decimal_places=2)
    
    # Tiempos de proceso
    hora_inicio_proceso = models.DateTimeField(null=True, blank=True)
    hora_fin_proceso = models.DateTimeField(null=True, blank=True)
    
    # Personal asignado
    lavador_asignado = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='carwash_asignadas'
    )
    
    # Servicios adicionales
    servicios_adicionales = models.TextField(blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    
    def calcular_precio_total(self):
        """Calcular precio total basado en paquete y tipo de vehículo"""
        self.precio_base = self.paquete.precio_base
        self.precio_total = self.precio_base * self.tipo_vehiculo.factor_precio
        return self.precio_total
    
    def save(self, *args, **kwargs):
        # Calcular precio automáticamente
        self.calcular_precio_total()
        super().save(*args, **kwargs)
    
    def duracion_real(self):
        """Calcular duración real del servicio"""
        if self.hora_inicio_proceso and self.hora_fin_proceso:
            delta = self.hora_fin_proceso - self.hora_inicio_proceso
            return delta.total_seconds() / 60  # minutos
        return None
    
    def __str__(self):
        return f"Carwash #{self.cita.id} - {self.paquete.nombre}"
    
    class Meta:
        verbose_name_plural = "Citas de Carwash"

class ProductoCarwash(models.Model):
    """Productos utilizados en servicios de carwash"""
    cita_carwash = models.ForeignKey(CitaCarwash, on_delete=models.CASCADE, related_name='productos_utilizados')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad_utilizada = models.DecimalField(max_digits=8, decimal_places=3)
    costo_unitario = models.DecimalField(max_digits=8, decimal_places=2)
    
    @property
    def costo_total(self):
        return self.cantidad_utilizada * self.costo_unitario
    
    def __str__(self):
        return f"{self.producto.nombre} - {self.cantidad_utilizada}"
    
    class Meta:
        verbose_name_plural = "Productos utilizados en Carwash"

class CalificacionCarwash(models.Model):
    cita_carwash = models.OneToOneField(CitaCarwash, on_delete=models.CASCADE, related_name='calificacion')
    puntuacion = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # 1-5 estrellas
    comentarios = models.TextField(blank=True, null=True)
    fecha_calificacion = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Calificación {self.puntuacion}/5 - Cita #{self.cita_carwash.cita.id}"
    
    class Meta:
        verbose_name_plural = "Calificaciones de Carwash"