# notificaciones/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime, date, timedelta
from citas.models import Cita, Notificacion
from inventario.models import AlertaInventario
from usuarios.models import Perfil
from django.contrib.auth.models import User

def es_admin_notificaciones(user):
    """Verificar si el usuario puede gestionar notificaciones"""
    if not user.is_authenticated:
        return False
    try:
        perfil = Perfil.objects.get(usuario=user)
        return perfil.rol and perfil.rol.nombre in ['Administrador']
    except (Perfil.DoesNotExist, AttributeError):
        return user.is_superuser

@login_required
def dashboard_notificaciones(request):
    """Dashboard del sistema de notificaciones"""
    if not es_admin_notificaciones(request.user):
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('dashboard')
    
    # Estadísticas generales
    stats = {
        'notificaciones_hoy': Notificacion.objects.filter(
            fecha_envio__date=date.today()
        ).count(),
        'emails_enviados_semana': Notificacion.objects.filter(
            fecha_envio__gte=date.today() - timedelta(days=7),
            enviado=True
        ).count(),
        'alertas_inventario_activas': AlertaInventario.objects.filter(activa=True).count(),
        'recordatorios_pendientes': obtener_recordatorios_pendientes().count(),
    }
    
    # Últimas notificaciones
    ultimas_notificaciones = Notificacion.objects.select_related(
        'cita', 'cita__cliente'
    ).order_by('-fecha_envio')[:10]
    
    # Alertas de inventario recientes
    alertas_recientes = AlertaInventario.objects.filter(
        activa=True
    ).select_related('producto').order_by('-fecha_creacion')[:5]
    
    context = {
        'stats': stats,
        'ultimas_notificaciones': ultimas_notificaciones,
        'alertas_recientes': alertas_recientes,
    }
    
    return render(request, 'notificaciones/dashboard.html', context)

@login_required
def configuracion_notificaciones(request):
    """Configuración del sistema de notificaciones"""
    if not es_admin_notificaciones(request.user):
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        # Guardar configuraciones
        config = {
            'recordatorios_automaticos': request.POST.get('recordatorios_automaticos') == 'on',
            'alertas_inventario': request.POST.get('alertas_inventario') == 'on',
            'dias_anticipo_recordatorio': int(request.POST.get('dias_anticipo_recordatorio', 1)),
            'hora_envio_recordatorios': request.POST.get('hora_envio_recordatorios', '09:00'),
            'emails_destino_inventario': request.POST.get('emails_destino_inventario', '').split(','),
        }
        
        # Aquí guardarías la configuración en la base de datos o archivo
        # Por simplicidad, usaremos mensajes para mostrar que se guardó
        
        messages.success(request, 'Configuración guardada correctamente.')
        return redirect('configuracion_notificaciones')
    
    # Configuración actual (simulada)
    config_actual = {
        'recordatorios_automaticos': True,
        'alertas_inventario': True,
        'dias_anticipo_recordatorio': 1,
        'hora_envio_recordatorios': '09:00',
        'emails_destino_inventario': 'admin@tallermecánico.gt, mecanico@tallermecánico.gt',
    }
    
    return render(request, 'notificaciones/configuracion.html', {
        'config': config_actual
    })

@login_required
def historial_notificaciones(request):
    """Historial completo de notificaciones"""
    if not es_admin_notificaciones(request.user):
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('dashboard')
    
    # Filtros
    tipo = request.GET.get('tipo')
    estado = request.GET.get('estado')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    notificaciones = Notificacion.objects.select_related(
        'cita', 'cita__cliente'
    ).order_by('-fecha_envio')
    
    if tipo:
        notificaciones = notificaciones.filter(tipo=tipo)
    
    if estado == 'enviado':
        notificaciones = notificaciones.filter(enviado=True)
    elif estado == 'pendiente':
        notificaciones = notificaciones.filter(enviado=False)
    
    if fecha_inicio:
        notificaciones = notificaciones.filter(fecha_envio__gte=fecha_inicio)
    if fecha_fin:
        notificaciones = notificaciones.filter(fecha_envio__lte=fecha_fin)
    
    context = {
        'notificaciones': notificaciones,
        'tipos_notificacion': Notificacion.TIPOS,
        'filtros': {
            'tipo': tipo,
            'estado': estado,
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
        }
    }
    
    return render(request, 'notificaciones/historial.html', context)

