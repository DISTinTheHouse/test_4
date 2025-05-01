from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from .models import PerfilUsuario
from django.contrib import messages
import stripe
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
stripe.api_key = settings.STRIPE_SECRET_KEY

# index
def landing(request):
    return render(request, 'usuarios/landing.html')

# registrarse
def registro(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        if password != password2:
            messages.error(request, 'Las contraseñas no coinciden')
            return redirect('registro')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Ese nombre de usuario ya existe')
            return redirect('registro')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Ese correo ya está registrado')
            return redirect('registro')

        user = User.objects.create_user(username=username, email=email, password=password)
        
        # Crear perfil, pero sin membresía activa todavía
        PerfilUsuario.objects.create(usuario=user)

        login(request, user)
        return redirect('perfil')

    return render(request, 'usuarios/registro_socio.html')


def perfil(request):
    if request.user.is_authenticated:
        perfil_usuario = request.user.perfil

        pago_exitoso = request.GET.get('pago')

        if pago_exitoso == 'exitoso':
            if not perfil_usuario.es_socio:
                perfil_usuario.es_socio = True
                perfil_usuario.cantidad_restaurantes = 1  
                perfil_usuario.fecha_pago = timezone.now()
                perfil_usuario.fecha_expiracion = timezone.now() + timedelta(days=30)  # +30 días
                perfil_usuario.save()
                messages.success(request, '🎉 ¡Pago recibido! Tu membresía está activa.')

        elif pago_exitoso == 'cancelado':
            messages.warning(request, '⚠️ El pago fue cancelado. Puedes intentarlo de nuevo.')

    return render(request, 'usuarios/perfil.html', {
        'STRIPE_PUBLIC_KEY': settings.STRIPE_PUBLIC_KEY
    })


@csrf_exempt
def crear_payment_intent(request):
    if request.method == 'POST':
        try:
            intent = stripe.PaymentIntent.create(
                amount=45000,  # 450.00 MXN (Stripe maneja centavos)
                currency='mxn',
                metadata={'integration_check': 'accept_a_payment'},
                description='Membresía Restaurante QR'
            )
            return JsonResponse({'clientSecret': intent.client_secret})
        except Exception as e:
            return JsonResponse({'error': str(e)})
