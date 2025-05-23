# inventario/management/commands/crear_inventario_inicial.py
from django.core.management.base import BaseCommand
from inventario.models import CategoriaProducto, Producto, Proveedor

class Command(BaseCommand):
    help = 'Crea categorías y productos iniciales del inventario'

    def handle(self, *args, **options):
        self.stdout.write('Creando categorías iniciales...')
        
        # Crear categorías
        categorias = [
            {'nombre': 'Aceites y Lubricantes', 'descripcion': 'Aceites para motor, transmisión y otros lubricantes'},
            {'nombre': 'Filtros', 'descripcion': 'Filtros de aceite, aire, combustible y cabina'},
            {'nombre': 'Frenos', 'descripcion': 'Pastillas, discos, líquido de frenos y componentes'},
            {'nombre': 'Suspensión', 'descripcion': 'Amortiguadores, resortes y componentes de suspensión'},
            {'nombre': 'Motor', 'descripcion': 'Repuestos y componentes del motor'},
            {'nombre': 'Transmisión', 'descripcion': 'Componentes de caja de cambios y embrague'},
            {'nombre': 'Eléctrico', 'descripcion': 'Baterías, alternadores, arranques y componentes eléctricos'},
            {'nombre': 'Herramientas', 'descripcion': 'Herramientas de taller y equipos'},
            {'nombre': 'Productos de Limpieza', 'descripcion': 'Champús, ceras, limpiadores para carwash'},
            {'nombre': 'Neumáticos', 'descripcion': 'Llantas y neumáticos'},
        ]
        
        for cat_data in categorias:
            categoria, created = CategoriaProducto.objects.get_or_create(
                nombre=cat_data['nombre'],
                defaults={'descripcion': cat_data['descripcion']}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Categoría "{categoria.nombre}" creada'))
            else:
                self.stdout.write(f'Categoría "{categoria.nombre}" ya existía')
        
        # Crear proveedor genérico
        proveedor_generico, created = Proveedor.objects.get_or_create(
            nombre='Proveedor General',
            defaults={
                'contacto': 'Administrador',
                'telefono': '000-000-0000',
                'email': 'proveedor@example.com',
                'direccion': 'Dirección no especificada',
                'activo': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('Proveedor genérico creado'))
        
        self.stdout.write('Creando productos iniciales...')
        
        # Obtener categorías creadas
        aceites = CategoriaProducto.objects.get(nombre='Aceites y Lubricantes')
        filtros = CategoriaProducto.objects.get(nombre='Filtros')
        frenos = CategoriaProducto.objects.get(nombre='Frenos')
        herramientas = CategoriaProducto.objects.get(nombre='Herramientas')
        limpieza = CategoriaProducto.objects.get(nombre='Productos de Limpieza')
        
        # Crear productos iniciales
        productos = [
            # Aceites y Lubricantes
            {
                'codigo': 'ACE001',
                'nombre': 'Aceite Motor 20W-50 4L',
                'descripcion': 'Aceite mineral para motor 20W-50, presentación 4 litros',
                'tipo': 'CONSUMIBLE',
                'categoria': aceites,
                'precio_compra': 15.00,
                'precio_venta': 22.00,
                'stock_minimo': 20,
                'unidad_medida': 'Litros'
            },
            {
                'codigo': 'ACE002',
                'nombre': 'Aceite Motor 10W-40 Sintético 4L',
                'descripcion': 'Aceite sintético para motor 10W-40, presentación 4 litros',
                'tipo': 'CONSUMIBLE',
                'categoria': aceites,
                'precio_compra': 25.00,
                'precio_venta': 35.00,
                'stock_minimo': 15,
                'unidad_medida': 'Litros'
            },
            {
                'codigo': 'ACE003',
                'nombre': 'Aceite Transmisión ATF',
                'descripcion': 'Aceite para transmisión automática ATF',
                'tipo': 'CONSUMIBLE',
                'categoria': aceites,
                'precio_compra': 8.00,
                'precio_venta': 12.00,
                'stock_minimo': 10,
                'unidad_medida': 'Litros'
            },
            
            # Filtros
            {
                'codigo': 'FIL001',
                'nombre': 'Filtro de Aceite Universal',
                'descripcion': 'Filtro de aceite universal para motores',
                'tipo': 'REPUESTO',
                'categoria': filtros,
                'precio_compra': 3.50,
                'precio_venta': 6.00,
                'stock_minimo': 50,
                'unidad_medida': 'Unidad'
            },
            {
                'codigo': 'FIL002',
                'nombre': 'Filtro de Aire Universal',
                'descripcion': 'Filtro de aire universal para motores',
                'tipo': 'REPUESTO',
                'categoria': filtros,
                'precio_compra': 5.00,
                'precio_venta': 8.50,
                'stock_minimo': 30,
                'unidad_medida': 'Unidad'
            },
            {
                'codigo': 'FIL003',
                'nombre': 'Filtro de Combustible',
                'descripcion': 'Filtro de combustible universal',
                'tipo': 'REPUESTO',
                'categoria': filtros,
                'precio_compra': 4.00,
                'precio_venta': 7.00,
                'stock_minimo': 25,
                'unidad_medida': 'Unidad'
            },
            
            # Frenos
            {
                'codigo': 'FRE001',
                'nombre': 'Pastillas de Freno Delanteras',
                'descripcion': 'Juego de pastillas de freno delanteras',
                'tipo': 'REPUESTO',
                'categoria': frenos,
                'precio_compra': 25.00,
                'precio_venta': 40.00,
                'stock_minimo': 20,
                'unidad_medida': 'Juego'
            },
            {
                'codigo': 'FRE002',
                'nombre': 'Pastillas de Freno Traseras',
                'descripcion': 'Juego de pastillas de freno traseras',
                'tipo': 'REPUESTO',
                'categoria': frenos,
                'precio_compra': 20.00,
                'precio_venta': 32.00,
                'stock_minimo': 20,
                'unidad_medida': 'Juego'
            },
            {
                'codigo': 'FRE003',
                'nombre': 'Líquido de Frenos DOT 3',
                'descripcion': 'Líquido de frenos DOT 3, botella 500ml',
                'tipo': 'CONSUMIBLE',
                'categoria': frenos,
                'precio_compra': 3.00,
                'precio_venta': 5.50,
                'stock_minimo': 15,
                'unidad_medida': 'Botella'
            },
            
            # Herramientas
            {
                'codigo': 'HER001',
                'nombre': 'Llave de Tubo 10mm',
                'descripcion': 'Llave de tubo 10mm',
                'tipo': 'HERRAMIENTA',
                'categoria': herramientas,
                'precio_compra': 5.00,
                'precio_venta': 8.00,
                'stock_minimo': 5,
                'unidad_medida': 'Unidad'
            },
            {
                'codigo': 'HER002',
                'nombre': 'Destornillador Plano',
                'descripcion': 'Destornillador plano mediano',
                'tipo': 'HERRAMIENTA',
                'categoria': herramientas,
                'precio_compra': 3.00,
                'precio_venta': 5.00,
                'stock_minimo': 10,
                'unidad_medida': 'Unidad'
            },
            
            # Productos de Limpieza
            {
                'codigo': 'LIM001',
                'nombre': 'Champú para Auto 1L',
                'descripcion': 'Champú concentrado para lavado de autos',
                'tipo': 'CONSUMIBLE',
                'categoria': limpieza,
                'precio_compra': 4.00,
                'precio_venta': 7.00,
                'stock_minimo': 20,
                'unidad_medida': 'Litros'
            },
            {
                'codigo': 'LIM002',
                'nombre': 'Cera Liquida 500ml',
                'descripcion': 'Cera líquida para protección de carrocería',
                'tipo': 'CONSUMIBLE',
                'categoria': limpieza,
                'precio_compra': 6.00,
                'precio_venta': 10.00,
                'stock_minimo': 15,
                'unidad_medida': 'Botella'
            },
            {
                'codigo': 'LIM003',
                'nombre': 'Limpiador de Llantas 500ml',
                'descripcion': 'Limpiador especializado para llantas y rines',
                'tipo': 'CONSUMIBLE',
                'categoria': limpieza,
                'precio_compra': 3.50,
                'precio_venta': 6.00,
                'stock_minimo': 10,
                'unidad_medida': 'Botella'
            },
        ]
        
        for prod_data in productos:
            producto, created = Producto.objects.get_or_create(
                codigo=prod_data['codigo'],
                defaults={
                    'nombre': prod_data['nombre'],
                    'descripcion': prod_data['descripcion'],
                    'tipo': prod_data['tipo'],
                    'categoria': prod_data['categoria'],
                    'proveedor_principal': proveedor_generico,
                    'precio_compra': prod_data['precio_compra'],
                    'precio_venta': prod_data['precio_venta'],
                    'stock_minimo': prod_data['stock_minimo'],
                    'stock_actual': 0,
                    'unidad_medida': prod_data['unidad_medida'],
                    'activo': True
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Producto "{producto.nombre}" creado'))
            else:
                self.stdout.write(f'Producto "{producto.nombre}" ya existía')
        
        self.stdout.write(self.style.SUCCESS('Inventario inicial creado exitosamente.'))