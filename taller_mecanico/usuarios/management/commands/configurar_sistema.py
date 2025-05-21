# usuarios/management/commands/configurar_sistema.py
from django.core.management.base import BaseCommand
from usuarios.models import Rol, Perfil
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Configura roles iniciales y usuario administrador'

    def handle(self, *args, **options):
        self.stdout.write('Configurando roles iniciales...')
        
        # Crear roles básicos
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
        
        # Verificar si existe usuario admin
        if not User.objects.filter(username='admin').exists():
            self.stdout.write('Creando usuario administrador...')
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin12345'
            )
            
            # Asignar rol de administrador
            admin_role = Rol.objects.get(nombre='Administrador')
            perfil, _ = Perfil.objects.get_or_create(usuario=admin_user)
            perfil.rol = admin_role
            perfil.save()
            
            self.stdout.write(self.style.SUCCESS('Usuario administrador creado con éxito.'))
            self.stdout.write('Usuario: admin')
            self.stdout.write('Contraseña: admin')
        else:
            # Verificar que el usuario admin tenga rol de Administrador
            admin_user = User.objects.get(username='admin')
            admin_role = Rol.objects.get(nombre='Administrador')
            
            perfil, _ = Perfil.objects.get_or_create(usuario=admin_user)
            if not perfil.rol or perfil.rol.nombre != 'Administrador':
                perfil.rol = admin_role
                perfil.save()
                self.stdout.write(self.style.SUCCESS('Rol de Administrador asignado al usuario admin.'))
            
            self.stdout.write('El usuario administrador ya existe.')
        
        self.stdout.write(self.style.SUCCESS('Configuración completada.'))