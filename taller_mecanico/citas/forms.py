# citas/forms.py
from django import forms
from .models import Vehiculo, Cita, TipoServicio
from django.core.exceptions import ValidationError
import datetime

class VehiculoForm(forms.ModelForm):
    class Meta:
        model = Vehiculo
        fields = ['marca', 'modelo', 'año', 'placa', 'color']
        widgets = {
            'año': forms.NumberInput(attrs={'min': 1900, 'max': datetime.date.today().year + 1}),
        }

class FechaHoraDisponibleForm(forms.Form):
    """Formulario para seleccionar fecha y ver horas disponibles"""
    fecha = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'min': datetime.date.today().isoformat()}),
        initial=datetime.date.today
    )
    categoria_servicio = forms.ChoiceField(
        choices=TipoServicio.CATEGORIAS,
        required=True,
        label="Tipo de Servicio"
    )

class CitaForm(forms.ModelForm):
    vehiculo = forms.ModelChoiceField(queryset=None)
    servicio = forms.ModelChoiceField(queryset=None)
    
    class Meta:
        model = Cita
        fields = ['vehiculo', 'servicio', 'fecha', 'hora_inicio', 'notas']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date', 'min': datetime.date.today().isoformat()}),
            'hora_inicio': forms.Select(),
            'notas': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        categoria = kwargs.pop('categoria', None)
        super(CitaForm, self).__init__(*args, **kwargs)
        
        # Filtrar vehículos del usuario actual
        if user:
            self.fields['vehiculo'].queryset = Vehiculo.objects.filter(propietario=user)
        
        # Filtrar servicios por categoría
        if categoria:
            self.fields['servicio'].queryset = TipoServicio.objects.filter(categoria=categoria)
        else:
            self.fields['servicio'].queryset = TipoServicio.objects.all()
        
        # Campo de hora_inicio solo muestra las horas disponibles
        self.fields['hora_inicio'].widget = forms.Select(choices=[])

class GestionCitaForm(forms.ModelForm):
    class Meta:
        model = Cita
        fields = ['estado', 'atendida_por', 'notas']
        widgets = {
            'notas': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super(GestionCitaForm, self).__init__(*args, **kwargs)
        # Solo permitimos usuarios con rol "Mecánico" para atender citas de servicios mecánicos
        from usuarios.models import Perfil, Rol
        mecanicos = Perfil.objects.filter(rol__nombre='Mecánico').values_list('usuario', flat=True)
        self.fields['atendida_por'].queryset = User.objects.filter(id__in=mecanicos)