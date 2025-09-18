# vehiculos/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Avg, Q
from datetime import datetime, date, timedelta
from citas.models import Vehiculo, Cita, TipoServicio
from inventario.models import Producto, MovimientoInventario
from usuarios.models import Perfil

# Importar los modelos nuevos (una vez creados)
# from .models import HistorialServicio, RepuestoUtilizado, MantenimientoRecomendado

def es_propietario_o_staff(user, vehiculo):
    """Verificar si el usuario es propietario del vehículo o staff"""
    if vehiculo.propietario == user:
        return True
    try:
        perfil = Perfil.objects.get(usuario=user)
        return perfil.rol and perfil.rol.nombre in ['Administrador', 'Mecánico', 'Recepcionista']
    except (Perfil.DoesNotExist, AttributeError):
        return user.is_superuser

@login_required
def dashboard_vehiculos(request):
    """Dashboard de gestión de vehículos"""
    # Si es cliente, mostrar solo sus vehículos
    if hasattr(request.user, 'perfil') and request.user.perfil.rol and request.user.perfil.rol.nombre == 'Cliente':
        vehiculos = Vehiculo.objects.filter(propietario=request.user)
    else:
        # Staff puede ver todos los vehículos
        vehiculos = Vehiculo.objects.all()
    
    # Estadísticas
    stats = {
        'total_vehiculos': vehiculos.count(),
        'vehiculos_con_servicios': vehiculos.filter(citas__isnull=False).distinct().count(),
        'servicios_mes_actual': Cita.objects.filter(
            vehiculo__in=vehiculos,
            fecha__month=date.today().month,
            fecha__year=date.today().year,
            estado='COMPLETADA'
        ).count(),
    }
    
    # Vehículos con servicios recientes
    vehiculos_recientes = vehiculos.filter(
        citas__fecha__gte=date.today() - timedelta(days=30),
        citas__estado='COMPLETADA'
    ).distinct()[:5]
    
    # Próximos mantenimientos (simulado)
    proximos_mantenimientos = []
    
    context = {
        'vehiculos': vehiculos[:10],  # Mostrar solo los primeros 10
        'stats': stats,
        'vehiculos_recientes': vehiculos_recientes,
        'proximos_mantenimientos': proximos_mantenimientos,
    }
    
    return render(request, 'vehiculos/dashboard.html', context)

@login_required
def detalle_vehiculo_completo(request, vehiculo_id):
    """Vista detallada del vehículo con historial completo"""
    vehiculo = get_object_or_404(Vehiculo, id=vehiculo_id)
    
    # Verificar permisos
    if not es_propietario_o_staff(request.user, vehiculo):
        messages.error(request, 'No tienes permiso para ver este vehículo.')
        return redirect('lista_vehiculos')
    
    # Historial de servicios (todas las citas completadas)
    historial_servicios = Cita.objects.filter(
        vehiculo=vehiculo,
        estado='COMPLETADA'
    ).select_related('servicio', 'atendida_por').order_by('-fecha')
    
    # Estadísticas del vehículo
    stats = {
        'total_servicios': historial_servicios.count(),
        'gasto_total': historial_servicios.aggregate(
            total=Sum('servicio__precio')
        )['total'] or 0,
        'ultimo_servicio': historial_servicios.first(),
        'servicios_por_categoria': historial_servicios.values(
            'servicio__categoria'
        ).annotate(count=Count('id')),
        'promedio_gasto': historial_servicios.aggregate(
            promedio=Avg('servicio__precio')
        )['promedio'] or 0,
    }
    
    # Próximas citas
    proximas_citas = Cita.objects.filter(
        vehiculo=vehiculo,
        fecha__gte=date.today(),
        estado__in=['PENDIENTE', 'CONFIRMADA']
    ).order_by('fecha', 'hora_inicio')
    
    # Servicios más frecuentes
    servicios_frecuentes = historial_servicios.values(
        'servicio__nombre'
    ).annotate(
        cantidad=Count('id')
    ).order_by('-cantidad')[:5]
    
    context = {
        'vehiculo': vehiculo,
        'historial_servicios': historial_servicios[:10],  # Últimos 10
        'stats': stats,
        'proximas_citas': proximas_citas,
        'servicios_frecuentes': servicios_frecuentes,
    }
    
    return render(request, 'vehiculos/detalle_completo.html', context)

