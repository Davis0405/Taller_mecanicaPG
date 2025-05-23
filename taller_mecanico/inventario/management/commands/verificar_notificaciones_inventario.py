# inventario/management/commands/verificar_notificaciones_inventario.py
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from inventario.models import Producto, AlertaInventario
from inventario.utils import obtener_usuarios_notificacion
from django.db.models import F

class Command(BaseCommand):
    help = 'Verifica el sistema completo de notificaciones de inventario'

    def handle(self, *args, **options):
        self.stdout.write('=== VERIFICACIÓN SISTEMA NOTIFICACIONES INVENTARIO ===\n')
        
        # 1. Configuración de email
        self.stdout.write('1. Configuración de Email:')
        self.stdout.write(f'   ✓ Backend: {settings.EMAIL_BACKEND}')
        self.stdout.write(f'   ✓ Host: {settings.EMAIL_HOST}')
        self.stdout.write(f'   ✓ Usuario: {settings.EMAIL_HOST_USER}')
        
        # 2. Usuarios para notificaciones
        usuarios_notif = obtener_usuarios_notificacion()
        self.stdout.write(f'\n2. Usuarios para Notificaciones: {len(usuarios_notif)}')
        for usuario in usuarios_notif:
            self.stdout.write(f'   - {usuario.username} ({usuario.email})')
        
        # 3. Productos con problemas
        productos_problema = Producto.objects.filter(
            activo=True,
            stock_actual__lte=F('stock_minimo')
        )
        self.stdout.write(f'\n3. Productos con Stock Bajo: {productos_problema.count()}')
        for producto in productos_problema[:5]:  # Solo mostrar primeros 5
            self.stdout.write(f'   - {producto.codigo}: {producto.stock_actual}/{producto.stock_minimo}')
        
        # 4. Alertas activas
        alertas_activas = AlertaInventario.objects.filter(activa=True)
        self.stdout.write(f'\n4. Alertas Activas: {alertas_activas.count()}')
        
        # 5. Prueba de email
        self.stdout.write('\n5. Prueba de Email:')
        try:
            send_mail(
                'Verificación Sistema Inventario',
                'Sistema de notificaciones funcionando correctamente.',
                settings.EMAIL_HOST_USER,
                [settings.EMAIL_HOST_USER],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS('   ✓ Email enviado correctamente'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ✗ Error: {e}'))
        
        self.stdout.write('\n=== FIN VERIFICACIÓN ===')