@login_required
def enviar_recordatorios_manual(request):
    """Envío manual de recordatorios"""
    if not es_admin_notificaciones(request.user):
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    if request.method == 'POST':
        fecha_citas = request.POST.get('fecha_citas')
        
        try:
            fecha_obj = datetime.strptime(fecha_citas, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'error': 'Fecha inválida'}, status=400)
        
        # Obtener citas para esa fecha
        citas = Cita.objects.filter(
            fecha=fecha_obj,
            estado__in=['PENDIENTE', 'CONFIRMADA']
        )
        
        enviados = 0
        errores = 0
        
        for cita in citas:
            try:
                # Verificar si ya se envió recordatorio
                if not Notificacion.objects.filter(
                    cita=cita,
                    tipo='RECORDATORIO'
                ).exists():
                    
                    # Enviar email usando el sistema existente
                    from citas.utils import enviar_email_cita
                    
                    if cita.cliente.email and enviar_email_cita(cita, 'recordatorio'):
                        Notificacion.objects.create(
                            cita=cita,
                            tipo='RECORDATORIO',
                            mensaje=f'Recordatorio enviado a {cita.cliente.email}',
                            enviado=True
                        )
                        enviados += 1
                    else:
                        errores += 1
                        
            except Exception as e:
                errores += 1
        
        return JsonResponse({
            'success': True,
            'enviados': enviados,
            'errores': errores,
            'mensaje': f'Recordatorios procesados: {enviados} enviados, {errores} errores'
        })
    
    # GET: Mostrar formulario
    # Obtener fechas con citas próximas
    fechas_con_citas = Cita.objects.filter(
        fecha__gte=date.today(),
        estado__in=['PENDIENTE', 'CONFIRMADA']
    ).values_list('fecha', flat=True).distinct().order_by('fecha')
    
    return render(request, 'notificaciones/enviar_recordatorios.html', {
        'fechas_con_citas': fechas_con_citas
    })

@login_required
def test_configuracion_email(request):
    """Probar configuración de email"""
    if not es_admin_notificaciones(request.user):
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    try:
        # Enviar email de prueba
        send_mail(
            'Prueba de Configuración - Taller Mecánico',
            'Este es un email de prueba para verificar la configuración SMTP.',
            settings.EMAIL_HOST_USER,
            [request.user.email or settings.EMAIL_HOST_USER],
            fail_silently=False,
        )
        
        return JsonResponse({
            'success': True,
            'mensaje': 'Email de prueba enviado correctamente.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

def obtener_recordatorios_pendientes():
    """Obtener citas que necesitan recordatorios"""
    mañana = date.today() + timedelta(days=1)
    
    # Citas para mañana sin recordatorio enviado
    citas_sin_recordatorio = Cita.objects.filter(
        fecha=mañana,
        estado__in=['PENDIENTE', 'CONFIRMADA']
    ).exclude(
        notificaciones__tipo='RECORDATORIO'
    )
    
    return citas_sin_recordatorio

@login_required
def alertas_inventario_config(request):
    """Configuración específica de alertas de inventario"""
    if not es_admin_notificaciones(request.user):
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        accion = request.POST.get('accion')
        
        if accion == 'enviar_alertas':
            # Ejecutar comando de generación de alertas
            try:
                from django.core.management import call_command
                call_command('generar_alertas_inventario', enviar_email=True)
                messages.success(request, 'Alertas de inventario generadas y enviadas.')
            except Exception as e:
                messages.error(request, f'Error al generar alertas: {e}')
        
        elif accion == 'enviar_resumen':
            # Enviar resumen diario
            try:
                from inventario.utils import enviar_resumen_alertas_diario
                if enviar_resumen_alertas_diario():
                    messages.success(request, 'Resumen diario enviado correctamente.')
                else:
                    messages.warning(request, 'No se pudo enviar el resumen diario.')
            except Exception as e:
                messages.error(request, f'Error al enviar resumen: {e}')
    
    # Obtener usuarios que reciben notificaciones de inventario
    from inventario.utils import obtener_usuarios_notificacion
    usuarios_notificacion = obtener_usuarios_notificacion()
    
    # Estadísticas de alertas
    alertas_stats = {
        'activas': AlertaInventario.objects.filter(activa=True).count(),
        'criticas': AlertaInventario.objects.filter(
            activa=True, 
            prioridad='CRITICA'
        ).count(),
        'productos_agotados': AlertaInventario.objects.filter(
            activa=True,
            tipo='STOCK_AGOTADO'
        ).count(),
    }
    
    context = {
        'usuarios_notificacion': usuarios_notificacion,
        'alertas_stats': alertas_stats,
    }
    
    return render(request, 'notificaciones/alertas_inventario.html', context)

@login_required
def notificaciones_personales(request):
    """Notificaciones personales del usuario"""
    # Obtener notificaciones relacionadas con las citas del usuario
    mis_notificaciones = Notificacion.objects.filter(
        cita__cliente=request.user
    ).select_related('cita', 'cita__servicio').order_by('-fecha_envio')[:20]
    
    # Marcar notificaciones como leídas (si tuviéramos ese campo)
    
    context = {
        'notificaciones': mis_notificaciones,
    }
    
    return render(request, 'notificaciones/personales.html', context)

@login_required
def configurar_notificaciones_usuario(request):
    """Configuración de notificaciones por usuario"""
    if request.method == 'POST':
        # Guardar preferencias del usuario
        preferencias = {
            'recordatorios_email': request.POST.get('recordatorios_email') == 'on',
            'confirmaciones_email': request.POST.get('confirmaciones_email') == 'on',
            'cambios_estado_email': request.POST.get('cambios_estado_email') == 'on',
        }
        
        # Aquí guardarías en el perfil del usuario o tabla separada
        messages.success(request, 'Preferencias de notificación guardadas.')
        return redirect('configurar_notificaciones_usuario')
    
    # Preferencias actuales (simuladas)
    preferencias = {
        'recordatorios_email': True,
        'confirmaciones_email': True,
        'cambios_estado_email': True,
    }
    
    return render(request, 'notificaciones/configurar_usuario.html', {
        'preferencias': preferencias
    })