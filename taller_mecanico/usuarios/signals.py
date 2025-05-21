# usuarios/signals.py
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Perfil, Rol

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        # Buscar o crear el rol de Administrador
        admin_role, _ = Rol.objects.get_or_create(
            nombre='Administrador', 
            defaults={'descripcion': 'Control total del sistema'}
        )
        
        # Crear perfil y asignar rol de Administrador si es superusuario
        perfil = Perfil.objects.create(usuario=instance)
        if instance.is_superuser:
            perfil.rol = admin_role
            perfil.save()

@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    try:
        # Si el usuario es superusuario, asegúrate de que tenga rol Administrador
        if instance.is_superuser:
            admin_role, _ = Rol.objects.get_or_create(
                nombre='Administrador',
                defaults={'descripcion': 'Control total del sistema'}
            )
            
            if not hasattr(instance, 'perfil'):
                perfil = Perfil.objects.create(usuario=instance)
            else:
                perfil = instance.perfil
                
            if not perfil.rol or perfil.rol.nombre != 'Administrador':
                perfil.rol = admin_role
                perfil.save()
        else:
            # Solo guardar el perfil para usuarios no superusuarios
            if hasattr(instance, 'perfil'):
                instance.perfil.save()
    except Exception as e:
        print(f"Error en señal save_profile: {e}")