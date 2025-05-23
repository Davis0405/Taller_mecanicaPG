# inventario/utils.py
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.contrib.auth.models import User
from usuarios.models import Perfil
import logging

logger = logging.getLogger(__name__)

def obtener_usuarios_notificacion():
    """Obtener usuarios que deben recibir notificaciones de inventario"""
    try:
        # Usuarios con roles de Administrador y Mecánico
        perfiles_notificar = Perfil.objects.filter(
            rol__nombre__in=['Administrador', 'Mecánico'],
            usuario__is_active=True,
            usuario__email__isnull=False
        ).exclude(usuario__email='')
        
        usuarios = [perfil.usuario for perfil in perfiles_notificar if perfil.usuario.email]
        
        # Agregar superusuarios que tengan email
        superusuarios = User.objects.filter(
            is_superuser=True,
            is_active=True,
            email__isnull=False
        ).exclude(email='')
        
        # Combinar y eliminar duplicados
        todos_usuarios = list(set(usuarios + list(superusuarios)))
        
        return todos_usuarios
    except Exception as e:
        logger.error(f"Error al obtener usuarios para notificación: {e}")
        return []

def enviar_alerta_email(alerta):
    """Enviar email de alerta de inventario"""
    try:
        usuarios_destinatarios = obtener_usuarios_notificacion()
        
        if not usuarios_destinatarios:
            logger.warning("No hay usuarios configurados para recibir alertas de inventario")
            return False
        
        emails_destinatarios = [usuario.email for usuario in usuarios_destinatarios]
        
        # Determinar el color y emoji según el tipo de alerta
        if alerta.tipo == 'STOCK_AGOTADO':
            color = '#dc3545'  # Rojo
            emoji = '🚨'
            urgencia = 'URGENTE'
        elif alerta.tipo == 'STOCK_CRITICO':
            color = '#fd7e14'  # Naranja
            emoji = '⚠️'
            urgencia = 'CRÍTICO'
        elif alerta.tipo == 'STOCK_BAJO':
            color = '#ffc107'  # Amarillo
            emoji = '📉'
            urgencia = 'ATENCIÓN'
        else:
            color = '#17a2b8'  # Azul
            emoji = '📦'
            urgencia = 'INFORMACIÓN'
        
        asunto = f"{emoji} {urgencia}: {alerta.get_tipo_display()} - {alerta.producto.nombre}"
        
        mensaje_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background-color: {color}; color: white; padding: 15px; border-radius: 5px 5px 0 0;">
                    <h2 style="margin: 0; color: white;">
                        {emoji} Alerta de Inventario - {urgencia}
                    </h2>
                </div>
                
                <div style="background-color: #f8f9fa; padding: 20px; border: 1px solid #ddd; border-top: none; border-radius: 0 0 5px 5px;">
                    <h3 style="color: {color}; margin-top: 0;">
                        {alerta.get_tipo_display()}: {alerta.producto.nombre}
                    </h3>
                    
                    <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
                        <tr>
                            <td style="padding: 8px 0; border-bottom: 1px solid #ddd;"><strong>Producto:</strong></td>
                            <td style="padding: 8px 0; border-bottom: 1px solid #ddd;">{alerta.producto.codigo} - {alerta.producto.nombre}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; border-bottom: 1px solid #ddd;"><strong>Stock Actual:</strong></td>
                            <td style="padding: 8px 0; border-bottom: 1px solid #ddd;">
                                <span style="background-color: {color}; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">
                                    {alerta.producto.stock_actual}
                                </span>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; border-bottom: 1px solid #ddd;"><strong>Stock Mínimo:</strong></td>
                            <td style="padding: 8px 0; border-bottom: 1px solid #ddd;">{alerta.producto.stock_minimo}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; border-bottom: 1px solid #ddd;"><strong>Categoría:</strong></td>
                            <td style="padding: 8px 0; border-bottom: 1px solid #ddd;">{alerta.producto.categoria.nombre if alerta.producto.categoria else 'Sin categoría'}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; border-bottom: 1px solid #ddd;"><strong>Proveedor:</strong></td>
                            <td style="padding: 8px 0; border-bottom: 1px solid #ddd;">{alerta.producto.proveedor_principal.nombre if alerta.producto.proveedor_principal else 'No asignado'}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0;"><strong>Prioridad:</strong></td>
                            <td style="padding: 8px 0;">
                                <span style="background-color: {'#dc3545' if alerta.prioridad == 'CRITICA' else '#ffc107' if alerta.prioridad == 'ALTA' else '#28a745'}; 
                                             color: white; padding: 3px 8px; border-radius: 3px; font-size: 12px;">
                                    {alerta.get_prioridad_display()}
                                </span>
                            </td>
                        </tr>
                    </table>
                    
                    <div style="background-color: white; border-left: 4px solid {color}; padding: 15px; margin: 20px 0;">
                        <p style="margin: 0;"><strong>Mensaje:</strong></p>
                        <p style="margin: 5px 0 0 0;">{alerta.mensaje}</p>
                    </div>
                    
                    <div style="background-color: #e8f5e8; border: 1px solid #4caf50; padding: 15px; margin: 20px 0; border-radius: 5px;">
                        <p style="margin: 0;"><strong>Acciones recomendadas:</strong></p>
                        <ul style="margin: 5px 0 0 20px;">
                            <li>Revisar el inventario físico</li>
                            <li>Contactar al proveedor para reposición</li>
                            <li>Considerar compras de emergencia si es crítico</li>
                            <li>Actualizar los niveles de stock mínimo si es necesario</li>
                        </ul>
                    </div>
                    
                    <div style="text-align: center; margin-top: 30px;">
                        <p style="color: #666; font-size: 12px;">
                            Alerta generada automáticamente el {alerta.fecha_creacion.strftime('%d/%m/%Y a las %H:%M')}<br>
                            Sistema de Gestión de Taller Mecánico
                        </p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        mensaje_texto = f"""
ALERTA DE INVENTARIO - {urgencia}

{alerta.get_tipo_display()}: {alerta.producto.nombre}

Detalles del Producto:
- Código: {alerta.producto.codigo}
- Nombre: {alerta.producto.nombre}
- Stock Actual: {alerta.producto.stock_actual}
- Stock Mínimo: {alerta.producto.stock_minimo}
- Categoría: {alerta.producto.categoria.nombre if alerta.producto.categoria else 'Sin categoría'}
- Proveedor: {alerta.producto.proveedor_principal.nombre if alerta.producto.proveedor_principal else 'No asignado'}
- Prioridad: {alerta.get_prioridad_display()}

Mensaje: {alerta.mensaje}

Acciones recomendadas:
- Revisar el inventario físico
- Contactar al proveedor para reposición
- Considerar compras de emergencia si es crítico
- Actualizar los niveles de stock mínimo si es necesario

Alerta generada automáticamente el {alerta.fecha_creacion.strftime('%d/%m/%Y a las %H:%M')}
Sistema de Gestión de Taller Mecánico
        """.strip()
        
        # Crear y enviar email
        email = EmailMultiAlternatives(
            asunto,
            mensaje_texto,
            settings.EMAIL_HOST_USER,
            emails_destinatarios
        )
        email.attach_alternative(mensaje_html, "text/html")
        email.send()
        
        logger.info(f"Alerta enviada por email: {alerta.producto.nombre} a {len(emails_destinatarios)} destinatarios")
        return True
        
    except Exception as e:
        logger.error(f"Error al enviar email de alerta: {e}")
        return False

