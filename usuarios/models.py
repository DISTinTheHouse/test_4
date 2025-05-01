from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class PerfilUsuario(models.Model):
    id = models.AutoField(primary_key=True)
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    
    es_socio = models.BooleanField(default=False)
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    fecha_pago = models.DateTimeField(blank=True, null=True)
    fecha_expiracion = models.DateTimeField(blank=True, null=True)  # <-- AQUI
    cantidad_restaurantes = models.IntegerField(default=0)

    def __str__(self):
        return f"Perfil de {self.usuario.username}"

    def membresia_activa(self):
        """
        Retorna True si la membresía sigue activa (no expirada).
        """
        if self.fecha_expiracion and timezone.now() > self.fecha_expiracion:
            return False
        return self.es_socio
