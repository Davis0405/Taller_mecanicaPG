# inventario/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard_inventario, name='dashboard_inventario'),
    
    # Productos
    path('productos/', views.lista_productos, name='lista_productos'),
    path('productos/agregar/', views.agregar_producto, name='agregar_producto'),
    path('productos/<int:producto_id>/', views.detalle_producto, name='detalle_producto'),
    path('productos/<int:producto_id>/editar/', views.editar_producto, name='editar_producto'),
    
    # Movimientos
    path('movimientos/', views.historial_movimientos, name='historial_movimientos'),
    path('movimientos/agregar/', views.agregar_movimiento, name='agregar_movimiento'),
    path('ajustar-inventario/', views.ajustar_inventario, name='ajustar_inventario'),
    
    # Proveedores
    path('proveedores/', views.lista_proveedores, name='lista_proveedores'),
    path('proveedores/agregar/', views.agregar_proveedor, name='agregar_proveedor'),
    path('proveedores/<int:proveedor_id>/editar/', views.editar_proveedor, name='editar_proveedor'),
    
    # Categorías
    path('categorias/', views.lista_categorias, name='lista_categorias'),
    path('categorias/agregar/', views.agregar_categoria, name='agregar_categoria'),
    
    # Reportes
    path('reportes/stock-bajo/', views.reporte_stock_bajo, name='reporte_stock_bajo'),
    path('reportes/valorizado/', views.reporte_valorizado, name='reporte_valorizado'),
    
    # API
    path('api/buscar-productos/', views.api_buscar_productos, name='api_buscar_productos'),
    path('api/stock/<int:producto_id>/', views.api_stock_producto, name='api_stock_producto'),
]