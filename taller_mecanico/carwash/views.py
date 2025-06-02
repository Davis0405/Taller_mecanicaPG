# carwash/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Avg, Sum
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone
import datetime

from .models import (
    PaqueteCarwash, TipoVehiculo, CitaCarwash, CalificacionCarwash, ProductoCarwash
)
from .forms import (
    PaqueteCarwashForm, TipoVehiculoForm, CitaCarwashForm, 
    GestionCarwashForm, CalificacionCarwashForm, BusquedaCarwashForm, ProductoCarwashForm
)
from citas.models import Cita, TipoServicio
from usuarios.models import Perfil

def es_staff_carwash(user):
    """Verificar si el usuario puede gestionar carwash"""
    if not user.is_authenticated:
        return False
    try:
        perfil = Perfil.objects.get(usuario=user)
        return perfil.rol and perfil.rol.nombre in ['Administrador', 'Mecánico', 'Recepcionista']
    except (Perfil.DoesNotExist, AttributeError):
        return user.is_superuser

# ============= DASHBOARD CARWASH =============

@login_required
def dashboard_carwash(request):
    """Dashboard principal de carwash"""
    if not es_staff_carwash(request.user):
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('dashboard')
    
    # Estadísticas del día
    hoy = timezone.now().date()
    citas_hoy = CitaCarwash.objects.filter(cita__fecha=hoy)
    
    # Estadísticas generales
    total_citas_hoy = citas_hoy.count()
    en_proceso = citas_hoy.filter(estado_proceso__in=['LAVANDO', 'SECANDO', 'FINALIZANDO']).count()
    completadas_hoy = citas_hoy.filter(estado_proceso='ENTREGADO').count()
    ingresos_hoy = citas_hoy.filter(estado_proceso='ENTREGADO').aggregate(
        total=Sum('precio_total')
    )['total'] or 0
    
    # Próximas citas
    proximas_citas = CitaCarwash.objects.filter(
        cita__fecha=hoy,
        estado_proceso='EN_ESPERA'
    ).order_by('cita__hora_inicio')[:5]
    
    # Estadísticas de la semana
    inicio_semana = hoy - datetime.timedelta(days=hoy.weekday())
    fin_semana = inicio_semana + datetime.timedelta(days=6)
    
    citas_semana = CitaCarwash.objects.filter(
        cita__fecha__range=[inicio_semana, fin_semana],
        estado_proceso='ENTREGADO'
    )
    
    ingresos_semana = citas_semana.aggregate(total=Sum('precio_total'))['total'] or 0
    
    # Paquetes más populares
    paquetes_populares = CitaCarwash.objects.filter(
        cita__fecha__gte=inicio_semana
    ).values('paquete__nombre').annotate(
        total=Count('id')
    ).order_by('-total')[:5]
    
    # Calificaciones promedio
    calificacion_promedio = CalificacionCarwash.objects.aggregate(
        promedio=Avg('puntuacion')
    )['promedio'] or 0
    
    context = {
        'total_citas_hoy': total_citas_hoy,
        'en_proceso': en_proceso,
        'completadas_hoy': completadas_hoy,
        'ingresos_hoy': ingresos_hoy,
        'ingresos_semana': ingresos_semana,
        'proximas_citas': proximas_citas,
        'paquetes_populares': paquetes_populares,
        'calificacion_promedio': calificacion_promedio,
    }
    
    return render(request, 'carwash/dashboard.html', context)

# ============= GESTIÓN DE PAQUETES =============

@login_required
def lista_paquetes(request):
    """Lista de paquetes de carwash"""
    if not es_staff_carwash(request.user):
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('dashboard')
    
    paquetes = PaqueteCarwash.objects.all().order_by('tipo', 'precio_base')
    return render(request, 'carwash/lista_paquetes.html', {'paquetes': paquetes})

