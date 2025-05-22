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
    # Generar opciones de hora por defecto (8:00 AM a 5:00 PM cada 30 min)
    def generar_opciones_hora():
        opciones = []
        hora_actual = datetime.time(8, 0)  # 8:00 AM
        hora_fin = datetime.time(17, 0)    # 5:00 PM
        
        while hora_actual < hora_fin:
            opciones.append((hora_actual.strftime('%H:%M'), hora_actual.strftime('%H:%M')))
            # Agregar 30 minutos
            hora_dt = datetime.datetime.combine(datetime.date.today(), hora_actual)
            hora_dt = hora_dt + datetime.timedelta(minutes=30)
            hora_actual = hora_dt.time()
        
        return opciones
    
    vehiculo = forms.ModelChoiceField(queryset=None)
    servicio = forms.ModelChoiceField(queryset=None)
    hora_inicio = forms.ChoiceField(choices=generar_opciones_hora())
    
    class Meta:
        model = Cita
        fields = ['vehiculo', 'servicio', 'fecha', 'hora_inicio', 'notas']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date', 'min': datetime.date.today().isoformat()}),
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
    
    def clean_hora_inicio(self):
        hora_str = self.cleaned_data['hora_inicio']
        try:
            return datetime.datetime.strptime(hora_str, '%H:%M').time()
        except ValueError:
            raise ValidationError("Formato de hora inválido")

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
        from django.contrib.auth.models import User
        
        try:
            mecanicos = Perfil.objects.filter(rol__nombre__in=['Mecánico', 'Administrador']).values_list('usuario', flat=True)
            self.fields['atendida_por'].queryset = User.objects.filter(id__in=mecanicos)
        except:
            self.fields['atendida_por'].queryset = User.objects.filter(is_staff=True)