def enviar_resumen_alertas_diario():
    """Enviar resumen diario de alertas activas"""
    from .models import AlertaInventario
    from django.utils import timezone
    
    try:
        alertas_activas = AlertaInventario.objects.filter(activa=True).order_by('-prioridad', '-fecha_creacion')
        
        if not alertas_activas:
            return True  # No hay alertas, no enviar resumen
        
        usuarios_destinatarios = obtener_usuarios_notificacion()
        if not usuarios_destinatarios:
            return False
        
        emails_destinatarios = [usuario.email for usuario in usuarios_destinatarios]
        
        # Contar alertas por tipo
        alertas_por_tipo = {}
        for alerta in alertas_activas:
            tipo = alerta.get_tipo_display()
            if tipo not in alertas_por_tipo:
                alertas_por_tipo[tipo] = 0
            alertas_por_tipo[tipo] += 1
        
        asunto = f"📊 Resumen Diario de Alertas de Inventario - {timezone.now().strftime('%d/%m/%Y')}"
        
        # Crear tabla HTML de alertas
        tabla_alertas = ""
        for alerta in alertas_activas:
            color_prioridad = {
                'CRITICA': '#dc3545',
                'ALTA': '#fd7e14', 
                'MEDIA': '#ffc107',
                'BAJA': '#28a745'
            }.get(alerta.prioridad, '#6c757d')
            
            tabla_alertas += f"""
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;">{alerta.producto.codigo}</td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;">{alerta.producto.nombre}</td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: center;">
                    <span style="background-color: {color_prioridad}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">
                        {alerta.get_prioridad_display()}
                    </span>
                </td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: center;">{alerta.producto.stock_actual}</td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;">{alerta.get_tipo_display()}</td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd; font-size: 11px;">{alerta.fecha_creacion.strftime('%d/%m %H:%M')}</td>
            </tr>
            """
        
        mensaje_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 800px; margin: 0 auto; padding: 20px;">
                <div style="background-color: #343a40; color: white; padding: 20px; border-radius: 5px 5px 0 0;">
                    <h2 style="margin: 0; color: white;">
                        📊 Resumen Diario de Alertas de Inventario
                    </h2>
                    <p style="margin: 5px 0 0 0; opacity: 0.8;">
                        {timezone.now().strftime('%A, %d de %B de %Y')}
                    </p>
                </div>
                
                <div style="background-color: #f8f9fa; padding: 20px; border: 1px solid #ddd; border-top: none;">
                    <h3 style="color: #343a40; margin-top: 0;">Resumen de Alertas Activas</h3>
                    
                    <div style="display: flex; justify-content: space-between; margin-bottom: 20px;">
                        <div style="text-align: center; padding: 15px; background-color: white; border-radius: 5px; min-width: 100px;">
                            <h4 style="margin: 0; color: #dc3545; font-size: 24px;">{alertas_activas.count()}</h4>
                            <p style="margin: 5px 0 0 0; color: #666; font-size: 12px;">TOTAL ALERTAS</p>
                        </div>
                    </div>
                    
                    <h4>Desglose por Tipo:</h4>
                    <ul>
                        {' '.join([f"<li><strong>{tipo}:</strong> {cantidad}</li>" for tipo, cantidad in alertas_por_tipo.items()])}
                    </ul>
                    
                    <h4>Detalle de Alertas:</h4>
                    <table style="width: 100%; border-collapse: collapse; background-color: white;">
                        <thead>
                            <tr style="background-color: #343a40; color: white;">
                                <th style="padding: 10px; text-align: left;">Código</th>
                                <th style="padding: 10px; text-align: left;">Producto</th>
                                <th style="padding: 10px; text-align: center;">Prioridad</th>
                                <th style="padding: 10px; text-align: center;">Stock</th>
                                <th style="padding: 10px; text-align: left;">Tipo</th>
                                <th style="padding: 10px; text-align: left;">Fecha</th>
                            </tr>
                        </thead>
                        <tbody>
                            {tabla_alertas}
                        </tbody>
                    </table>
                    
                    <div style="background-color: #e8f5e8; border: 1px solid #4caf50; padding: 15px; margin: 20px 0; border-radius: 5px;">
                        <p style="margin: 0;"><strong>💡 Recomendaciones:</strong></p>
                        <ul style="margin: 5px 0 0 20px;">
                            <li>Revisar y resolver las alertas críticas primero</li>
                            <li>Contactar proveedores para productos agotados</li>
                            <li>Realizar inventario físico de productos con alertas</li>
                            <li>Considerar ajustar niveles de stock mínimo</li>
                        </ul>
                    </div>
                    
                    <div style="text-align: center; margin-top: 30px;">
                        <p style="color: #666; font-size: 12px;">
                            Resumen generado automáticamente<br>
                            Sistema de Gestión de Taller Mecánico
                        </p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Crear y enviar email
        email = EmailMultiAlternatives(
            asunto,
            f"Resumen diario de alertas de inventario - {alertas_activas.count()} alertas activas",
            settings.EMAIL_HOST_USER,
            emails_destinatarios
        )
        email.attach_alternative(mensaje_html, "text/html")
        email.send()
        
        logger.info(f"Resumen diario de alertas enviado a {len(emails_destinatarios)} destinatarios")
        return True
        
    except Exception as e:
        logger.error(f"Error al enviar resumen diario de alertas: {e}")
        return False