@login_required
def historial_servicios_vehiculo(request, vehiculo_id):
    """Historial completo de servicios de un vehículo"""
    vehiculo = get_object_or_404(Vehiculo, id=vehiculo_id)
    
    if not es_propietario_o_staff(request.user, vehiculo):
        messages.error(request, 'No tienes permiso para ver este vehículo.')
        return redirect('lista_vehiculos')
    
    # Filtros
    categoria = request.GET.get('categoria')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    servicios = Cita.objects.filter(
        vehiculo=vehiculo,
        estado='COMPLETADA'
    ).select_related('servicio', 'atendida_por')
    
    if categoria:
        servicios = servicios.filter(servicio__categoria=categoria)
    if fecha_inicio:
        servicios = servicios.filter(fecha__gte=fecha_inicio)
    if fecha_fin:
        servicios = servicios.filter(fecha__lte=fecha_fin)
    
    servicios = servicios.order_by('-fecha')
    
    # Resumen de gastos
    resumen = {
        'total_servicios': servicios.count(),
        'gasto_total': servicios.aggregate(total=Sum('servicio__precio'))['total'] or 0,
        'gasto_promedio': servicios.aggregate(promedio=Avg('servicio__precio'))['promedio'] or 0,
    }
    
    context = {
        'vehiculo': vehiculo,
        'servicios': servicios,
        'resumen': resumen,
        'categoria_filtro': categoria,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'categorias': TipoServicio.CATEGORIAS,
    }
    
    return render(request, 'vehiculos/historial_servicios.html', context)

@login_required
def crear_historial_detallado(request, cita_id):
    """Crear historial detallado de servicio (para mecánicos)"""
    cita = get_object_or_404(Cita, id=cita_id)
    
    # Solo mecánicos/admin pueden crear historiales detallados
    try:
        perfil = Perfil.objects.get(usuario=request.user)
        if not (perfil.rol and perfil.rol.nombre in ['Administrador', 'Mecánico']):
            messages.error(request, 'No tienes permiso para crear historiales detallados.')
            return redirect('calendario_citas')
    except Perfil.DoesNotExist:
        if not request.user.is_superuser:
            messages.error(request, 'No tienes permiso para crear historiales detallados.')
            return redirect('calendario_citas')
    
    if request.method == 'POST':
        # Recoger datos del formulario
        descripcion_trabajo = request.POST.get('descripcion_trabajo')
        observaciones_mecanico = request.POST.get('observaciones_mecanico', '')
        kilometraje = request.POST.get('kilometraje')
        costo_mano_obra = request.POST.get('costo_mano_obra', 0)
        
        # Crear registro de historial detallado (usando el modelo de la cita por ahora)
        # En el futuro, aquí se usaría HistorialServicio.objects.create(...)
        
        # Por ahora, actualizamos las notas de la cita
        cita.notas = f"TRABAJO REALIZADO: {descripcion_trabajo}\n"
        if observaciones_mecanico:
            cita.notas += f"OBSERVACIONES: {observaciones_mecanico}\n"
        if kilometraje:
            cita.notas += f"KILOMETRAJE: {kilometraje}\n"
        
        cita.estado = 'COMPLETADA'
        cita.atendida_por = request.user
        cita.save()
        
        # Registrar uso de repuestos si hay
        repuestos_data = request.POST.getlist('repuesto_id')
        cantidades_data = request.POST.getlist('cantidad_repuesto')
        
        for i, repuesto_id in enumerate(repuestos_data):
            if repuesto_id and i < len(cantidades_data):
                try:
                    producto = Producto.objects.get(id=repuesto_id)
                    cantidad = int(cantidades_data[i])
                    
                    # Crear movimiento de inventario
                    MovimientoInventario.objects.create(
                        producto=producto,
                        tipo='SALIDA',
                        motivo='SERVICIO',
                        cantidad=cantidad,
                        precio_unitario=producto.precio_venta,
                        stock_anterior=producto.stock_actual,
                        stock_nuevo=producto.stock_actual - cantidad,
                        usuario=request.user,
                        cita=cita,
                        observaciones=f"Usado en {cita.servicio.nombre} - {cita.vehiculo}"
                    )
                    
                    # Actualizar stock
                    producto.stock_actual = max(0, producto.stock_actual - cantidad)
                    producto.save()
                    
                except (Producto.DoesNotExist, ValueError):
                    continue
        
        messages.success(request, 'Historial de servicio creado correctamente.')
        return redirect('detalle_cita', cita_id=cita.id)
    
    # Obtener repuestos disponibles
    repuestos = Producto.objects.filter(
        tipo='REPUESTO',
        activo=True,
        stock_actual__gt=0
    ).order_by('nombre')
    
    context = {
        'cita': cita,
        'repuestos': repuestos,
    }
    
    return render(request, 'vehiculos/crear_historial.html', context)

