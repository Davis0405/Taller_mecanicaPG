# citas/management/commands/crear_servicios_iniciales.py
from django.core.management.base import BaseCommand
from citas.models import TipoServicio

class Command(BaseCommand):
    help = 'Crea los servicios iniciales del sistema'

    def handle(self, *args, **options):
        servicios = [
            # Servicios Mecánicos
            {
                'nombre': 'Cambio de Aceite',
                'descripcion': 'Cambio de aceite y filtro para mantener el motor en buen estado',
                'duracion': 30,
                'precio': 35.00,
                'categoria': 'MECANICO'
            },
            {
                'nombre': 'Revisión de Frenos',
                'descripcion': 'Inspección y ajuste del sistema de frenos',
                'duracion': 60,
                'precio': 50.00,
                'categoria': 'MECANICO'
            },
            {
                'nombre': 'Cambio de Pastillas de Freno',
                'descripcion': 'Sustitución de pastillas de freno desgastadas',
                'duracion': 90,
                'precio': 85.00,
                'categoria': 'MECANICO'
            },
            {
                'nombre': 'Alineación y Balanceo',
                'descripcion': 'Alineación de dirección y balanceo de ruedas',
                'duracion': 60,
                'precio': 65.00,
                'categoria': 'MECANICO'
            },
            {
                'nombre': 'Mantenimiento General',
                'descripcion': 'Revisión completa del vehículo según kilometraje',
                'duracion': 180,
                'precio': 150.00,
                'categoria': 'MECANICO'
            },
            
            # Servicios de Carwash
            {
                'nombre': 'Lavado Básico',
                'descripcion': 'Lavado exterior con champú y secado',
                'duracion': 30,
                'precio': 15.00,
                'categoria': 'CARWASH'
            },
            {
                'nombre': 'Lavado Completo',
                'descripcion': 'Lavado exterior, limpieza de llantas y aspirado interior',
                'duracion': 60,
                'precio': 25.00,
                'categoria': 'CARWASH'
            },
            {
                'nombre': 'Lavado Premium',
                'descripcion': 'Lavado completo con encerado y protección UV',
                'duracion': 90,
                'precio': 40.00,
                'categoria': 'CARWASH'
            },
            {
                'nombre': 'Detallado Interior',
                'descripcion': 'Limpieza profunda de interior, tapicería y plásticos',
                'duracion': 120,
                'precio': 55.00,
                'categoria': 'CARWASH'
            },
            {
                'nombre': 'Pulido y Encerado',
                'descripcion': 'Pulido de carrocería y encerado protector',
                'duracion': 120,
                'precio': 65.00,
                'categoria': 'CARWASH'
            },
        ]
        
        for servicio_data in servicios:
            servicio, created = TipoServicio.objects.get_or_create(
                nombre=servicio_data['nombre'],
                defaults={
                    'descripcion': servicio_data['descripcion'],
                    'duracion': servicio_data['duracion'],
                    'precio': servicio_data['precio'],
                    'categoria': servicio_data['categoria']
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Servicio "{servicio.nombre}" creado exitosamente'))
            else:
                self.stdout.write(f'El servicio "{servicio.nombre}" ya existía')