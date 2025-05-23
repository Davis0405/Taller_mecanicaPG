# inventario/models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from decimal import Decimal

class Proveedor(models.Model):
    nombre = models.CharField(max_length=100)
    contacto = models.CharField(max_length=100, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name_plural = "Proveedores"

class CategoriaProducto(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name_plural = "Categorías de Productos"

class Producto(models.Model):
    TIPOS = (
        ('REPUESTO', 'Repuesto'),
        ('HERRAMIENTA', 'Herramienta'),
        ('CONSUMIBLE', 'Consumible'),
    )
    
    codigo = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    tipo = models.CharField(max_length=15, choices=TIPOS)
    categoria = models.ForeignKey(CategoriaProducto, on_delete=models.SET_NULL, null=True, blank=True)
    proveedor_principal = models.ForeignKey(Proveedor, on_delete=models.SET_NULL, null=True, blank=True)
    precio_compra = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock_minimo = models.PositiveIntegerField(default=5)
    stock_actual = models.PositiveIntegerField(default=0)
    unidad_medida = models.CharField(max_length=20, default='Unidad')
    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"
    
    @property
    def necesita_reposicion(self):
        return self.stock_actual <= self.stock_minimo
    
    @property
    def valor_inventario(self):
        return self.stock_actual * self.precio_compra
    
    def clean(self):
        if self.precio_venta < self.precio_compra:
            raise ValidationError("El precio de venta no puede ser menor al precio de compra.")
    
    class Meta:
        ordering = ['nombre']

class MovimientoInventario(models.Model):
    TIPOS_MOVIMIENTO = (
        ('ENTRADA', 'Entrada'),
        ('SALIDA', 'Salida'),
        ('AJUSTE', 'Ajuste'),
    )
    
    MOTIVOS = (
        ('COMPRA', 'Compra'),
        ('DEVOLUCION', 'Devolución'),
        ('SERVICIO', 'Uso en Servicio'),
        ('PERDIDA', 'Pérdida'),
        ('DAÑADO', 'Producto Dañado'),
        ('AJUSTE_INVENTARIO', 'Ajuste de Inventario'),
        ('OTROS', 'Otros'),
    )
    
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='movimientos')
    tipo = models.CharField(max_length=10, choices=TIPOS_MOVIMIENTO)
    motivo = models.CharField(max_length=20, choices=MOTIVOS)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock_anterior = models.PositiveIntegerField()
    stock_nuevo = models.PositiveIntegerField()
    observaciones = models.TextField(blank=True, null=True)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    fecha = models.DateTimeField(auto_now_add=True)
    
    # Relación opcional con cita para rastrear el uso de productos en servicios
    cita = models.ForeignKey('citas.Cita', on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.producto.nombre} - {self.cantidad}"
    
    @property
    def valor_total(self):
        return self.cantidad * self.precio_unitario
    
    class Meta:
        ordering = ['-fecha']

class ProductoServicio(models.Model):
    """Relación entre productos y servicios - qué productos se usan típicamente en cada servicio"""
    servicio = models.ForeignKey('citas.TipoServicio', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad_estimada = models.PositiveIntegerField(default=1)
    obligatorio = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.servicio.nombre} - {self.producto.nombre}"
    
    class Meta:
        unique_together = ['servicio', 'producto']
        verbose_name_plural = "Productos por Servicio"

class OrdenCompra(models.Model):
    ESTADOS = (
        ('BORRADOR', 'Borrador'),
        ('ENVIADA', 'Enviada'),
        ('RECIBIDA', 'Recibida'),
        ('CANCELADA', 'Cancelada'),
    )
    
    numero = models.CharField(max_length=20, unique=True)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_entrega_estimada = models.DateField(null=True, blank=True)
    estado = models.CharField(max_length=10, choices=ESTADOS, default='BORRADOR')
    observaciones = models.TextField(blank=True, null=True)
    creada_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    def __str__(self):
        return f"OC-{self.numero} - {self.proveedor.nombre}"
    
    def calcular_total(self):
        total = sum([detalle.subtotal for detalle in self.detalles.all()])
        self.total = total
        self.save()
        return total
    
    class Meta:
        ordering = ['-fecha_creacion']

class DetalleOrdenCompra(models.Model):
    orden = models.ForeignKey(OrdenCompra, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    
    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario
    
    def __str__(self):
        return f"{self.orden.numero} - {self.producto.nombre}"
    
    class Meta:
        unique_together = ['orden', 'producto']

class AlertaInventario(models.Model):
    TIPOS = (
        ('STOCK_BAJO', 'Stock Bajo'),
        ('STOCK_AGOTADO', 'Stock Agotado'),
        ('PRODUCTO_VENCIDO', 'Producto Vencido'),
    )
    
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=20, choices=TIPOS)
    mensaje = models.TextField()
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_resolucion = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.producto.nombre}"
    
    class Meta:
        ordering = ['-fecha_creacion']