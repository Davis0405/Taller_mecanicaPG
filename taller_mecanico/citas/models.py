# citas/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
import datetime

class TipoServicio(models.Model):
    CATEGORIAS = (
        ('MECANICO', 'Servicio Mecánico'),
        ('CARWASH', 'Servicio de Lavado'),
    )
    
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    duracion = models.IntegerField(help_text="Duración en minutos")
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    categoria = models.CharField(max_length=10, choices=CATEGORIAS)
    
    def __str__(self):
        return f"{self.nombre} ({self.get_categoria_display()})"

class Vehiculo(models.Model):
    propietario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vehiculos')
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    año = models.PositiveIntegerField()
    placa = models.CharField(max_length=10, unique=True)
    color = models.CharField(max_length=30)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.marca} {self.modelo} ({self.placa})"

class Cita(models.Model):
    ESTADOS = (
        ('PENDIENTE', 'Pendiente'),
        ('CONFIRMADA', 'Confirmada'),
        ('COMPLETADA', 'Completada'),
        ('CANCELADA', 'Cancelada'),
    )
    
    cliente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='citas')
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE, related_name='citas')
    servicio = models.ForeignKey(TipoServicio, on_delete=models.CASCADE)
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    estado = models.CharField(max_length=10, choices=ESTADOS, default='PENDIENTE')
    notas = models.TextField(blank=True, null=True)
    creada_el = models.DateTimeField(auto_now_add=True)
    actualizada_el = models.DateTimeField(auto_now=True)
    atendida_por = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='citas_atendidas'
    )
    
    def clean(self):
        # Verificar que la fecha no sea en el pasado
        if self.fecha < datetime.date.today():
            raise ValidationError("No se pueden agendar citas en fechas pasadas.")
        
        # Calcular hora_fin basada en la duración del servicio
        if self.hora_inicio and self.servicio:
            inicio_dt = datetime.datetime.combine(datetime.date.today(), self.hora_inicio)
            fin_dt = inicio_dt + datetime.timedelta(minutes=self.servicio.duracion)
            self.hora_fin = fin_dt.time()
        
        # Verificar disponibilidad (no hay otras citas en el mismo horario)
        if self.fecha and self.hora_inicio and self.hora_fin:
            citas_en_conflicto = Cita.objects.filter(
                fecha=self.fecha,
                estado__in=['PENDIENTE', 'CONFIRMADA']
            ).exclude(id=self.id)
            
            for cita in citas_en_conflicto:
                # Verificar si hay solapamiento de horarios
                if (self.hora_inicio < cita.hora_fin and self.hora_fin > cita.hora_inicio):
                    if self.servicio.categoria == cita.servicio.categoria:
                        raise ValidationError(
                            f"Ya existe una cita de {cita.servicio.get_categoria_display()} en ese horario."
                        )
                    # Si son de categorías diferentes, permitir (mecánico y carwash pueden funcionar simultáneamente)
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Cita {self.id} - {self.cliente.username} - {self.fecha} {self.hora_inicio}"

class Notificacion(models.Model):
    TIPOS = (
        ('RECORDATORIO', 'Recordatorio de Cita'),
        ('CONFIRMACION', 'Confirmación de Cita'),
        ('CAMBIO_ESTADO', 'Cambio de Estado'),
    )
    
    cita = models.ForeignKey(Cita, on_delete=models.CASCADE, related_name='notificaciones')
    tipo = models.CharField(max_length=15, choices=TIPOS)
    mensaje = models.TextField()
    fecha_envio = models.DateTimeField(auto_now_add=True)
    enviado = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.get_tipo_display()} - Cita {self.cita.id}"