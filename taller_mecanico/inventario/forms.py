# inventario/forms.py
from django import forms
from .models import (
    Proveedor, Producto, CategoriaProducto, MovimientoInventario, 
    OrdenCompra, DetalleOrdenCompra, ProductoServicio
)
from citas.models import TipoServicio

class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ['nombre', 'contacto', 'telefono', 'email', 'direccion', 'activo']
        widgets = {
            'direccion': forms.Textarea(attrs={'rows': 3}),
        }

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = CategoriaProducto
        fields = ['nombre', 'descripcion']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
        }

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = [
            'codigo', 'nombre', 'descripcion', 'tipo', 'categoria', 
            'proveedor_principal', 'precio_compra', 'precio_venta',
            'stock_minimo', 'unidad_medida', 'activo'
        ]
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
            'precio_compra': forms.NumberInput(attrs={'step': '0.01'}),
            'precio_venta': forms.NumberInput(attrs={'step': '0.01'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['proveedor_principal'].queryset = Proveedor.objects.filter(activo=True)

class MovimientoInventarioForm(forms.ModelForm):
    class Meta:
        model = MovimientoInventario
        fields = ['producto', 'tipo', 'motivo', 'cantidad', 'precio_unitario', 'observaciones']
        widgets = {
            'observaciones': forms.Textarea(attrs={'rows': 3}),
            'precio_unitario': forms.NumberInput(attrs={'step': '0.01'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['producto'].queryset = Producto.objects.filter(activo=True)

class BusquedaProductoForm(forms.Form):
    busqueda = forms.CharField(
        max_length=100, 
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Buscar por código, nombre o descripción...',
            'class': 'form-control'
        })
    )
    
    # Corregir esta línea - convertir tupla a lista
    tipo = forms.ChoiceField(
        choices=[('', 'Todos')] + list(Producto.TIPOS),  # Convertir tupla a lista
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    categoria = forms.ModelChoiceField(
        queryset=CategoriaProducto.objects.all(),
        required=False,
        empty_label="Todas las categorías",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    solo_stock_bajo = forms.BooleanField(
        required=False,
        label="Solo productos con stock bajo"
    )

class OrdenCompraForm(forms.ModelForm):
    class Meta:
        model = OrdenCompra
        fields = ['proveedor', 'fecha_entrega_estimada', 'observaciones']
        widgets = {
            'fecha_entrega_estimada': forms.DateInput(attrs={'type': 'date'}),
            'observaciones': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['proveedor'].queryset = Proveedor.objects.filter(activo=True)

class DetalleOrdenCompraForm(forms.ModelForm):
    class Meta:
        model = DetalleOrdenCompra
        fields = ['producto', 'cantidad', 'precio_unitario']
        widgets = {
            'precio_unitario': forms.NumberInput(attrs={'step': '0.01'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['producto'].queryset = Producto.objects.filter(activo=True)

class ProductoServicioForm(forms.ModelForm):
    class Meta:
        model = ProductoServicio
        fields = ['servicio', 'producto', 'cantidad_estimada', 'obligatorio']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['producto'].queryset = Producto.objects.filter(activo=True)

class AjusteInventarioForm(forms.Form):
    producto = forms.ModelChoiceField(
        queryset=Producto.objects.filter(activo=True),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    stock_nuevo = forms.IntegerField(
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    motivo = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Motivo del ajuste...',
            'class': 'form-control'
        })
    )