# reportes/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Q, Avg
from django.http import HttpResponse, JsonResponse
from datetime import datetime, date, timedelta
from citas.models import Cita, TipoServicio
from inventario.models import Producto, MovimientoInventario, AlertaInventario
from usuarios.models import Perfil
import json

def es_staff_reportes(user):
    """Verificar si el usuario puede ver reportes"""
    if not user.is_authenticated:
        return False
    try:
        perfil = Perfil.objects.get(usuario=user)
        return perfil.rol and perfil.rol.nombre in ['Administrador', 'Mecánico', 'Recepcionista']
    except (Perfil.DoesNotExist, AttributeError):
        return user.is_superuser

@login_required
def dashboard_reportes(request):
    """Dashboard principal de reportes"""
    if not es_staff_reportes(request.user):
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('dashboard')
    
    hoy = date.today()
    inicio_mes = hoy.replace(day=1)
    
    # Resumen general
    resumen = {
        'citas_hoy': Cita.objects.filter(fecha=hoy).count(),
        'citas_mes': Cita.objects.filter(fecha__gte=inicio_mes).count(),
        'ingresos_mes': Cita.objects.filter(
            fecha__gte=inicio_mes, 
            estado='COMPLETADA'
        ).aggregate(total=Sum('servicio__precio'))['total'] or 0,
        'productos_stock_bajo': Producto.objects.filter(
            activo=True,
            stock_actual__lte=('stock_minimo')
        ).count(),
    }
    
    return render(request, 'reportes/dashboard.html', {'resumen': resumen})

@login_required
def reporte_citas(request):
    """Reporte detallado de citas"""
    if not es_staff_reportes(request.user):
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('dashboard')
    
    # Filtros
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    estado = request.GET.get('estado')
    categoria = request.GET.get('categoria')
    
    citas = Cita.objects.all().select_related('cliente', 'servicio', 'vehiculo')
    
    # Aplicar filtros
    if fecha_inicio:
        citas = citas.filter(fecha__gte=fecha_inicio)
    if fecha_fin:
        citas = citas.filter(fecha__lte=fecha_fin)
    if estado:
        citas = citas.filter(estado=estado)
    if categoria:
        citas = citas.filter(servicio__categoria=categoria)
    
    # Estadísticas del reporte
    stats = {
        'total_citas': citas.count(),
        'por_estado': citas.values('estado').annotate(count=Count('id')),
        'por_categoria': citas.values('servicio__categoria').annotate(count=Count('id')),
        'ingresos_totales': citas.filter(estado='COMPLETADA').aggregate(
            total=Sum('servicio__precio')
        )['total'] or 0,
    }
    
    # Ordenar por fecha más reciente
    citas = citas.order_by('-fecha', '-hora_inicio')
    
    context = {
        'citas': citas,
        'stats': stats,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'estado_filtro': estado,
        'categoria_filtro': categoria,
        'estados': Cita.ESTADOS,
        'categorias': TipoServicio.CATEGORIAS,
    }
    
    return render(request, 'reportes/citas.html', context)

@login_required
def reporte_inventario(request):
    """Reporte detallado de inventario"""
    if not es_staff_reportes(request.user):
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('dashboard')
    
    from django.db.models import F
    from inventario.models import CategoriaProducto
    
    # Filtros
    categoria_id = request.GET.get('categoria')
    solo_stock_bajo = request.GET.get('solo_stock_bajo')
    
    productos = Producto.objects.filter(activo=True).annotate(
        valor_total=F('stock_actual') * F('precio_compra')
    )
    
    if categoria_id:
        productos = productos.filter(categoria_id=categoria_id)
    
    if solo_stock_bajo:
        productos = productos.filter(stock_actual__lte=F('stock_minimo'))
    
    # Estadísticas
    stats = {
        'total_productos': productos.count(),
        'valor_total_inventario': productos.aggregate(
            total=Sum('valor_total')
        )['total'] or 0,
        'productos_stock_bajo': productos.filter(
            stock_actual__lte=F('stock_minimo')
        ).count(),
        'productos_agotados': productos.filter(stock_actual=0).count(),
    }
    
    # Alertas activas
    alertas_activas = AlertaInventario.objects.filter(activa=True).count()
    
    # Por categoría
    stats_por_categoria = CategoriaProducto.objects.annotate(
        total_productos=Count('producto', filter=Q(producto__activo=True)),
        valor_categoria=Sum(
            F('producto__stock_actual') * F('producto__precio_compra'),
            filter=Q(producto__activo=True)
        )
    ).order_by('-valor_categoria')
    
    context = {
        'productos': productos.order_by('nombre'),
        'stats': stats,
        'alertas_activas': alertas_activas,
        'stats_por_categoria': stats_por_categoria,
        'categorias': CategoriaProducto.objects.all(),
        'categoria_filtro': categoria_id,
        'solo_stock_bajo': solo_stock_bajo,
    }
    
    return render(request, 'reportes/inventario.html', context)