@login_required
def agregar_paquete(request):
    """Agregar nuevo paquete de carwash"""
    if not es_staff_carwash(request.user):
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = PaqueteCarwashForm(request.POST)
        if form.is_valid():
            paquete = form.save()
            
            # Crear o actualizar el TipoServicio correspondiente
            tipo_servicio, created = TipoServicio.objects.get_or_create(
                nombre=paquete.nombre,
                categoria='CARWASH',
                defaults={
                    'descripcion': paquete.descripcion,
                    'duracion': paquete.duracion_estimada,
                    'precio': paquete.precio_base
                }
            )
            
            if not created:
                tipo_servicio.descripcion = paquete.descripcion
                tipo_servicio.duracion = paquete.duracion_estimada
                tipo_servicio.precio = paquete.precio_base
                tipo_servicio.save()
            
            messages.success(request, 'Paquete de carwash agregado correctamente.')
            return redirect('lista_paquetes')
    else:
        form = PaqueteCarwashForm()
    
    return render(request, 'carwash/agregar_paquete.html', {'form': form})

@login_required
def editar_paquete(request, paquete_id):
    """Editar paquete de carwash"""
    if not es_staff_carwash(request.user):
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('dashboard')
    
    paquete = get_object_or_404(PaqueteCarwash, id=paquete_id)
    
    if request.method == 'POST':
        form = PaqueteCarwashForm(request.POST, instance=paquete)
        if form.is_valid():
            paquete = form.save()
            
            # Actualizar TipoServicio correspondiente
            try:
                tipo_servicio = TipoServicio.objects.get(
                    nombre=paquete.nombre,
                    categoria='CARWASH'
                )
                tipo_servicio.descripcion = paquete.descripcion
                tipo_servicio.duracion = paquete.duracion_estimada
                tipo_servicio.precio = paquete.precio_base
                tipo_servicio.save()
            except TipoServicio.DoesNotExist:
                pass
            
            messages.success(request, 'Paquete actualizado correctamente.')
            return redirect('lista_paquetes')
    else:
        form = PaqueteCarwashForm(instance=paquete)
    
    return render(request, 'carwash/editar_paquete.html', {'form': form, 'paquete': paquete})

# ============= GESTIÓN DE CITAS CARWASH =============

@login_required
def lista_citas_carwash(request):
    """Lista de citas de carwash con filtros"""
    if not es_staff_carwash(request.user):
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('dashboard')
    
    form = BusquedaCarwashForm(request.GET)
    citas = CitaCarwash.objects.select_related(
        'cita', 'cita__cliente', 'cita__vehiculo', 'paquete', 'tipo_vehiculo'
    ).order_by('-cita__fecha', 'cita__hora_inicio')
    
    if form.is_valid():
        fecha_desde = form.cleaned_data.get('fecha_desde')
        fecha_hasta = form.cleaned_data.get('fecha_hasta')
        estado_proceso = form.cleaned_data.get('estado_proceso')
        paquete = form.cleaned_data.get('paquete')
        
        if fecha_desde:
            citas = citas.filter(cita__fecha__gte=fecha_desde)
        
        if fecha_hasta:
            citas = citas.filter(cita__fecha__lte=fecha_hasta)
        
        if estado_proceso:
            citas = citas.filter(estado_proceso=estado_proceso)
        
        if paquete:
            citas = citas.filter(paquete=paquete)
    
    # Paginación
    paginator = Paginator(citas, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'form': form,
        'page_obj': page_obj,
    }
    
    return render(request, 'carwash/lista_citas.html', context)

@login_required
def detalle_cita_carwash(request, cita_id):
    """Detalle de cita de carwash"""
    cita_carwash = get_object_or_404(CitaCarwash, cita__id=cita_id)
    
    # Verificar permisos
    if not es_staff_carwash(request.user) and cita_carwash.cita.cliente != request.user:
        messages.error(request, 'No tienes permiso para ver esta cita.')
        return redirect('dashboard')
    
    productos_utilizados = ProductoCarwash.objects.filter(cita_carwash=cita_carwash)
    
    context = {
        'cita_carwash': cita_carwash,
        'productos_utilizados': productos_utilizados,
    }
    
    return render(request, 'carwash/detalle_cita.html', context)

