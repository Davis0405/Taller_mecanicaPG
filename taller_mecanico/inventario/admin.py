# inventario/admin.py
from django.contrib import admin
from .models import (
    Proveedor, CategoriaProducto, Producto, MovimientoInventario,
    OrdenCompra, DetalleOrdenCompra, AlertaInventario, ProductoServicio
)

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'contacto', 'telefono', 'email', 'activo', 'fecha_registro')
    list_filter = ('activo', 'fecha_registro')
    search_fields = ('nombre', 'contacto', 'email')

@admin.register(CategoriaProducto)
class CategoriaProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')
    search_fields = ('nombre',)

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'tipo', 'categoria', 'stock_actual', 'stock_minimo', 'precio_venta', 'activo')
    list_filter = ('tipo', 'categoria', 'activo', 'proveedor_principal')
    search_fields = ('codigo', 'nombre', 'descripcion')
    list_editable = ('stock_actual', 'precio_venta')

@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'producto', 'tipo', 'motivo', 'cantidad', 'stock_anterior', 'stock_nuevo', 'usuario')
    list_filter = ('tipo', 'motivo', 'fecha')
    search_fields = ('producto__nombre', 'producto__codigo')
    date_hierarchy = 'fecha'

@admin.register(AlertaInventario)
class AlertaInventarioAdmin(admin.ModelAdmin):
    list_display = ('producto', 'tipo', 'activa', 'fecha_creacion')
    list_filter = ('tipo', 'activa', 'fecha_creacion')
    search_fields = ('producto__nombre',)