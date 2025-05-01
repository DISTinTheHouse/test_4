from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Restaurante
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import stripe
from django.conf import settings
stripe.api_key = settings.STRIPE_SECRET_KEY

@login_required
def mis_restaurantes(request):
    perfil = request.user.perfil

    # Manejar resultado del pago adicional
    extra_pago = request.GET.get('extra_pago')
    if extra_pago == 'exitoso':
        perfil.cantidad_restaurantes += 1
        perfil.save()
        messages.success(request, '✅ Pago recibido. Puedes agregar otro restaurante ahora.')
    elif extra_pago == 'cancelado':
        messages.warning(request, '⚠️ Pago cancelado. No se registró ningún cambio.')

    # Registrar restaurante si tiene membresía activa y aún le quedan disponibles
    if request.method == 'POST' and perfil.membresia_activa():
        nombre = request.POST.get('nombre')
        direccion = request.POST.get('direccion')
        telefono = request.POST.get('telefono')

        if Restaurante.objects.filter(socio=perfil).count() >= perfil.cantidad_restaurantes:
            messages.warning(request, "⚠️ Ya alcanzaste tu límite actual. Paga otra membresía para agregar más.")
        else:
            Restaurante.objects.create(
                socio=perfil,
                nombre=nombre,
                direccion=direccion,
                telefono=telefono
            )
            messages.success(request, "🎉 Restaurante registrado exitosamente.")
            return redirect('mis_restaurantes')

    restaurantes = Restaurante.objects.filter(socio=perfil)

    return render(request, 'restaurantes/mis_restaurantes.html', {
        'perfil': perfil,  # ✅ Agregado para usarlo directo en el template
        'restaurantes': restaurantes,
        'STRIPE_PUBLIC_KEY': settings.STRIPE_PUBLIC_KEY,
    })


@csrf_exempt
def crear_payment_intent_restaurante(request):
    if request.method == 'POST':
        try:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            intent = stripe.PaymentIntent.create(
                amount=40000,  # $400.00 MXN
                currency='mxn',
                metadata={'tipo': 'restaurante_extra'},
                description='Pago por restaurante adicional'
            )
            return JsonResponse({'clientSecret': intent.client_secret})
        except Exception as e:
            return JsonResponse({'error': str(e)})
