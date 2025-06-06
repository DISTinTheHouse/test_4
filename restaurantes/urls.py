from django.urls import path
from . import views

urlpatterns = [
    path('ws_test/', views.ws_test, name='ws_test'),
    # qr de mesas:
    path('qr/<slug:slug>/<int:numero_mesa>/', views.qr_mesa, name='qr_mesa'),
    # /-----------
    path('mis/', views.mis_restaurantes, name='mis_restaurantes'),
    path('crear-payment-intent-restaurante/', views.crear_payment_intent_restaurante, name='crear_payment_intent_restaurante'),
    path('dashboard/<slug:slug>/', views.dashboard_restaurante, name='dashboard'),
    # ver restaurantes para clientes
    path('<slug:slug>/', views.detalle_restaurante, name='detalle_restaurante'),
    path('restaurante/<slug:slug>/agendar/', views.agendar_mesa_publico, name='agendar_cita'),
    path('cita/<int:cita_id>/enviar_whatsapp/', views.enviar_confirmacion_whatsapp, name='enviar_whatsapp'),
    path('restaurantes/confirmacion/<int:cita_id>/', views.confirmacion_agenda, name='confirmacion_agenda'),
    # configurar restaurante para socios
    path('configurar_restaurante/<slug:slug>/', views.configurar_restaurante, name='configurar_restaurante'),
    path('r/<slug:slug>/mesa/<int:numero_mesa>/', views.pedido_rapido, name='pedido_rapido'),
    path('dashboard/<str:area>/', views.dashboard_pedidos, name='dashboard_pedidos'),
    path('dashboard/<str:area>/cambiar_estado/<int:pedido_id>/', views.cambiar_estado_pedido, name='cambiar_estado_pedido'),
    # area para el socio ver restaurantes, mesas y pedidos
    path('socio/restaurante/<int:restaurante_id>/mesas/', views.mesas_restaurante, name='mesas_restaurante'),
    # Cocina
    path('dashboard/<slug:slug>/cocina/', views.dashboard_pedidos_cocina, name='dashboard_pedidos_cocina'),
    path('dashboard/<slug:slug>/cocina/cambiar_estado/<int:pedido_id>/', views.cambiar_estado_pedido_cocina, name='cambiar_estado_pedido_cocina'),
    # Barra
    path('dashboard/<slug:slug>/barra/', views.dashboard_pedidos_barra, name='dashboard_pedidos_barra'),
    path('dashboard/<slug:slug>/barra/cambiar_estado/<int:pedido_id>/', views.cambiar_estado_pedido_barra, name='cambiar_estado_pedido_barra'),
    # ticket pdf
    path('<slug:slug>/mesa/<int:numero_mesa>/ticket/', views.generar_ticket_pdf, name='generar_ticket_pdf'),
]
