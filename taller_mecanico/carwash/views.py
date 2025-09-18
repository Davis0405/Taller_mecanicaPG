# carwash/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from datetime import datetime, date
from citas.models import Cita, TipoServicio, Vehiculo
from citas.forms import CitaForm, FechaHoraDisponibleForm
from usuarios.models import Perfil

def es_staff_carwash(user):
    """Verificar si el usuario puede gestionar carwash"""
    if not user.is_authenticated:
        return False
    try:
        perfil = Perfil.objects.get(usuario=user)
        return perfil.rol and perfil.rol.nombre in ['Administrador', 'Recepcionista']
    except (Perfil.DoesNotExist, AttributeError):
        return user.is_superuser

@login_required
def dashboard_carwash(request):
    """Dashboard específico para carwash"""
    # Estadísticas de carwash
    hoy = date.today()
    
    citas_carwash_hoy = Cita.objects.filter(
        fecha=hoy,
        servicio__categoria='CARWASH'
    )
    
    servicios_carwash = TipoServicio.objects.filter(categoria='CARWASH')
    
    # Citas pendientes y confirmadas hoy
    citas_pendientes = citas_carwash_hoy.filter(estado__in=['PENDIENTE', 'CONFIRMADA']).count()
    citas_completadas = citas_carwash_hoy.filter(estado='COMPLETADA').count()
    
    # Próximas citas de carwash
    proximas_citas = Cita.objects.filter(
        fecha__gte=hoy,
        servicio__categoria='CARWASH',
        estado__in=['PENDIENTE', 'CONFIRMADA']
    ).order_by('fecha', 'hora_inicio')[:10]
    
    context = {
        'citas_pendientes_hoy': citas_pendientes,
        'citas_completadas_hoy': citas_completadas,
        'total_servicios': servicios_carwash.count(),
        'proximas_citas': proximas_citas,
        'servicios_carwash': servicios_carwash,
    }
    return render(request, 'carwash/dashboard.html', context)

@login_required
def calendario_carwash(request):
    """Calendario específico para servicios de carwash"""
    # Filtros
    fecha = request.GET.get('fecha')
    estado = request.GET.get('estado')
    
    citas = Cita.objects.filter(
        servicio__categoria='CARWASH'
    ).order_by('fecha', 'hora_inicio')
    
    if fecha:
        try:
            fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
            citas = citas.filter(fecha=fecha_obj)
        except ValueError:
            messages.error(request, 'Formato de fecha inválido.')
    
    if estado:
        citas = citas.filter(estado=estado)
    
    context = {
        'citas': citas,
        'fecha_filtro': fecha,
        'estado_filtro': estado,
        'estados_cita': Cita.ESTADOS,
    }
    return render(request, 'carwash/calendario.html', context)

@login_required
def nueva_cita_carwash(request):
    """Vista específica para agendar cita de carwash"""
    if request.method == 'POST':
        form = FechaHoraDisponibleForm(request.POST)
        if form.is_valid():
            fecha = form.cleaned_data['fecha']
            # Forzar categoría CARWASH
            return redirect('nueva_cita', fecha=fecha.strftime('%Y-%m-%d'), categoria='CARWASH')
    else:
        # Pre-seleccionar CARWASH
        form = FechaHoraDisponibleForm(initial={'categoria_servicio': 'CARWASH'})
    
    return render(request, 'carwash/nueva_cita.html', {'form': form})

@login_required
def mis_citas_carwash(request):
    """Mis citas específicas de carwash"""
    citas = Cita.objects.filter(
        cliente=request.user,
        servicio__categoria='CARWASH'
    ).order_by('-fecha', 'hora_inicio')
    
    return render(request, 'carwash/mis_citas.html', {'citas': citas})

@login_required
def servicios_carwash(request):
    """Gestión de servicios de carwash"""
    if not es_staff_carwash(request.user):
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('dashboard')
    
    servicios = TipoServicio.objects.filter(categoria='CARWASH').order_by('precio')
    
    # Calcular estadísticas
    estadisticas = {}
    if servicios.exists():
        precios = [servicio.precio for servicio in servicios]
        estadisticas = {
            'total_servicios': servicios.count(),
            'precio_minimo': min(precios),
            'precio_maximo': max(precios),
            'precio_promedio': sum(precios) / len(precios)
        }
    else:
        estadisticas = {
            'total_servicios': 0,
            'precio_minimo': 0,
            'precio_maximo': 0,
            'precio_promedio': 0
        }
    
    return render(request, 'carwash/servicios.html', {
        'servicios': servicios,
        'estadisticas': estadisticas
    })

@login_required
def estadisticas_carwash(request):
    """Estadísticas específicas de carwash"""
    if not es_staff_carwash(request.user):
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('dashboard')
    
    from django.db.models import Count, Sum
    from datetime import timedelta
    
    hoy = date.today()
    inicio_mes = hoy.replace(day=1)
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    
    # Estadísticas por período
    stats = {
        'hoy': {
            'completadas': Cita.objects.filter(
                fecha=hoy, 
                servicio__categoria='CARWASH', 
                estado='COMPLETADA'
            ).count(),
            'ingresos': Cita.objects.filter(
                fecha=hoy, 
                servicio__categoria='CARWASH', 
                estado='COMPLETADA'
            ).aggregate(total=Sum('servicio__precio'))['total'] or 0
        },
        'semana': {
            'completadas': Cita.objects.filter(
                fecha__gte=inicio_semana,
                fecha__lte=hoy,
                servicio__categoria='CARWASH', 
                estado='COMPLETADA'
            ).count(),
            'ingresos': Cita.objects.filter(
                fecha__gte=inicio_semana,
                fecha__lte=hoy,
                servicio__categoria='CARWASH', 
                estado='COMPLETADA'
            ).aggregate(total=Sum('servicio__precio'))['total'] or 0
        },
        'mes': {
            'completadas': Cita.objects.filter(
                fecha__gte=inicio_mes,
                fecha__lte=hoy,
                servicio__categoria='CARWASH', 
                estado='COMPLETADA'
            ).count(),
            'ingresos': Cita.objects.filter(
                fecha__gte=inicio_mes,
                fecha__lte=hoy,
                servicio__categoria='CARWASH', 
                estado='COMPLETADA'
            ).aggregate(total=Sum('servicio__precio'))['total'] or 0
        }
    }
    
    # Servicios más populares
    servicios_populares = TipoServicio.objects.filter(
        categoria='CARWASH'
    ).annotate(
        total_citas=Count('cita', filter=Q(cita__estado='COMPLETADA'))
    ).order_by('-total_citas')[:5]
    
    # Métricas calculadas
    metricas = {
        'ingreso_promedio_servicio': 0,
        'servicios_promedio_dia': 0,
        'tasa_satisfaccion': 85,  # Simulado
        'puntualidad_citas': 92   # Simulado
    }
    
    # Calcular ingreso promedio por servicio
    if stats['mes']['completadas'] > 0:
        metricas['ingreso_promedio_servicio'] = stats['mes']['ingresos'] / stats['mes']['completadas']
    
    # Calcular servicios promedio por día (basado en el mes)
    if stats['mes']['completadas'] > 0:
        dias_del_mes = (hoy - inicio_mes).days + 1
        metricas['servicios_promedio_dia'] = stats['mes']['completadas'] / dias_del_mes
    
    context = {
        'stats': stats,
        'servicios_populares': servicios_populares,
        'metricas': metricas,
    }
    
    return render(request, 'carwash/estadisticas.html', context)