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

class Mesa(models.Model):
    id = models.AutoField(primary_key=True)
    restaurante = models.ForeignKey(Restaurante, on_delete=models.CASCADE, related_name='mesas')
    numero_mesa = models.PositiveIntegerField()
    disponibilidad = models.BooleanField(default=True)  # Indica si la mesa está disponible
    capacidad = models.PositiveIntegerField(default=4, blank=True, null=True)  # Capacidad máxima de la mesa
    descripcion = models.CharField(max_length=255, blank=True, null=True)  # Descripción de la mesa

    class Meta:
        unique_together = ('restaurante', 'numero_mesa')  # Asegura que el mismo número de mesa no se repita en el mismo restaurante

    def __str__(self):
        return f"Mesa {self.numero_mesa} - {self.restaurante.nombre}"


class Barra(models.Model):
    id = models.AutoField(primary_key=True)
    restaurante = models.ForeignKey(Restaurante, on_delete=models.CASCADE, related_name='barras')
    numero_barra = models.PositiveIntegerField()
    capacidad = models.PositiveIntegerField(default=5, blank=True, null=True)  # Capacidad de la barra
    disponibilidad = models.BooleanField(default=True)  # Indica si la barra está disponible

    class Meta:
        unique_together = ('restaurante', 'numero_barra')  # Asegura que el mismo número de barra no se repita en el mismo restaurante

    def __str__(self):
        return f"Barra {self.numero_barra} - {self.restaurante.nombre}"


class Platillo(models.Model):
    id = models.AutoField(primary_key=True)
    restaurante = models.ForeignKey(Restaurante, on_delete=models.CASCADE, related_name='platillos')
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    disponible = models.BooleanField(default=True)  # Indica si el platillo está disponible

    def __str__(self):
        return self.nombre


class Bebida(models.Model):
    id = models.AutoField(primary_key=True)
    restaurante = models.ForeignKey(Restaurante, on_delete=models.CASCADE, related_name='bebidas')
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    disponible = models.BooleanField(default=True)  # Indica si la bebida está disponible

    def __str__(self):
        return self.nombre
    
class Pedido(models.Model):
    id = models.AutoField(primary_key=True)
    restaurante = models.ForeignKey(Restaurante, on_delete=models.CASCADE)
    mesa = models.ForeignKey(Mesa, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=50, choices=[('barra', 'Barra'), ('cocina', 'Cocina')])
    estado = models.CharField(max_length=50, choices=[('pendiente', 'Pendiente'), ('en_proceso', 'En Proceso'), ('completado', 'Completado')], default='pendiente')
    platillo = models.ForeignKey(Platillo, null=True, blank=True, on_delete=models.SET_NULL)
    bebida = models.ForeignKey(Bebida, null=True, blank=True, on_delete=models.SET_NULL)
    cantidad = models.PositiveIntegerField(default=1)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Pedido {self.id} - Mesa {self.mesa.numero_mesa}"

class Notificacion(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE)
    mensaje = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)
    enviado_a = models.CharField(max_length=50, choices=[('cocina', 'Cocina'), ('barra', 'Barra')])

    def __str__(self):
        return f"Notificación {self.id} - {self.enviado_a}"
