# carwash/forms.py
from django import forms
from .models import PaqueteCarwash, TipoVehiculo, CitaCarwash, CalificacionCarwash, ProductoCarwash
from citas.models import Cita, TipoServicio
from django.contrib.auth.models import User
from usuarios.models import Perfil

class PaqueteCarwashForm(forms.ModelForm):
    class Meta:
        model = PaqueteCarwash
        fields = [
            'nombre', 'tipo', 'descripcion', 'precio_base', 'duracion_estimada', 
            'incluye_lavado_exterior', 'incluye_lavado_interior', 'incluye_aspirado',
            'incluye_encerado', 'incluye_llantas', 'incluye_motor', 
            'incluye_proteccion_uv', 'incluye_aromatizacion', 'activo'
        ]
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 4}),
            'precio_base': forms.NumberInput(attrs={'step': '0.01'}),
        }

class TipoVehiculoForm(forms.ModelForm):
    class Meta:
        model = TipoVehiculo
        fields = ['nombre', 'factor_precio', 'descripcion']
        widgets = {
            'factor_precio': forms.NumberInput(attrs={'step': '0.01'}),
            'descripcion': forms.Textarea(attrs={'rows': 3}),
        }

class CitaCarwashForm(forms.ModelForm):
    class Meta:
        model = CitaCarwash
        fields = ['paquete', 'tipo_vehiculo', 'servicios_adicionales', 'observaciones']
        widgets = {
            'servicios_adicionales': forms.Textarea(attrs={'rows': 3}),
            'observaciones': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['paquete'].queryset = PaqueteCarwash.objects.filter(activo=True)

class GestionCarwashForm(forms.ModelForm):
    class Meta:
        model = CitaCarwash
        fields = ['estado_proceso', 'lavador_asignado', 'servicios_adicionales', 'observaciones']
        widgets = {
            'servicios_adicionales': forms.Textarea(attrs={'rows': 2}),
            'observaciones': forms.Textarea(attrs={'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar solo usuarios que pueden ser lavadores
        try:
            lavadores = Perfil.objects.filter(
                rol__nombre__in=['Mecánico', 'Administrador']
            ).values_list('usuario', flat=True)
            self.fields['lavador_asignado'].queryset = User.objects.filter(id__in=lavadores)
        except:
            self.fields['lavador_asignado'].queryset = User.objects.filter(is_staff=True)

class CalificacionCarwashForm(forms.ModelForm):
    class Meta:
        model = CalificacionCarwash
        fields = ['puntuacion', 'comentarios']
        widgets = {
            'comentarios': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Comparte tu experiencia con nuestro servicio de carwash...'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Widget personalizado para puntuación con estrellas
        self.fields['puntuacion'].widget = forms.RadioSelect(choices=[
            (5, '⭐⭐⭐⭐⭐ Excelente'),
            (4, '⭐⭐⭐⭐ Muy Bueno'),
            (3, '⭐⭐⭐ Bueno'),
            (2, '⭐⭐ Regular'),
            (1, '⭐ Necesita Mejorar'),
        ])

class BusquedaCarwashForm(forms.Form):
    fecha_desde = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    fecha_hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    estado_proceso = forms.ChoiceField(
        choices=[('', 'Todos')] + list(CitaCarwash.ESTADOS_PROCESO),
        required=False
    )
    paquete = forms.ModelChoiceField(
        queryset=PaqueteCarwash.objects.filter(activo=True),
        required=False,
        empty_label="Todos los paquetes"
    )

class ProductoCarwashForm(forms.ModelForm):
    class Meta:
        model = ProductoCarwash
        fields = ['producto', 'cantidad_utilizada', 'costo_unitario']
        widgets = {
            'cantidad_utilizada': forms.NumberInput(attrs={'step': '0.001'}),
            'costo_unitario': forms.NumberInput(attrs={'step': '0.01'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar solo productos de carwash
        from inventario.models import Producto
        self.fields['producto'].queryset = Producto.objects.filter(
            activo=True,
            categoria__nombre__icontains='limpieza'
        ) | Producto.objects.filter(
            activo=True,
            tipo='CONSUMIBLE'
        )