# inventario/management/commands/enviar_resumen_inventario.py
from django.core.management.base import BaseCommand
from inventario.utils import enviar_resumen_alertas_diario
import logging

class Command(BaseCommand):
    help = 'Envía resumen diario de alertas de inventario'

    def handle(self, *args, **options):
        logger = logging.getLogger(__name__)
        
        try:
            if enviar_resumen_alertas_diario():
                self.stdout.write(self.style.SUCCESS('Resumen diario enviado correctamente'))
                logger.info('Resumen diario de inventario enviado')
            else:
                self.stdout.write(self.style.WARNING('No se pudo enviar el resumen diario'))
                logger.warning('No se pudo enviar resumen diario de inventario')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))
            logger.error(f'Error al enviar resumen diario: {e}')