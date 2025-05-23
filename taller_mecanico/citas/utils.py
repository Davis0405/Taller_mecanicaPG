# citas/utils.py
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
import datetime

def enviar_email_cita(cita, tipo_email, destinatario_email=None):
    """
    Enviar email relacionado con una cita
    tipo_email: 'confirmacion', 'recordatorio', 'cambio_estado'
    """
    if not destinatario_email:
        destinatario_email = cita.cliente.email
    
    if not destinatario_email:
        return False
    
    # Configurar el contenido según el tipo de email
    if tipo_email == 'confirmacion':
        emoji = '✅'
        asunto = f'✅ Confirmación de Cita - {cita.servicio.nombre}'
        titulo = 'Confirmación de Cita'
        mensaje_principal = 'Tu cita ha sido <strong>confirmada exitosamente</strong>.'
        color_principal = '#28a745'  # Verde
        cuando = f"el {cita.fecha.strftime('%A, %d de %B de %Y')} a las {cita.hora_inicio.strftime('%H:%M')}"
        
    elif tipo_email == 'recordatorio':
        emoji = '🔔'
        asunto = f'🔔 Recordatorio de Cita - {cita.servicio.nombre}'
        titulo = 'Recordatorio de Cita'
        
        # Determinar si es hoy o mañana
        dias_diferencia = (cita.fecha - datetime.date.today()).days
        if dias_diferencia == 0:
            cuando_texto = "hoy"
        elif dias_diferencia == 1:
            cuando_texto = "mañana"
        else:
            cuando_texto = f"el {cita.fecha.strftime('%d/%m/%Y')}"
            
        mensaje_principal = f'Te recordamos que tienes una cita programada para <strong>{cuando_texto}</strong>.'
        color_principal = '#ffc107'  # Amarillo
        cuando = f"el {cita.fecha.strftime('%A, %d de %B de %Y')} a las {cita.hora_inicio.strftime('%H:%M')}"
        
    elif tipo_email == 'cambio_estado':
        emoji = '📋'
        asunto = f'📋 Actualización de Cita - {cita.servicio.nombre}'
        titulo = 'Estado de Cita Actualizado'
        mensaje_principal = f'El estado de tu cita ha cambiado a: <strong>{cita.get_estado_display()}</strong>'
        color_principal = '#17a2b8'  # Azul
        cuando = f"el {cita.fecha.strftime('%A, %d de %B de %Y')} a las {cita.hora_inicio.strftime('%H:%M')}"
        
    else:
        return False
    
    # Determinar el color del estado
    color_estado = {
        'PENDIENTE': '#ffc107',
        'CONFIRMADA': '#28a745', 
        'COMPLETADA': '#17a2b8',
        'CANCELADA': '#dc3545'
    }.get(cita.estado, '#6c757d')
    
    mensaje_html = f"""
    <html>
    <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f4f4f4;">
        <div style="max-width: 600px; margin: 20px auto; background-color: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            
            <!-- Header -->
            <div style="background: linear-gradient(135deg, {color_principal}, {color_principal}dd); color: white; padding: 30px 20px; text-align: center;">
                <h1 style="margin: 0; font-size: 28px; font-weight: 300;">
                    {emoji} {titulo}
                </h1>
                <p style="margin: 10px 0 0 0; opacity: 0.9; font-size: 16px;">
                    Taller Mecánico Profesional
                </p>
            </div>
            
            <!-- Content -->
            <div style="padding: 30px;">
                <p style="font-size: 18px; margin-bottom: 25px;">
                    Hola <strong>{cita.cliente.first_name or cita.cliente.username}</strong>,
                </p>
                
                <p style="font-size: 16px; margin-bottom: 30px; color: #555;">
                    {mensaje_principal}
                </p>
                
                <!-- Cita Details Card -->
                <div style="background-color: #f8f9fa; border-radius: 8px; padding: 25px; margin: 25px 0; border-left: 5px solid {color_principal};">
                    <h3 style="margin: 0 0 20px 0; color: {color_principal}; font-size: 20px;">
                        📋 Detalles de la Cita
                    </h3>
                    
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 12px 0; border-bottom: 1px solid #e9ecef; font-weight: 600; color: #495057; width: 40%;">
                                📅 Fecha y Hora:
                            </td>
                            <td style="padding: 12px 0; border-bottom: 1px solid #e9ecef; color: #212529;">
                                {cuando}
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 12px 0; border-bottom: 1px solid #e9ecef; font-weight: 600; color: #495057;">
                                🔧 Servicio:
                            </td>
                            <td style="padding: 12px 0; border-bottom: 1px solid #e9ecef; color: #212529;">
                                {cita.servicio.nombre}
                                <div style="font-size: 14px; color: #6c757d; margin-top: 5px;">
                                    {cita.servicio.get_categoria_display()}
                                </div>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 12px 0; border-bottom: 1px solid #e9ecef; font-weight: 600; color: #495057;">
                                🚗 Vehículo:
                            </td>
                            <td style="padding: 12px 0; border-bottom: 1px solid #e9ecef; color: #212529;">
                                {cita.vehiculo.marca} {cita.vehiculo.modelo} 
                                <span style="background-color: #e9ecef; padding: 2px 8px; border-radius: 12px; font-size: 12px; margin-left: 10px;">
                                    {cita.vehiculo.placa}
                                </span>
                                <div style="font-size: 14px; color: #6c757d; margin-top: 5px;">
                                    {cita.vehiculo.color} • {cita.vehiculo.año}
                                </div>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 12px 0; border-bottom: 1px solid #e9ecef; font-weight: 600; color: #495057;">
                                💰 Precio:
                            </td>
                            <td style="padding: 12px 0; border-bottom: 1px solid #e9ecef; color: #212529;">
                                <span style="font-size: 18px; font-weight: 600; color: {color_principal};">
                                    Q{cita.servicio.precio}
                                </span>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 12px 0; font-weight: 600; color: #495057;">
                                📊 Estado:
                            </td>
                            <td style="padding: 12px 0; color: #212529;">
                                <span style="background-color: {color_estado}; color: white; padding: 6px 12px; border-radius: 20px; font-size: 14px; font-weight: 500;">
                                    {cita.get_estado_display()}
                                </span>
                            </td>
                        </tr>
                    </table>
                </div>
                
                {f'''<div style="background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 8px; padding: 15px; margin: 20px 0;">
                    <h4 style="margin: 0 0 10px 0; color: #856404;">📝 Notas adicionales:</h4>
                    <p style="margin: 0; color: #856404;">{cita.notas}</p>
                </div>''' if cita.notas else ''}
                
                <!-- Info Box -->
                <div style="background: linear-gradient(135deg, #e8f5e8, #d4edda); border-radius: 8px; padding: 20px; margin: 25px 0;">
                    <h4 style="margin: 0 0 15px 0; color: #155724;">ℹ️ Información Importante</h4>
                    <ul style="margin: 0; padding-left: 20px; color: #155724;">
                        <li style="margin-bottom: 8px;">Por favor, llega <strong>15 minutos antes</strong> de tu cita</li>
                        <li style="margin-bottom: 8px;">Trae la <strong>documentación</strong> de tu vehículo</li>
                        <li style="margin-bottom: 8px;">Si necesitas <strong>cancelar o reprogramar</strong>, contáctanos con anticipación</li>
                        <li>Nuestro equipo estará listo para atenderte</li>
                    </ul>
                </div>
                
                <!-- Contact Info -->
                <div style="background-color: #f8f9fa; border-radius: 8px; padding: 20px; margin-top: 30px; text-align: center;">
                    <h4 style="margin: 0 0 15px 0; color: #495057;">📞 ¿Necesitas ayuda?</h4>
                    <p style="margin: 0; color: #6c757d;">
                        Contáctanos si tienes alguna pregunta o necesitas hacer cambios
                    </p>
                    <div style="margin-top: 15px;">
                        <a href="tel:+50212345678" style="color: {color_principal}; text-decoration: none; font-weight: 600; margin-right: 20px;">
                            📞 +502 1234-5678
                        </a>
                        <a href="mailto:info@tallermecánico.gt" style="color: {color_principal}; text-decoration: none; font-weight: 600;">
                            ✉️ info@tallermecánico.gt
                        </a>
                    </div>
                </div>
            </div>
            
            <!-- Footer -->
            <div style="background-color: #343a40; color: white; padding: 20px; text-align: center;">
                <p style="margin: 0 0 10px 0; font-size: 16px; font-weight: 600;">
                    🔧 Taller Mecánico Profesional
                </p>
                <p style="margin: 0; opacity: 0.8; font-size: 14px;">
                    Tu taller de confianza • Servicio de calidad garantizado
                </p>
                <div style="margin-top: 15px; font-size: 12px; opacity: 0.6;">
                    Email generado automáticamente el {datetime.datetime.now().strftime('%d/%m/%Y a las %H:%M')}
                </div>
            </div>
            
        </div>
    </body>
    </html>
    """
    
    # Mensaje de texto alternativo
    mensaje_texto = f"""
🔧 TALLER MECÁNICO PROFESIONAL

{titulo.upper()}

Hola {cita.cliente.first_name or cita.cliente.username},

{mensaje_principal.replace('<strong>', '').replace('</strong>', '')}

DETALLES DE LA CITA:
📅 Fecha: {cita.fecha.strftime('%A, %d de %B de %Y')}
🕐 Hora: {cita.hora_inicio.strftime('%H:%M')} - {cita.hora_fin.strftime('%H:%M')}
🔧 Servicio: {cita.servicio.nombre} ({cita.servicio.get_categoria_display()})
🚗 Vehículo: {cita.vehiculo.marca} {cita.vehiculo.modelo} ({cita.vehiculo.placa})
💰 Precio: Q{cita.servicio.precio}
📊 Estado: {cita.get_estado_display()}

{f"📝 Notas: {cita.notas}" if cita.notas else ""}

INFORMACIÓN IMPORTANTE:
- Por favor, llega 15 minutos antes de tu cita
- Trae la documentación de tu vehículo
- Si necesitas cancelar o reprogramar, contáctanos con anticipación

¿NECESITAS AYUDA?
📞 +502 1234-5678
✉️ info@tallermecánico.gt

¡Te esperamos!

---
Taller Mecánico Profesional
Tu taller de confianza
    """.strip()
    
    try:
        # Crear y enviar email
        email = EmailMultiAlternatives(
            asunto,
            mensaje_texto,
            settings.EMAIL_HOST_USER,
            [destinatario_email]
        )
        email.attach_alternative(mensaje_html, "text/html")
        email.send()
        
        return True
        
    except Exception as e:
        print(f"Error al enviar email: {e}")
        return False