@login_required
def gestionar_cita_carwash(request, cita_id):
    """Gestionar el proceso de una cita de carwash"""
    if not es_staff_carwash(request.user):
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('dashboard')
    
    cita_carwash = get_object_or_404(CitaCarwash, cita__id=cita_id)
    
    if request.method == 'POST':
        form = GestionCarwashForm(request.POST, instance=cita_carwash)
        if form.is_valid():
            estado_anterior = cita_carwash.estado_proceso
            cita_carwash = form.save()
            
            # Actualizar tiempos según el estado
            if estado_anterior != cita_carwash.estado_proceso:
                if cita_carwash.estado_proceso == 'LAVANDO' and not cita_carwash.hora_inicio_proceso:
                    cita_carwash.hora_inicio_proceso = timezone.now()
                elif cita_carwash.estado_proceso == 'ENTREGADO' and not cita_carwash.hora_fin_proceso:
                    cita_carwash.hora_fin_proceso = timezone.now()
                    # Actualizar estado de la cita principal
                    cita_carwash.cita.estado = 'COMPLETADA'
                    cita_carwash.cita.save()
                
                cita_carwash.save()
            
            messages.success(request, 'Estado de la cita actualizado correctamente.')
            return redirect('lista_citas_carwash')
    else:
        form = GestionCarwashForm(instance=cita_carwash)
    
    context = {
        'form': form,
        'cita_carwash': cita_carwash,
    }
    
    return render(request, 'carwash/gestionar_cita.html', context)

# ============= CALIFICACIONES =============

@login_required
def calificar_servicio(request, cita_id):
    """Permitir al cliente calificar el servicio de carwash"""
    cita_carwash = get_object_or_404(CitaCarwash, cita__id=cita_id)
    
    # Verificar que sea el cliente de la cita
    if cita_carwash.cita.cliente != request.user:
        messages.error(request, 'No puedes calificar esta cita.')
        return redirect('mis_citas')
    
    # Verificar que el servicio esté terminado
    if cita_carwash.estado_proceso != 'ENTREGADO':
        messages.error(request, 'Solo puedes calificar servicios completados.')
        return redirect('mis_citas')
    
    # Verificar si ya existe una calificación
    calificacion_existente = CalificacionCarwash.objects.filter(cita_carwash=cita_carwash).first()
    
    if request.method == 'POST':
        form = CalificacionCarwashForm(request.POST, instance=calificacion_existente)
        if form.is_valid():
            calificacion = form.save(commit=False)
            calificacion.cita_carwash = cita_carwash
            calificacion.save()
            
            messages.success(request, '¡Gracias por tu calificación!')
            return redirect('mis_citas')
    else:
        form = CalificacionCarwashForm(instance=calificacion_existente)
    
    context = {
        'form': form,
        'cita_carwash': cita_carwash,
        'calificacion_existente': calificacion_existente,
    }
    
    return render(request, 'carwash/calificar_servicio.html', context)

# ============= API Y UTILIDADES =============

@login_required
def api_precio_paquete(request, paquete_id, tipo_vehiculo_id):
    """API para calcular precio según paquete y tipo de vehículo"""
    try:
        paquete = PaqueteCarwash.objects.get(id=paquete_id)
        tipo_vehiculo = TipoVehiculo.objects.get(id=tipo_vehiculo_id)
        
        precio_total = paquete.precio_base * tipo_vehiculo.factor_precio
        
        return JsonResponse({
            'precio_base': float(paquete.precio_base),
            'factor_precio': float(tipo_vehiculo.factor_precio),
            'precio_total': float(precio_total),
            'servicios_incluidos': paquete.get_servicios_incluidos()
        })
    except (PaqueteCarwash.DoesNotExist, TipoVehiculo.DoesNotExist):
        return JsonResponse({'error': 'Paquete o tipo de vehículo no encontrado'}, status=404)

@login_required
def tablero_tiempo_real(request):
    """Tablero de tiempo real para monitorear carwash"""
    if not es_staff_carwash(request.user):
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('dashboard')
    
    hoy = timezone.now().date()
    
    # Citas por estado
    citas_por_estado = {}
    for estado, descripcion in CitaCarwash.ESTADOS_PROCESO:
        count = CitaCarwash.objects.filter(
            cita__fecha=hoy,
            estado_proceso=estado
        ).count()
        citas_por_estado[estado] = {
            'descripcion': descripcion,
            'count': count
        }
    
    # Citas en proceso con detalles
    citas_en_proceso = CitaCarwash.objects.filter(
        cita__fecha=hoy,
        estado_proceso__in=['LAVANDO', 'SECANDO', 'FINALIZANDO']
    ).select_related('cita', 'cita__cliente', 'cita__vehiculo', 'paquete', 'lavador_asignado')
    
    # Próximas citas
    proximas_citas = CitaCarwash.objects.filter(
        cita__fecha=hoy,
        estado_proceso='EN_ESPERA'
    ).select_related('cita', 'cita__cliente', 'cita__vehiculo', 'paquete').order_by('cita__hora_inicio')
    
    context = {
        'citas_por_estado': citas_por_estado,
        'citas_en_proceso': citas_en_proceso,
        'proximas_citas': proximas_citas,
    }
    
    return render(request, 'carwash/tablero_tiempo_real.html', context)

