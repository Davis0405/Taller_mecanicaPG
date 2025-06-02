# carwash/management/commands/crear_carwash_inicial.py
from django.core.management.base import BaseCommand
from carwash.models import PaqueteCarwash, TipoVehiculo
from citas.models import TipoServicio

class Command(BaseCommand):
    help = 'Crea paquetes y tipos de vehículo iniciales para carwash'

    def handle(self, *args, **options):
        self.stdout.write('Creando tipos de vehículo...')
        
        # Tipos de vehículo
        tipos_vehiculo = [
            {'nombre': 'Sedán Pequeño', 'factor_precio': 1.0, 'descripcion': 'Autos compactos y sedanes pequeños'},
            {'nombre': 'Sedán Grande', 'factor_precio': 1.2, 'descripcion': 'Sedanes medianos y grandes'},
            {'nombre': 'SUV/Crossover', 'factor_precio': 1.4, 'descripcion': 'SUVs y crossovers'},
            {'nombre': 'Pickup', 'factor_precio': 1.5, 'descripcion': 'Camionetas pickup'},
            {'nombre': 'Van/Minivan', 'factor_precio': 1.6, 'descripcion': 'Vans y minivans'},
            {'nombre': 'Motocicleta', 'factor_precio': 0.6, 'descripcion': 'Motocicletas y scooters'},
        ]
        
        for tipo_data in tipos_vehiculo:
            tipo, created = TipoVehiculo.objects.get_or_create(
                nombre=tipo_data['nombre'],
                defaults={
                    'factor_precio': tipo_data['factor_precio'],
                    'descripcion': tipo_data['descripcion']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Tipo de vehículo "{tipo.nombre}" creado'))
            else:
                self.stdout.write(f'Tipo de vehículo "{tipo.nombre}" ya existía')
        
        self.stdout.write('Creando paquetes de carwash...')
        
        # Paquetes de carwash
        paquetes = [
            {
                'nombre': 'Lavado Básico',
                'tipo': 'BASICO',
                'descripcion': 'Lavado exterior con champú y secado',
                'precio_base': 15.00,
                'duracion_estimada': 30,
                'incluye_lavado_exterior': True,
                'incluye_lavado_interior': False,
                'incluye_aspirado': False,
                'incluye_encerado': False,
                'incluye_llantas': False,
                'incluye_motor': False,
                'incluye_proteccion_uv': False,
                'incluye_aromatizacion': False,
            },
            {
                'nombre': 'Lavado Completo',
                'tipo': 'COMPLETO',
                'descripcion': 'Lavado exterior, interior básico y aspirado',
                'precio_base': 25.00,
                'duracion_estimada': 45,
                'incluye_lavado_exterior': True,
                'incluye_lavado_interior': True,
                'incluye_aspirado': True,
                'incluye_encerado': False,
                'incluye_llantas': True,
                'incluye_motor': False,
                'incluye_proteccion_uv': False,
                'incluye_aromatizacion': False,
            },
            {
                'nombre': 'Lavado Premium',
                'tipo': 'PREMIUM',
                'descripcion': 'Lavado completo con encerado y protección',
                'precio_base': 40.00,
                'duracion_estimada': 60,
                'incluye_lavado_exterior': True,
                'incluye_lavado_interior': True,
                'incluye_aspirado': True,
                'incluye_encerado': True,
                'incluye_llantas': True,
                'incluye_motor': False,
                'incluye_proteccion_uv': True,
                'incluye_aromatizacion': True,
            },
            {
                'nombre': 'Detallado Completo',
                'tipo': 'DETALLADO',
                'descripcion': 'Servicio completo de detallado profesional',
                'precio_base': 65.00,
                'duracion_estimada': 90,
                'incluye_lavado_exterior': True,
                'incluye_lavado_interior': True,
                'incluye_aspirado': True,
                'incluye_encerado': True,
                'incluye_llantas': True,
                'incluye_motor': True,
                'incluye_proteccion_uv': True,
                'incluye_aromatizacion': True,
            },
            {
                'nombre': 'Lavado Express',
                'tipo': 'BASICO',
                'descripcion': 'Lavado rápido solo exterior',
                'precio_base': 10.00,
                'duracion_estimada': 20,
                'incluye_lavado_exterior': True,
                'incluye_lavado_interior': False,
                'incluye_aspirado': False,
                'incluye_encerado': False,
                'incluye_llantas': False,
                'incluye_motor': False,
                'incluye_proteccion_uv': False,
                'incluye_aromatizacion': False,
            },
        ]
        
        for paquete_data in paquetes:
            paquete, created = PaqueteCarwash.objects.get_or_create(
                nombre=paquete_data['nombre'],
                defaults=paquete_data
            )
            
            if created:
                # Crear TipoServicio correspondiente
                TipoServicio.objects.get_or_create(
                    nombre=paquete.nombre,
                    categoria='CARWASH',
                    defaults={
                        'descripcion': paquete.descripcion,
                        'duracion': paquete.duracion_estimada,
                        'precio': paquete.precio_base
                    }
                )
                self.stdout.write(self.style.SUCCESS(f'Paquete "{paquete.nombre}" creado'))
            else:
                self.stdout.write(f'Paquete "{paquete.nombre}" ya existía')
        
        self.stdout.write(self.style.SUCCESS('Datos iniciales de carwash creados exitosamente.'))