# inventario/management/commands/generar_alertas_inventario.py
from django.core.management.base import BaseCommand
from inventario.models import Producto, AlertaInventario
from django.db.models import F
from django.utils import timezone
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('alertas_inventario.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class Command(BaseCommand):
    help = 'Genera alertas automáticas para productos con stock bajo y envía emails'

    def add_arguments(self, parser):
        parser.add_argument(
            '--enviar-email',
            action='store_true',
            help='Enviar notificaciones por email para nuevas alertas (por defecto: True)'
        )
        parser.add_argument(
            '--no-email',
            action='store_true',
            help='NO enviar emails, solo generar alertas'
        )
        parser.add_argument(
            '--resumen-diario',
            action='store_true',
            help='Enviar resumen diario de todas las alertas activas'
        )
        parser.add_argument(
            '--forzar-email',
            action='store_true',
            help='Enviar emails incluso para alertas existentes'
        )

    def handle(self, *args, **options):
        logger = logging.getLogger(__name__)
        
        logger.info('Iniciando generación de alertas de inventario...')
        
        # Por defecto enviar emails, a menos que se especifique --no-email
        enviar_emails = not options['no_email']
        if options['enviar_email']:
            enviar_emails = True
            
        resumen_diario = options['resumen_diario']
        forzar_email = options['forzar_email']
        
        logger.info(f'Configuración: Enviar emails: {enviar_emails}, Resumen diario: {resumen_diario}, Forzar email: {forzar_email}')
        
        # 1. Limpiar alertas antiguas que ya no aplican
        alertas_resueltas = self.limpiar_alertas_resueltas(logger)
        
        # 2. Generar nuevas alertas
        alertas_nuevas, emails_enviados = self.generar_nuevas_alertas(logger, enviar_emails, forzar_email)
        
        # 3. Enviar resumen diario si se solicita
        if resumen_diario:
            self.enviar_resumen_diario(logger)
        
        # Resumen final
        logger.info('='*60)
        logger.info(f'✓ Alertas nuevas: {alertas_nuevas}')
        logger.info(f'✓ Alertas resueltas: {alertas_resueltas}')
        logger.info(f'✓ Emails enviados: {emails_enviados}')
        logger.info('='*60)
        
        self.stdout.write(self.style.SUCCESS(f'Proceso completado: {alertas_nuevas} nuevas alertas, {emails_enviados} emails enviados'))

    def limpiar_alertas_resueltas(self, logger):
        """Marcar como resueltas las alertas que ya no aplican"""
        # Productos que ya no tienen stock bajo
        productos_con_stock_ok = Producto.objects.filter(
            activo=True,
            stock_actual__gt=F('stock_minimo')
        )
        
        alertas_a_resolver = AlertaInventario.objects.filter(
            producto__in=productos_con_stock_ok,
            activa=True,
            tipo__in=['STOCK_BAJO', 'STOCK_CRITICO', 'STOCK_AGOTADO']
        )
        
        count = 0
        for alerta in alertas_a_resolver:
            alerta.marcar_como_resuelta()
            count += 1
            logger.info(f'✓ Alerta resuelta automáticamente: {alerta.producto.nombre}')
        
        if count > 0:
            logger.info(f'{count} alertas marcadas como resueltas')
        
        return count

    def generar_nuevas_alertas(self, logger, enviar_emails, forzar_email):
        """Generar nuevas alertas para productos con problemas de stock"""
        alertas_creadas = 0
        emails_enviados = 0
        
        # Productos activos con problemas de stock
        productos_problema = Producto.objects.filter(
            activo=True,
            stock_actual__lte=F('stock_minimo')
        ).order_by('stock_actual')  # Procesar primero los más críticos
        
        logger.info(f'Encontrados {productos_problema.count()} productos con stock bajo o agotado')
        
        for producto in productos_problema:
            # Determinar tipo y prioridad de alerta
            if producto.stock_actual == 0:
                tipo_alerta = 'STOCK_AGOTADO'
                prioridad = 'CRITICA'
                mensaje = f'🚨 CRÍTICO: El producto {producto.nombre} (código: {producto.codigo}) está AGOTADO. Stock actual: 0'
                emoji = '🚨'
            elif producto.stock_actual <= (producto.stock_minimo * 0.3):  # 30% del stock mínimo
                tipo_alerta = 'STOCK_CRITICO'
                prioridad = 'ALTA'
                mensaje = f'⚠️ URGENTE: El producto {producto.nombre} (código: {producto.codigo}) tiene stock CRÍTICO: {producto.stock_actual} unidades (mínimo: {producto.stock_minimo})'
                emoji = '⚠️'
            else:
                tipo_alerta = 'STOCK_BAJO'
                prioridad = 'MEDIA'
                mensaje = f'📉 ATENCIÓN: El producto {producto.nombre} (código: {producto.codigo}) tiene stock bajo: {producto.stock_actual} unidades (mínimo: {producto.stock_minimo})'
                emoji = '📉'
            
            # Verificar si ya existe una alerta activa para este producto y tipo
            alerta_existente = AlertaInventario.objects.filter(
                producto=producto,
                tipo=tipo_alerta,
                activa=True
            ).first()
            
            if alerta_existente:
                # Actualizar mensaje y prioridad si es necesario
                if alerta_existente.mensaje != mensaje or alerta_existente.prioridad != prioridad:
                    alerta_existente.mensaje = mensaje
                    alerta_existente.prioridad = prioridad
                    alerta_existente.save()
                    logger.info(f'📝 Alerta actualizada: {producto.nombre}')
                
                # Enviar email si se fuerza o si es crítica y no se ha enviado
                if forzar_email or (tipo_alerta in ['STOCK_AGOTADO', 'STOCK_CRITICO'] and not alerta_existente.notificado_por_email):
                    if enviar_emails:
                        try:
                            if alerta_existente.enviar_notificacion_email():
                                emails_enviados += 1
                                logger.info(f'📧 Email enviado para alerta existente: {producto.nombre}')
                            else:
                                logger.warning(f'❌ No se pudo enviar email para: {producto.nombre}')
                        except Exception as e:
                            logger.error(f'❌ Error al enviar email para {producto.nombre}: {e}')
                continue
            
            # Crear nueva alerta
            try:
                alerta = AlertaInventario.objects.create(
                    producto=producto,
                    tipo=tipo_alerta,
                    prioridad=prioridad,
                    mensaje=mensaje,
                    activa=True
                )
                
                alertas_creadas += 1
                logger.info(f'{emoji} Nueva alerta creada: {tipo_alerta} para {producto.nombre}')
                
                # Enviar email para nueva alerta
                if enviar_emails:
                    try:
                        if alerta.enviar_notificacion_email():
                            emails_enviados += 1
                            logger.info(f'📧 Email enviado para nueva alerta: {producto.nombre}')
                        else:
                            logger.warning(f'❌ No se pudo enviar email para: {producto.nombre}')
                    except Exception as e:
                        logger.error(f'❌ Error al enviar email para {producto.nombre}: {e}')
                        
            except Exception as e:
                logger.error(f'❌ Error al crear alerta para {producto.nombre}: {e}')
        
        return alertas_creadas, emails_enviados

    def enviar_resumen_diario(self, logger):
        """Enviar resumen diario de alertas"""
        try:
            from inventario.utils import enviar_resumen_alertas_diario
            
            if enviar_resumen_alertas_diario():
                logger.info('📊 Resumen diario de alertas enviado correctamente')
            else:
                logger.warning('❌ No se pudo enviar el resumen diario de alertas')
                
        except Exception as e:
            logger.error(f'❌ Error al enviar resumen diario: {e}')