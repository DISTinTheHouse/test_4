# Generated by Django 5.0.6 on 2025-05-10 02:46

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('restaurantes', '0002_bebida_platillo_barra_mesa'),
    ]

    operations = [
        migrations.CreateModel(
            name='Pedido',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('tipo', models.CharField(choices=[('barra', 'Barra'), ('cocina', 'Cocina')], max_length=50)),
                ('estado', models.CharField(choices=[('pendiente', 'Pendiente'), ('en_proceso', 'En Proceso'), ('completado', 'Completado')], default='pendiente', max_length=50)),
                ('cantidad', models.PositiveIntegerField(default=1)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('bebida', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='restaurantes.bebida')),
                ('mesa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='restaurantes.mesa')),
                ('platillo', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='restaurantes.platillo')),
                ('restaurante', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='restaurantes.restaurante')),
            ],
        ),
        migrations.CreateModel(
            name='Notificacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mensaje', models.TextField()),
                ('fecha', models.DateTimeField(auto_now_add=True)),
                ('enviado_a', models.CharField(choices=[('cocina', 'Cocina'), ('barra', 'Barra')], max_length=50)),
                ('pedido', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='restaurantes.pedido')),
            ],
        ),
    ]