# ============= GESTIÓN DE TIPOS DE VEHÍCULO =============

@login_required
def lista_tipos_vehiculo(request):
    """Lista de tipos de vehículo"""
    if not es_staff_carwash(request.user):
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('dashboard')
    
    tipos = TipoVehiculo.objects.all().order_by('nombre')
    return render(request, 'carwash/lista_tipos_vehiculo.html', {'tipos': tipos})

@login_required
def agregar_tipo_vehiculo(request):
    """Agregar nuevo tipo de vehículo"""
    if not es_staff_carwash(request.user):
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = TipoVehiculoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tipo de vehículo agregado correctamente.')
            return redirect('lista_tipos_vehiculo')
    else:
        form = TipoVehiculoForm()
    
    return render(request, 'carwash/agregar_tipo_vehiculo.html', {'form': form})

# ============= REPORTES CARWASH =============

@login_required
def reporte_ventas_carwash(request):
    """Reporte de ventas de carwash"""
    if not es_staff_carwash(request.user):
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('dashboard')
    
    # Filtros de fecha
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    # Por defecto, último mes
    if not fecha_desde:
        fecha_desde = (timezone.now().date() - datetime.timedelta(days=30)).strftime('%Y-%m-%d')
    if not fecha_hasta:
        fecha_hasta = timezone.now().date().strftime('%Y-%m-%d')
    
    # Consulta base
    citas = CitaCarwash.objects.filter(
        estado_proceso='ENTREGADO',
        cita__fecha__range=[fecha_desde, fecha_hasta]
    )
    
    # Estadísticas generales
    total_servicios = citas.count()
    ingresos_totales = citas.aggregate(total=Sum('precio_total'))['total'] or 0
    promedio_por_servicio = ingresos_totales / total_servicios if total_servicios > 0 else 0
    
    # Ventas por paquete
    ventas_por_paquete = citas.values('paquete__nombre').annotate(
        cantidad=Count('id'),
        ingresos=Sum('precio_total')
    ).order_by('-ingresos')
    
    # Ventas por día
    ventas_por_dia = citas.extra(
        select={'dia': 'DATE(citas_cita.fecha)'}
    ).values('dia').annotate(
        cantidad=Count('id'),
        ingresos=Sum('precio_total')
    ).order_by('dia')
    
    # Tipos de vehículo más atendidos
    vehiculos_atendidos = citas.values('tipo_vehiculo__nombre').annotate(
        cantidad=Count('id')
    ).order_by('-cantidad')
    
    context = {
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'total_servicios': total_servicios,
        'ingresos_totales': ingresos_totales,
        'promedio_por_servicio': promedio_por_servicio,
        'ventas_por_paquete': ventas_por_paquete,
        'ventas_por_dia': ventas_por_dia,
        'vehiculos_atendidos': vehiculos_atendidos,
    }
    
    return render(request, 'carwash/reporte_ventas.html', context)

@login_required
def editar_tipo_vehiculo(request, tipo_id):
    """Editar tipo de vehículo existente"""
    if not es_staff_carwash(request.user):
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('dashboard')
    
    tipo_vehiculo = get_object_or_404(TipoVehiculo, id=tipo_id)
    
    if request.method == 'POST':
        form = TipoVehiculoForm(request.POST, instance=tipo_vehiculo)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tipo de vehículo actualizado correctamente.')
            return redirect('lista_tipos_vehiculo')
    else:
        form = TipoVehiculoForm(instance=tipo_vehiculo)
    
    return render(request, 'carwash/editar_tipo_vehiculo.html', {'form': form, 'tipo_vehiculo': tipo_vehiculo})