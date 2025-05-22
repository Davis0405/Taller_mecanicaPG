# usuarios/signals.py
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Perfil, Rol

@receiver(post_save, sender=User)
def create_or_update_profile(sender, instance, created, **kwargs):
    """
    Crear o actualizar perfil de usuario
    """
    if created:
        # Solo crear perfil si el usuario es nuevo y no tiene perfil
        try:
            perfil = Perfil.objects.get(usuario=instance)
        except Perfil.DoesNotExist:
            # Buscar o crear el rol de Cliente por defecto
            rol_cliente, _ = Rol.objects.get_or_create(
                nombre='Cliente',
                defaults={'descripcion': 'Usuario que solicita servicios'}
            )
            
            # Crear perfil
            perfil = Perfil.objects.create(usuario=instance)
            
            # Si es superusuario, asignar rol de Administrador
            if instance.is_superuser:
                rol_admin, _ = Rol.objects.get_or_create(
                    nombre='Administrador',
                    defaults={'descripcion': 'Control total del sistema'}
                )
                perfil.rol = rol_admin
            else:
                perfil.rol = rol_cliente
            
            perfil.save()