@login_required
def estadisticas_vehiculo(request, vehiculo_id):
    """Estadísticas detalladas de un vehículo"""
    vehiculo = get_object_or_404(Vehiculo, id=vehiculo_id)
    
    if not es_propietario_o_staff(request.user, vehiculo):
        messages.error(request, 'No tienes permiso para ver este vehículo.')
        return redirect('lista_vehiculos')
    
    # Servicios por año
    servicios_por_año = Cita.objects.filter(
        vehiculo=vehiculo,
        estado='COMPLETADA'
    ).extra(
        select={'año': 'YEAR(fecha)'}
    ).values('año').annotate(
        total_servicios=Count('id'),
        gasto_total=Sum('servicio__precio')
    ).order_by('-año')
    
    # Servicios por mes (último año)
    servicios_por_mes = Cita.objects.filter(
        vehiculo=vehiculo,
        estado='COMPLETADA',
        fecha__gte=date.today() - timedelta(days=365)
    ).extra(
        select={'mes': 'DATE_FORMAT(fecha, "%Y-%m")'}
    ).values('mes').annotate(
        total_servicios=Count('id'),
        gasto_total=Sum('servicio__precio')
    ).order_by('mes')
    
    # Frecuencia de servicios
    frecuencia_servicios = Cita.objects.filter(
        vehiculo=vehiculo,
        estado='COMPLETADA'
    ).values(
        'servicio__nombre',
        'servicio__categoria'
    ).annotate(
        cantidad=Count('id'),
        gasto_total=Sum('servicio__precio')
    ).order_by('-cantidad')
    
    # Comparación con otros vehículos de la misma marca/modelo
    vehiculos_similares = Vehiculo.objects.filter(
        marca=vehiculo.marca,
        modelo=vehiculo.modelo
    ).exclude(id=vehiculo.id)
    
    if vehiculos_similares.exists():
        promedio_similar = Cita.objects.filter(
            vehiculo__in=vehiculos_similares,
            estado='COMPLETADA'
        ).aggregate(
            promedio_gasto=Avg('servicio__precio'),
            promedio_servicios=Count('id') / vehiculos_similares.count()
        )
    else:
        promedio_similar = {'promedio_gasto': 0, 'promedio_servicios': 0}
    
    context = {
        'vehiculo': vehiculo,
        'servicios_por_año': servicios_por_año,
        'servicios_por_mes': list(servicios_por_mes),
        'frecuencia_servicios': frecuencia_servicios,
        'promedio_similar': promedio_similar,
    }
    
    return render(request, 'vehiculos/estadisticas.html', context)

@login_required
def vehiculos_por_cliente(request):
    """Vista para staff: vehículos agrupados por cliente"""
    try:
        perfil = Perfil.objects.get(usuario=request.user)
        if not (perfil.rol and perfil.rol.nombre in ['Administrador', 'Mecánico', 'Recepcionista']):
            messages.error(request, 'No tienes permiso para acceder a esta sección.')
            return redirect('dashboard')
    except Perfil.DoesNotExist:
        if not request.user.is_superuser:
            messages.error(request, 'No tienes permiso para acceder a esta sección.')
            return redirect('dashboard')
    
    from django.contrib.auth.models import User
    
    # Clientes con sus vehículos
    clientes_con_vehiculos = User.objects.filter(
        vehiculos__isnull=False
    ).prefetch_related('vehiculos').annotate(
        total_vehiculos=Count('vehiculos'),
        total_servicios=Count('vehiculos__citas', filter=Q(vehiculos__citas__estado='COMPLETADA')),
        gasto_total=Sum('vehiculos__citas__servicio__precio', filter=Q(vehiculos__citas__estado='COMPLETADA'))
    ).order_by('-total_servicios')
    
    context = {
        'clientes_con_vehiculos': clientes_con_vehiculos,
    }
    
    return render(request, 'vehiculos/por_cliente.html', context)