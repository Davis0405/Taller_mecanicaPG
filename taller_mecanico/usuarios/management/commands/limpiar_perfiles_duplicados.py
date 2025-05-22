# usuarios/management/commands/limpiar_perfiles_duplicados.py
from django.core.management.base import BaseCommand
from usuarios.models import Perfil, Rol
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Limpia perfiles duplicados y corrige inconsistencias'

    def handle(self, *args, **options):
        self.stdout.write('Limpiando perfiles duplicados...')
        
        # Encontrar usuarios sin perfil
        usuarios_sin_perfil = []
        for user in User.objects.all():
            try:
                user.perfil
            except Perfil.DoesNotExist:
                usuarios_sin_perfil.append(user)
        
        self.stdout.write(f'Usuarios sin perfil: {len(usuarios_sin_perfil)}')
        
        # Crear perfiles faltantes
        rol_cliente, _ = Rol.objects.get_or_create(
            nombre='Cliente',
            defaults={'descripcion': 'Usuario que solicita servicios'}
        )
        
        rol_admin, _ = Rol.objects.get_or_create(
            nombre='Administrador',
            defaults={'descripcion': 'Control total del sistema'}
        )
        
        for user in usuarios_sin_perfil:
            rol = rol_admin if user.is_superuser else rol_cliente
            perfil = Perfil.objects.create(usuario=user, rol=rol)
            self.stdout.write(f'Perfil creado para usuario: {user.username}')
        
        # Verificar perfiles duplicados
        usuarios_con_multiples_perfiles = []
        for user in User.objects.all():
            perfiles_count = Perfil.objects.filter(usuario=user).count()
            if perfiles_count > 1:
                usuarios_con_multiples_perfiles.append(user)
        
        self.stdout.write(f'Usuarios con múltiples perfiles: {len(usuarios_con_multiples_perfiles)}')
        
        # Limpiar perfiles duplicados
        for user in usuarios_con_multiples_perfiles:
            perfiles = Perfil.objects.filter(usuario=user).order_by('id')
            perfil_principal = perfiles.first()
            
            # Eliminar perfiles duplicados
            for perfil in perfiles[1:]:
                perfil.delete()
                self.stdout.write(f'Perfil duplicado eliminado para usuario: {user.username}')
        
        self.stdout.write(self.style.SUCCESS('Limpieza completada.'))