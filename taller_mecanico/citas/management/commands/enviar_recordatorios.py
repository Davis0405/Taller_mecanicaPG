# citas/management/commands/enviar_recordatorios.py
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from citas.models import Cita, Notificacion
import datetime

class Command(BaseCommand):
    help = 'Envía recordatorios por email para las citas próximas'

    def handle(self, *args, **options):
        # Obtener la fecha de mañana
        manana = datetime.date.today() + datetime.timedelta(days=1)
        
        # Buscar citas para mañana que estén confirmadas o pendientes
        citas_manana = Cita.objects.filter(
            fecha=manana,
            estado__in=['PENDIENTE', 'CONFIRMADA']
        )
        
        self.stdout.write(f'Encontradas {citas_manana.count()} citas para mañana ({manana})')
        
        # Enviar recordatorios
        for cita in citas_manana:
            # Verificar si ya se envió un recordatorio para esta cita
            recordatorio_existente = Notificacion.objects.filter(
                cita=cita,
                tipo='RECORDATORIO'
            ).exists()
            
            if not recordatorio_existente:
                # Crear el mensaje de recordatorio
                mensaje = f"""
                Hola {cita.cliente.first_name or cita.cliente.username},
                
                Te recordamos que tienes una cita programada para mañana:
                
                Servicio: {cita.servicio.nombre}
                Fecha: {cita.fecha}
                Hora: {cita.hora_inicio}
                Vehículo: {cita.vehiculo.marca} {cita.vehiculo.modelo} ({cita.vehiculo.placa})
                
                ¡Te esperamos!
                
                Atentamente,
                Equipo de Taller Mecánico
                """
                
                try:
                    # Enviar el email
                    send_mail(
                        f'Recordatorio de Cita - {cita.servicio.nombre}',
                        mensaje,
                        settings.EMAIL_HOST_USER,
                        [cita.cliente.email],
                        fail_silently=False,
                    )
                    
                    # Registrar la notificación
                    Notificacion.objects.create(
                        cita=cita,
                        tipo='RECORDATORIO',
                        mensaje=mensaje,
                        enviado=True
                    )
                    
                    self.stdout.write(self.style.SUCCESS(
                        f'Recordatorio enviado para la cita #{cita.id} ({cita.cliente.email})')
                    )
                except Exception as e:
                    self.stdout.write(self.style.ERROR(
                        f'Error al enviar recordatorio para la cita #{cita.id}: {e}')
                    )
            else:
                self.stdout.write(f'Ya se envió un recordatorio para la cita #{cita.id}')