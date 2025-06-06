from django.urls import re_path
from . import consumer

websocket_urlpatterns = [
    re_path(r'ws/pedidos/$', consumer.PedidoConsumer.as_asgi()),
]
