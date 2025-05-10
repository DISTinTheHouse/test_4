from django.contrib import admin
from .models import Restaurante, Mesa, Barra, Platillo, Bebida, Pedido, Notificacion
from django.utils.html import format_html

# Configuración para mostrar mejor las relaciones en el admin
class RestauranteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'socio', 'direccion', 'telefono', 'fecha_creacion', 'editar_link')
    search_fields = ('nombre', 'direccion', 'telefono')
    list_filter = ('fecha_creacion', 'socio')
    
    def editar_link(self, obj):
        return format_html('<a href="/admin/restaurantes/restaurante/{}/change/">Editar</a>', obj.pk)
    editar_link.short_description = 'Editar'

class MesaAdmin(admin.ModelAdmin):
    list_display = ('numero_mesa', 'restaurante', 'capacidad', 'disponibilidad')
    search_fields = ('restaurante__nombre', 'numero_mesa')
    list_filter = ('restaurante', 'disponibilidad')

class BarraAdmin(admin.ModelAdmin):
    list_display = ('numero_barra', 'restaurante', 'capacidad', 'disponibilidad')
    search_fields = ('restaurante__nombre', 'numero_barra')
    list_filter = ('restaurante', 'disponibilidad')

class PlatilloAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'restaurante', 'precio', 'disponible')
    search_fields = ('restaurante__nombre', 'nombre')
    list_filter = ('restaurante', 'disponible')

class BebidaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'restaurante', 'precio', 'disponible')
    search_fields = ('restaurante__nombre', 'nombre')
    list_filter = ('restaurante', 'disponible')

class PedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'restaurante', 'mesa', 'tipo', 'estado', 'timestamp')
    search_fields = ('restaurante__nombre', 'mesa__numero_mesa', 'estado')
    list_filter = ('estado', 'tipo', 'restaurante', 'timestamp')

class NotificacionAdmin(admin.ModelAdmin):
    list_display = ('pedido', 'mensaje', 'enviado_a', 'fecha')
    search_fields = ('pedido__id', 'mensaje', 'enviado_a')
    list_filter = ('enviado_a', 'fecha')

# Registro de los modelos en el admin
admin.site.register(Restaurante, RestauranteAdmin)
admin.site.register(Mesa, MesaAdmin)
admin.site.register(Barra, BarraAdmin)
admin.site.register(Platillo, PlatilloAdmin)
admin.site.register(Bebida, BebidaAdmin)
admin.site.register(Pedido, PedidoAdmin)
admin.site.register(Notificacion, NotificacionAdmin)
