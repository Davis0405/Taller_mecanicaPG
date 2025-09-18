from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_notificaciones, name='dashboard_notificaciones'),
    path('configuracion/', views.configuracion_notificaciones, name='configuracion_notificaciones'),
    path('historial/', views.historial_notificaciones, name='historial_notificaciones'),
    path('recordatorios/', views.enviar_recordatorios_manual, name='enviar_recordatorios_manual'),
    path('test-email/', views.test_configuracion_email, name='test_configuracion_email'),
    path('alertas-inventario/', views.alertas_inventario_config, name='alertas_inventario_config'),
    path('personales/', views.notificaciones_personales, name='notificaciones_personales'),
    path('configurar-usuario/', views.configurar_notificaciones_usuario, name='configurar_notificaciones_usuario'),
]