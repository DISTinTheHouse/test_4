from channels.generic.websocket import AsyncWebsocketConsumer
import json

class PedidoConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("pedidos", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("pedidos", self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        await self.channel_layer.group_send(
            "pedidos",
            {
                "type": "enviar_pedido",
                "pedido": data["pedido"]
            }
        )

    async def enviar_pedido(self, event):
        await self.send(text_data=json.dumps({
            "pedido": event["pedido"]
        }))
