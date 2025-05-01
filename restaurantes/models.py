import uuid
from django.utils.text import slugify
from django.db import models
from usuarios.models import PerfilUsuario

class Restaurante(models.Model):
    id = models.AutoField(primary_key=True)
    socio = models.ForeignKey(PerfilUsuario, on_delete=models.CASCADE, related_name='restaurantes')
    nombre = models.CharField(max_length=255)
    slug = models.SlugField(max_length=300, unique=True, blank=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            uid = str(uuid.uuid4())[:6]
            self.slug = slugify(f"{uid}-{self.nombre}")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre
