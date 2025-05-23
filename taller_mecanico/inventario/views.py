# inventario/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, F
from django.http import JsonResponse
from django.core.paginator import Paginator
import json
from datetime import datetime, timedelta

from .models import (
    Proveedor, Producto, CategoriaProducto, MovimientoInventario,
    OrdenCompra, DetalleOrdenCompra, AlertaInventario, ProductoServicio
)
from .forms import (
    ProveedorForm, ProductoForm, CategoriaForm, MovimientoInventarioForm,
    BusquedaProductoForm, OrdenCompraForm, DetalleOrdenCompraForm,
    ProductoServicioForm, AjusteInventarioForm
)
from usuarios.models import Perfil

def es_staff_inventario(user):
    """Verificar si el usuario puede gestionar inventario"""
    if not user.is_authenticated:
        return False
    try:
        perfil = Perfil.objects.get(usuario=user)
        return perfil.rol and perfil.rol.nombre in ['Administrador', 'Mecánico']
    except (Perfil.DoesNotExist, AttributeError):
        return user.is_superuser

# ============= VISTAS GENERALES =============

@login_required
def dashboard_inventario(request):
    """Dashboard principal de inventario"""
    if not es_staff_inventario(request.user):
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('dashboard')
    
    # Estadísticas generales
    total_productos = Producto.objects.filter(activo=True).count()
    productos_stock_bajo = Producto.objects.filter(
        activo=True,
        stock_actual__lte=F('stock_minimo')
    ).count()
    
    valor_total_inventario = Producto.objects.filter(activo=True).aggregate(
        total=Sum(F('stock_actual') * F('precio_compra'))
    )['total'] or 0
    
    # Productos más vendidos (últimos 30 días)
    fecha_limite = datetime.now() - timedelta(days=30)
    productos_mas_usados = MovimientoInventario.objects.filter(
        tipo='SALIDA',
        fecha__gte=fecha_limite
    ).values('producto__nombre').annotate(
        total_usado=Sum('cantidad')
    ).order_by('-total_usado')[:5]
    
    # Alertas activas
    alertas = AlertaInventario.objects.filter(activa=True)[:5]
    
    context = {
        'total_productos': total_productos,
        'productos_stock_bajo': productos_stock_bajo,
        'valor_total_inventario': valor_total_inventario,
        'productos_mas_usados': productos_mas_usados,
        'alertas': alertas,
    }
    return render(request, 'inventario/dashboard.html', context)

# ============= GESTIÓN DE PRODUCTOS =============

@login_required
def lista_productos(request):
    """Lista de productos con filtros de búsqueda"""
    if not es_staff_inventario(request.user):
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('dashboard')
    
    form = BusquedaProductoForm(request.GET)
    productos = Producto.objects.filter(activo=True)
    
    if form.is_valid():
        busqueda = form.cleaned_data.get('busqueda')
        tipo = form.cleaned_data.get('tipo')
        categoria = form.cleaned_data.get('categoria')
        solo_stock_bajo = form.cleaned_data.get('solo_stock_bajo')
        
        if busqueda:
            productos = productos.filter(
                Q(codigo__icontains=busqueda) |
                Q(nombre__icontains=busqueda) |
                Q(descripcion__icontains=busqueda)
            )
        
        if tipo:
            productos = productos.filter(tipo=tipo)
        
        if categoria:
            productos = productos.filter(categoria=categoria)
        
        if solo_stock_bajo:
            productos = productos.filter(stock_actual__lte=F('stock_minimo'))
    
    # Paginación
    paginator = Paginator(productos, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'form': form,
        'page_obj': page_obj,
        'productos': page_obj,
    }
    return render(request, 'inventario/lista_productos.html', context)

@login_required
def agregar_producto(request):
    """Agregar nuevo producto"""
    if not es_staff_inventario(request.user):
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            producto = form.save()
            
            # Crear movimiento inicial si hay stock inicial
            stock_inicial = request.POST.get('stock_inicial', 0)
            try:
                stock_inicial = int(stock_inicial)
                if stock_inicial > 0:
                    MovimientoInventario.objects.create(
                        producto=producto,
                        tipo='ENTRADA',
                        motivo='AJUSTE_INVENTARIO',
                        cantidad=stock_inicial,
                        precio_unitario=producto.precio_compra,
                        stock_anterior=0,
                        stock_nuevo=stock_inicial,
                        observaciones='Stock inicial',
                        usuario=request.user
                    )
                    
                    producto.stock_actual = stock_inicial
                    producto.save()
            except (ValueError, TypeError):
                pass
            
            messages.success(request, 'Producto agregado correctamente.')
            return redirect('lista_productos')
    else:
        form = ProductoForm()
    
    return render(request, 'inventario/agregar_producto.html', {'form': form})

@login_required
def editar_producto(request, producto_id):
    """Editar producto existente"""
    if not es_staff_inventario(request.user):
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('dashboard')
    
    producto = get_object_or_404(Producto, id=producto_id)
    
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto actualizado correctamente.')
            return redirect('detalle_producto', producto_id=producto.id)
    else:
        form = ProductoForm(instance=producto)
    
    return render(request, 'inventario/editar_producto.html', {'form': form, 'producto': producto})

@login_required
def detalle_producto(request, producto_id):
    """Detalle de producto con historial de movimientos"""
    if not es_staff_inventario(request.user):
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('dashboard')
    
    producto = get_object_or_404(Producto, id=producto_id)
    movimientos = MovimientoInventario.objects.filter(producto=producto).order_by('-fecha')[:20]
    
    context = {
        'producto': producto,
        'movimientos': movimientos,
    }
    return render(request, 'inventario/detalle_producto.html', context)

# ============= GESTIÓN DE MOVIMIENTOS =============

@login_required
def agregar_movimiento(request):
    """Agregar movimiento de inventario"""
    if not es_staff_inventario(request.user):
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = MovimientoInventarioForm(request.POST)
        if form.is_valid():
            movimiento = form.save(commit=False)
            producto = movimiento.producto
            
            # Calcular nuevo stock
            stock_anterior = producto.stock_actual
            
            if movimiento.tipo == 'ENTRADA':
                stock_nuevo = stock_anterior + movimiento.cantidad
            elif movimiento.tipo == 'SALIDA':
                if stock_anterior < movimiento.cantidad:
                    messages.error(request, f'No hay suficiente stock. Stock actual: {stock_anterior}')
                    return render(request, 'inventario/agregar_movimiento.html', {'form': form})
                stock_nuevo = stock_anterior - movimiento.cantidad
            else:  # AJUSTE
                stock_nuevo = movimiento.cantidad
                movimiento.cantidad = abs(stock_nuevo - stock_anterior)
            
            # Guardar movimiento
            movimiento.stock_anterior = stock_anterior
            movimiento.stock_nuevo = stock_nuevo
            movimiento.usuario = request.user
            movimiento.save()
            
            # Actualizar stock del producto
            producto.stock_actual = stock_nuevo
            producto.save()
            
            # Crear alerta si el stock está bajo
            if stock_nuevo <= producto.stock_minimo:
                AlertaInventario.objects.get_or_create(
                    producto=producto,
                    tipo='STOCK_BAJO' if stock_nuevo > 0 else 'STOCK_AGOTADO',
                    defaults={
                        'mensaje': f'El producto {producto.nombre} tiene stock bajo: {stock_nuevo} unidades',
                        'activa': True
                    }
                )
            
            messages.success(request, 'Movimiento registrado correctamente.')
            return redirect('detalle_producto', producto_id=producto.id)
    else:
        form = MovimientoInventarioForm()
    
    return render(request, 'inventario/agregar_movimiento.html', {'form': form})

@login_required
def historial_movimientos(request):
    """Historial completo de movimientos"""
    if not es_staff_inventario(request.user):
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('dashboard')
    
    movimientos = MovimientoInventario.objects.all().order_by('-fecha')
    
    # Filtros
    producto_id = request.GET.get('producto')
    tipo = request.GET.get('tipo')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    if producto_id:
        movimientos = movimientos.filter(producto_id=producto_id)
    
    if tipo:
        movimientos = movimientos.filter(tipo=tipo)
    
    if fecha_desde:
        movimientos = movimientos.filter(fecha__gte=fecha_desde)
    
    if fecha_hasta:
        movimientos = movimientos.filter(fecha__lte=fecha_hasta)
    
    # Paginación
    paginator = Paginator(movimientos, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'productos': Producto.objects.filter(activo=True),
        'tipos_movimiento': MovimientoInventario.TIPOS_MOVIMIENTO,
    }
    return render(request, 'inventario/historial_movimientos.html', context)

# ============= GESTIÓN DE PROVEEDORES =============

@login_required
def lista_proveedores(request):
    """Lista de proveedores"""
    if not es_staff_inventario(request.user):
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('dashboard')
    
    proveedores = Proveedor.objects.all().order_by('nombre')
    return render(request, 'inventario/lista_proveedores.html', {'proveedores': proveedores})

@login_required
def agregar_proveedor(request):
    """Agregar nuevo proveedor"""
    if not es_staff_inventario(request.user):
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = ProveedorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Proveedor agregado correctamente.')
            return redirect('lista_proveedores')
    else:
        form = ProveedorForm()
    
    return render(request, 'inventario/agregar_proveedor.html', {'form': form})

@login_required
def editar_proveedor(request, proveedor_id):
    """Editar proveedor existente"""
    if not es_staff_inventario(request.user):
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('dashboard')
    
    proveedor = get_object_or_404(Proveedor, id=proveedor_id)
    
    if request.method == 'POST':
        form = ProveedorForm(request.POST, instance=proveedor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Proveedor actualizado correctamente.')
            return redirect('lista_proveedores')
    else:
        form = ProveedorForm(instance=proveedor)
    
    return render(request, 'inventario/editar_proveedor.html', {'form': form, 'proveedor': proveedor})

# ============= GESTIÓN DE CATEGORÍAS =============

@login_required
def lista_categorias(request):
    """Lista de categorías de productos"""
    if not es_staff_inventario(request.user):
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('dashboard')
    
    categorias = CategoriaProducto.objects.all().order_by('nombre')
    return render(request, 'inventario/lista_categorias.html', {'categorias': categorias})

@login_required
def agregar_categoria(request):
    """Agregar nueva categoría"""
    if not es_staff_inventario(request.user):
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoría agregada correctamente.')
            return redirect('lista_categorias')
    else:
        form = CategoriaForm()
    
    return render(request, 'inventario/agregar_categoria.html', {'form': form})

# ============= AJUSTES DE INVENTARIO =============

@login_required
def ajustar_inventario(request):
    """Ajuste masivo de inventario"""
    if not es_staff_inventario(request.user):
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = AjusteInventarioForm(request.POST)
        if form.is_valid():
            producto = form.cleaned_data['producto']
            stock_nuevo = form.cleaned_data['stock_nuevo']
            motivo = form.cleaned_data['motivo'] or 'Ajuste de inventario'
            
            stock_anterior = producto.stock_actual
            diferencia = abs(stock_nuevo - stock_anterior)
            tipo_movimiento = 'ENTRADA' if stock_nuevo > stock_anterior else 'SALIDA'
            
            # Crear movimiento de ajuste
            MovimientoInventario.objects.create(
                producto=producto,
                tipo=tipo_movimiento,
                motivo='AJUSTE_INVENTARIO',
                cantidad=diferencia,
                precio_unitario=producto.precio_compra,
                stock_anterior=stock_anterior,
                stock_nuevo=stock_nuevo,
                observaciones=motivo,
                usuario=request.user
            )
            
            # Actualizar stock del producto
            producto.stock_actual = stock_nuevo
            producto.save()
            
            messages.success(request, f'Stock de {producto.nombre} ajustado de {stock_anterior} a {stock_nuevo}.')
            return redirect('lista_productos')
    else:
        form = AjusteInventarioForm()
    
    return render(request, 'inventario/ajustar_inventario.html', {'form': form})

# ============= REPORTES =============

@login_required
def reporte_stock_bajo(request):
    """Reporte de productos con stock bajo"""
    if not es_staff_inventario(request.user):
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('dashboard')
    
    productos_stock_bajo = Producto.objects.filter(
        activo=True,
        stock_actual__lte=F('stock_minimo')
    ).order_by('stock_actual')
    
    return render(request, 'inventario/reporte_stock_bajo.html', {
        'productos': productos_stock_bajo
    })

@login_required
def reporte_valorizado(request):
    """Reporte valorizado del inventario"""
    if not es_staff_inventario(request.user):
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('dashboard')
    
    productos = Producto.objects.filter(activo=True).annotate(
        valor_inventario=F('stock_actual') * F('precio_compra')
    ).order_by('-valor_inventario')
    
    total_inventario = productos.aggregate(
        total=Sum('valor_inventario')
    )['total'] or 0
    
    return render(request, 'inventario/reporte_valorizado.html', {
        'productos': productos,
        'total_inventario': total_inventario
    })

# ============= API ENDPOINTS =============

@login_required
def api_buscar_productos(request):
    """API para buscar productos (para autocompletado)"""
    if not es_staff_inventario(request.user):
        return JsonResponse({'error': 'Sin permisos'}, status=403)
    
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'productos': []})
    
    productos = Producto.objects.filter(
        Q(codigo__icontains=query) | Q(nombre__icontains=query),
        activo=True
    )[:10]
    
    data = {
        'productos': [
            {
                'id': p.id,
                'codigo': p.codigo,
                'nombre': p.nombre,
                'stock_actual': p.stock_actual,
                'precio_venta': float(p.precio_venta)
            }
            for p in productos
        ]
    }
    
    return JsonResponse(data)

@login_required
def api_stock_producto(request, producto_id):
    """API para obtener stock actual de un producto"""
    if not es_staff_inventario(request.user):
        return JsonResponse({'error': 'Sin permisos'}, status=403)
    
    try:
        producto = Producto.objects.get(id=producto_id, activo=True)
        return JsonResponse({
            'stock_actual': producto.stock_actual,
            'stock_minimo': producto.stock_minimo,
            'precio_compra': float(producto.precio_compra),
            'precio_venta': float(producto.precio_venta)
        })
    except Producto.DoesNotExist:
        return JsonResponse({'error': 'Producto no encontrado'}, status=404)
    
# inventario/views.py (agregar estas funciones)

@login_required
def lista_alertas(request):
    """Lista de alertas de inventario"""
    if not es_staff_inventario(request.user):
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('dashboard')
    
    # Filtros
    tipo = request.GET.get('tipo')
    prioridad = request.GET.get('prioridad')
    activa = request.GET.get('activa', 'true')  # Por defecto solo activas
    
    alertas = AlertaInventario.objects.all().order_by('-fecha_creacion')
    
    if tipo:
        alertas = alertas.filter(tipo=tipo)
    
    if prioridad:
        alertas = alertas.filter(prioridad=prioridad)
    
    if activa == 'true':
        alertas = alertas.filter(activa=True)
    elif activa == 'false':
        alertas = alertas.filter(activa=False)
    
    return render(request, 'inventario/lista_alertas.html', {
        'alertas': alertas,
        'tipos_alerta': AlertaInventario.TIPOS,
        'prioridades': AlertaInventario.PRIORIDADES,
    })

@login_required
def resolver_alerta(request, alerta_id):
    """Marcar alerta como resuelta"""
    if not es_staff_inventario(request.user):
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('dashboard')
    
    alerta = get_object_or_404(AlertaInventario, id=alerta_id)
    
    if request.method == 'POST':
        alerta.marcar_como_resuelta(request.user)
        messages.success(request, f'Alerta resuelta: {alerta.producto.nombre}')
        return redirect('lista_alertas')
    
    return render(request, 'inventario/resolver_alerta.html', {'alerta': alerta})

@login_required
def test_notificaciones(request):
    """Vista para probar el sistema de notificaciones"""
    if not es_staff_inventario(request.user):
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        accion = request.POST.get('accion')
        
        if accion == 'generar_alertas':
            from django.core.management import call_command
            try:
                call_command('generar_alertas_inventario', enviar_email=True)
                messages.success(request, 'Alertas generadas y emails enviados correctamente.')
            except Exception as e:
                messages.error(request, f'Error al generar alertas: {e}')
        
        elif accion == 'resumen_diario':
            from .utils import enviar_resumen_alertas_diario
            try:
                if enviar_resumen_alertas_diario():
                    messages.success(request, 'Resumen diario enviado correctamente.')
                else:
                    messages.warning(request, 'No se pudo enviar el resumen diario.')
            except Exception as e:
                messages.error(request, f'Error al enviar resumen: {e}')
        
        elif accion == 'test_email':
            from django.core.mail import send_mail
            from django.conf import settings
            try:
                send_mail(
                    'Prueba de Notificaciones de Inventario',
                    'Este es un email de prueba del sistema de notificaciones de inventario.',
                    settings.EMAIL_HOST_USER,
                    [request.user.email] if request.user.email else [settings.EMAIL_HOST_USER],
                    fail_silently=False,
                )
                messages.success(request, 'Email de prueba enviado correctamente.')
            except Exception as e:
                messages.error(request, f'Error al enviar email de prueba: {e}')
    
    # Estadísticas para mostrar en la vista
    alertas_activas = AlertaInventario.objects.filter(activa=True)
    alertas_por_tipo = {}
    alertas_por_prioridad = {}
    
    for alerta in alertas_activas:
        # Contar por tipo
        tipo = alerta.get_tipo_display()
        alertas_por_tipo[tipo] = alertas_por_tipo.get(tipo, 0) + 1
        
        # Contar por prioridad
        prioridad = alerta.get_prioridad_display()
        alertas_por_prioridad[prioridad] = alertas_por_prioridad.get(prioridad, 0) + 1
    
    context = {
        'total_alertas': alertas_activas.count(),
        'alertas_por_tipo': alertas_por_tipo,
        'alertas_por_prioridad': alertas_por_prioridad,
        'productos_stock_bajo': Producto.objects.filter(
            activo=True,
            stock_actual__lte=F('stock_minimo')
        ).count(),
    }
    
    return render(request, 'inventario/test_notificaciones.html', context)

def enviar_notificacion_email(self):
    """Enviar notificación por email"""
    from django.utils import timezone
    from .utils import enviar_alerta_email
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f'Intentando enviar email para alerta: {self.producto.nombre}')
        
        if enviar_alerta_email(self):
            self.notificado_por_email = True
            self.fecha_ultimo_email = timezone.now()
            self.save()
            logger.info(f'✓ Email enviado exitosamente para: {self.producto.nombre}')
            return True
        else:
            logger.warning(f'❌ No se pudo enviar email para: {self.producto.nombre}')
            return False
            
    except Exception as e:
        logger.error(f'❌ Error al enviar email para {self.producto.nombre}: {e}')
        return False