@login_required
def reporte_ingresos(request):
    """Reporte de ingresos por servicios"""
    if not es_staff_reportes(request.user):
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('dashboard')
    
    # Filtros
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    categoria = request.GET.get('categoria')
    
    # Si no hay fechas, usar el mes actual
    if not fecha_inicio:
        fecha_inicio = date.today().replace(day=1)
    else:
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
    
    if not fecha_fin:
        fecha_fin = date.today()
    else:
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
    
    citas_completadas = Cita.objects.filter(
        fecha__gte=fecha_inicio,
        fecha__lte=fecha_fin,
        estado='COMPLETADA'
    )
    
    if categoria:
        citas_completadas = citas_completadas.filter(servicio__categoria=categoria)
    
    # Ingresos por categoría
    ingresos_por_categoria = citas_completadas.values(
        'servicio__categoria'
    ).annotate(
        total_ingresos=Sum('servicio__precio'),
        total_citas=Count('id')
    ).order_by('-total_ingresos')
    
    # Ingresos por servicio
    ingresos_por_servicio = citas_completadas.values(
        'servicio__nombre',
        'servicio__precio'
    ).annotate(
        total_citas=Count('id'),
        total_ingresos=Sum('servicio__precio')
    ).order_by('-total_ingresos')[:10]
    
    # Ingresos diarios en el período
    ingresos_diarios = citas_completadas.extra(
        select={'dia': 'DATE(fecha)'}
    ).values('dia').annotate(
        ingresos_dia=Sum('servicio__precio'),
        citas_dia=Count('id')
    ).order_by('dia')
    
    # Totales
    totales = {
        'total_ingresos': citas_completadas.aggregate(
            total=Sum('servicio__precio')
        )['total'] or 0,
        'total_citas': citas_completadas.count(),
        'promedio_por_cita': 0
    }
    
    if totales['total_citas'] > 0:
        totales['promedio_por_cita'] = totales['total_ingresos'] / totales['total_citas']
    
    context = {
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'categoria_filtro': categoria,
        'ingresos_por_categoria': ingresos_por_categoria,
        'ingresos_por_servicio': ingresos_por_servicio,
        'ingresos_diarios': ingresos_diarios,
        'totales': totales,
        'categorias': TipoServicio.CATEGORIAS,
    }
    
    return render(request, 'reportes/ingresos.html', context)

@login_required
def exportar_reporte_citas(request):
    """Exportar reporte de citas a CSV"""
    if not es_staff_reportes(request.user):
        return HttpResponse("No autorizado", status=401)
    
    import csv
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="reporte_citas.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Cliente', 'Servicio', 'Categoria', 'Vehiculo', 
        'Fecha', 'Hora', 'Estado', 'Precio'
    ])
    
    citas = Cita.objects.all().select_related('cliente', 'servicio', 'vehiculo')
    
    for cita in citas:
        writer.writerow([
            cita.id,
            cita.cliente.get_full_name() or cita.cliente.username,
            cita.servicio.nombre,
            cita.servicio.get_categoria_display(),
            f"{cita.vehiculo.marca} {cita.vehiculo.modelo} ({cita.vehiculo.placa})",
            cita.fecha,
            cita.hora_inicio,
            cita.get_estado_display(),
            cita.servicio.precio
        ])
    
    return response

@login_required
def api_estadisticas_graficos(request):
    """API para datos de gráficos"""
    if not es_staff_reportes(request.user):
        return JsonResponse({'error': 'No autorizado'}, status=401)
    
    tipo = request.GET.get('tipo')
    
    if tipo == 'citas_por_mes':
        # Últimos 12 meses
        from datetime import datetime
        from dateutil.relativedelta import relativedelta
        
        datos = []
        fecha_actual = date.today().replace(day=1)
        
        for i in range(12):
            fecha_inicio = fecha_actual - relativedelta(months=i)
            fecha_fin = (fecha_inicio + relativedelta(months=1)) - timedelta(days=1)
            
            citas_mes = Cita.objects.filter(
                fecha__gte=fecha_inicio,
                fecha__lte=fecha_fin
            ).count()
            
            datos.append({
                'mes': fecha_inicio.strftime('%Y-%m'),
                'mes_nombre': fecha_inicio.strftime('%b %Y'),
                'citas': citas_mes
            })
        
        datos.reverse()
        return JsonResponse({'datos': datos})
    
    elif tipo == 'ingresos_categoria':
        # Ingresos por categoría del mes actual
        inicio_mes = date.today().replace(day=1)
        
        datos = []
        for categoria_key, categoria_nombre in TipoServicio.CATEGORIAS:
            ingresos = Cita.objects.filter(
                fecha__gte=inicio_mes,
                estado='COMPLETADA',
                servicio__categoria=categoria_key
            ).aggregate(total=Sum('servicio__precio'))['total'] or 0
            
            datos.append({
                'categoria': categoria_nombre,
                'ingresos': float(ingresos)
            })
        
        return JsonResponse({'datos': datos})
    
    return JsonResponse({'error': 'Tipo no válido'}, status=400)