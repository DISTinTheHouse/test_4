from django.contrib import admin
from .models import PerfilUsuario

@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'es_socio', 'stripe_customer_id', 'fecha_pago', 'cantidad_restaurantes')
    search_fields = ('usuario__username', 'usuario__email')
    list_filter = ('es_socio',)
    ordering = ('usuario__username',)
