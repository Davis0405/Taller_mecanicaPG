# inventario/management/commands/generar_alertas_inventario.py
from django.core.management.base import BaseCommand
from inventario.models import Producto, AlertaInventario
from django.db.models import F

class Command(BaseCommand):
    help = 'Genera alertas automáticas para productos con stock bajo'

    def handle(self, *args, **options):
        # Limpiar alertas antiguas resueltas
        AlertaInventario.objects.filter(activa=False).delete()
        
        # Productos con stock bajo o agotado
        productos_stock_bajo = Producto.objects.filter(
            activo=True,
            stock_actual__lte=F('stock_minimo')
        )
        
        alertas_creadas = 0
        
        for producto in productos_stock_bajo:
            tipo_alerta = 'STOCK_AGOTADO' if producto.stock_actual == 0 else 'STOCK_BAJO'
            mensaje = f'El producto {producto.nombre} (código: {producto.codigo}) tiene stock {"agotado" if producto.stock_actual == 0 else "bajo"}: {producto.stock_actual} unidades'
            
            # Crear o actualizar alerta
            alerta, created = AlertaInventario.objects.get_or_create(
                producto=producto,
                tipo=tipo_alerta,
                activa=True,
                defaults={'mensaje': mensaje}
            )
            
            if created:
                alertas_creadas += 1
                self.stdout.write(self.style.WARNING(f'Alerta creada: {mensaje}'))
            else:
                # Actualizar mensaje si ya existe
                alerta.mensaje = mensaje
                alerta.save()
        
        # Desactivar alertas para productos que ya no tienen stock bajo
        productos_con_stock_ok = Producto.objects.filter(
            activo=True,
            stock_actual__gt=F('stock_minimo')
        )
        
        alertas_resueltas = AlertaInventario.objects.filter(
            producto__in=productos_con_stock_ok,
            activa=True
        ).update(activa=False)
        
        self.stdout.write(self.style.SUCCESS(f'Proceso completado: {alertas_creadas} alertas nuevas, {alertas_resueltas} alertas resueltas'))