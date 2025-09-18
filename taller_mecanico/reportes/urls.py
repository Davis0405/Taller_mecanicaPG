from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_reportes, name='dashboard_reportes'),
    path('citas/', views.reporte_citas, name='reporte_citas'),
    path('inventario/', views.reporte_inventario, name='reporte_inventario'),
    path('ingresos/', views.reporte_ingresos, name='reporte_ingresos'),
    path('exportar/citas/', views.exportar_reporte_citas, name='exportar_reporte_citas'),
    path('api/graficos/', views.api_estadisticas_graficos, name='api_estadisticas_graficos'),
]