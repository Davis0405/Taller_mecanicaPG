# usuarios/management/commands/crear_roles_iniciales.py
from django.core.management.base import BaseCommand
from usuarios.models import Rol

class Command(BaseCommand):
    help = 'Crea los roles iniciales del sistema'

    def handle(self, *args, **options):
        roles = [
            {'nombre': 'Administrador', 'descripcion': 'Control total del sistema'},
            {'nombre': 'Mecánico', 'descripcion': 'Gestión de servicios mecánicos'},
            {'nombre': 'Recepcionista', 'descripcion': 'Gestión de citas y clientes'},
            {'nombre': 'Cliente', 'descripcion': 'Usuario que solicita servicios'}
        ]
        
        for rol_data in roles:
            rol, created = Rol.objects.get_or_create(
                nombre=rol_data['nombre'],
                defaults={'descripcion': rol_data['descripcion']}
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Rol "{rol.nombre}" creado exitosamente'))
            else:
                self.stdout.write(f'El rol "{rol.nombre}" ya existía')