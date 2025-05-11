from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import *
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import stripe
from django.conf import settings
stripe.api_key = settings.STRIPE_SECRET_KEY

#QR DE MESAS
import qrcode
from io import BytesIO
from django.http import HttpResponse

@login_required
def qr_mesa(request, slug, numero_mesa):
    url = f"{request.scheme}://{request.get_host()}/restaurantes/r/{slug}/mesa/{numero_mesa}/"
    qr = qrcode.make(url)
    buffer = BytesIO()
    qr.save(buffer, format='PNG')
    buffer.seek(0)

    return HttpResponse(buffer.getvalue(), content_type='image/png')


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

    # Contar mesas por restaurante
    conteo_mesas = {}
    for r in restaurantes:
        total = r.mesas.count()
        disponibles = r.mesas.filter(disponibilidad=True).count()
        conteo_mesas[r.id] = {
            'total': total,
            'disponibles': disponibles
    }

    return render(request, 'restaurantes/mis_restaurantes.html', {
        'perfil': perfil,  # ✅ Agregado para usarlo directo en el template
        'restaurantes': restaurantes,
        'conteo_mesas': conteo_mesas,
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

# para los que no tienen usuario y quieren agendar
def detalle_restaurante(request, slug):
    restaurante = get_object_or_404(Restaurante, slug=slug)

    # Verificar si hay mesas disponibles
    mesas_disponibles = Mesa.objects.filter(restaurante=restaurante, disponibilidad=True)

    # Determinar si el restaurante está disponible para agendar
    restaurante_disponible = True if mesas_disponibles.exists() else False

    return render(request, 'restaurantes/detalle_restaurante.html', {
        'restaurante': restaurante,
        'restaurante_disponible': restaurante_disponible,
    })


# para los socios y configuración
def configurar_restaurante(request, slug):
    restaurante = get_object_or_404(Restaurante, slug=slug)

    # Verificar que el usuario logueado es el socio del restaurante
    if restaurante.socio != request.user.perfil:
        return redirect('restaurantes_socio')  # Redirigir si no es el socio

    if request.method == 'POST':
        # Configuración de mesas
        if 'add_mesa' in request.POST:
            numero_mesa = int(request.POST.get('numero_mesa'))
            capacidad = int(request.POST.get('capacidad'))
            descripcion = request.POST.get('descripcion', '')

            Mesa.objects.create(
                restaurante=restaurante,
                numero_mesa=numero_mesa,
                capacidad=capacidad,
                descripcion=descripcion
            )

        # Configuración de barras
        if 'add_barra' in request.POST:
            numero_barra = int(request.POST.get('numero_barra'))
            capacidad = int(request.POST.get('capacidad'))
            Barra.objects.create(
                restaurante=restaurante,
                numero_barra=numero_barra,
                capacidad=capacidad,
            )

        # Configuración de platillos
        if 'add_platillo' in request.POST:
            nombre = request.POST.get('nombre_platillo')
            descripcion = request.POST.get('descripcion_platillo', '')
            precio = float(request.POST.get('precio_platillo'))
            Platillo.objects.create(
                restaurante=restaurante,
                nombre=nombre,
                descripcion=descripcion,
                precio=precio
            )

        # Configuración de bebidas
        if 'add_bebida' in request.POST:
            nombre = request.POST.get('nombre_bebida')
            descripcion = request.POST.get('descripcion_bebida', '')
            precio = float(request.POST.get('precio_bebida'))
            Bebida.objects.create(
                restaurante=restaurante,
                nombre=nombre,
                descripcion=descripcion,
                precio=precio
            )

        # Redirigir después de guardar la configuración
        return redirect('configurar_restaurante', slug=restaurante.slug)

    # Mostrar la configuración del restaurante
    mesas = Mesa.objects.filter(restaurante=restaurante)
    barras = Barra.objects.filter(restaurante=restaurante)
    platillos = Platillo.objects.filter(restaurante=restaurante)
    bebidas = Bebida.objects.filter(restaurante=restaurante)

    return render(request, 'restaurantes/configurar_restaurante.html', {
        'restaurante': restaurante,
        'mesas': mesas,
        'barras': barras,
        'platillos': platillos,
        'bebidas': bebidas
    })


def pedido_rapido(request, slug, numero_mesa):
    restaurante = get_object_or_404(Restaurante, slug=slug)
    mesa = get_object_or_404(Mesa, restaurante=restaurante, numero_mesa=numero_mesa)

    platillos = Platillo.objects.filter(restaurante=restaurante, disponible=True)
    bebidas = Bebida.objects.filter(restaurante=restaurante, disponible=True)

    if request.method == 'POST':
        tipo = request.POST.get('tipo')  # 'cocina' o 'barra'
        cantidad = int(request.POST.get('cantidad', 1))
        platillo_id = request.POST.get('platillo')
        bebida_id = request.POST.get('bebida')

        platillo = Platillo.objects.get(id=platillo_id) if platillo_id else None
        bebida = Bebida.objects.get(id=bebida_id) if bebida_id else None

        pedido = Pedido.objects.create(
            restaurante=restaurante,
            mesa=mesa,
            tipo=tipo,
            estado='pendiente',
            cantidad=cantidad,
            platillo=platillo,
            bebida=bebida
        )

        Notificacion.objects.create(
            pedido=pedido,
            mensaje=f"Nueva orden de {tipo} desde la mesa {mesa.numero_mesa}",
            enviado_a=tipo
        )

        return redirect('pedido_rapido', slug=slug, numero_mesa=numero_mesa)

    return render(request, 'restaurantes/pedido_rapido.html', {
        'restaurante': restaurante,
        'mesa': mesa,
        'platillos': platillos,
        'bebidas': bebidas,
    })


def cambiar_estado_pedido(request, area, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id, tipo=area)

    if pedido.estado == 'pendiente':
        pedido.estado = 'en_proceso'
    elif pedido.estado == 'en_proceso':
        pedido.estado = 'completado'

    pedido.save()
    messages.success(request, f"Pedido {pedido.id} actualizado a {pedido.estado}")
    return redirect('dashboard_pedidos', area=area)


@staff_member_required  # opcional, solo para usuarios del staff
def dashboard_pedidos(request, area):
    if area not in ['cocina', 'barra']:
        return redirect('dashboard_pedidos', area='cocina')

    pedidos = Pedido.objects.filter(
        tipo=area,
        estado__in=['pendiente', 'en_proceso']
    ).order_by('timestamp')

    return render(request, 'restaurantes/dashboard.html', {
        'area': area,
        'pedidos': pedidos
    })

# area para el socio ver sus restaurantes , messas y pedidos
@login_required
def mesas_restaurante(request, restaurante_id):
    restaurante = get_object_or_404(Restaurante, id=restaurante_id, socio=request.user.perfil)
    mesas = Mesa.objects.filter(restaurante=restaurante).order_by('numero_mesa')

    # Mapear mesas a pedidos activos
    pedidos_por_mesa = {
        mesa.id: Pedido.objects.filter(mesa=mesa, estado__in=['pendiente', 'en_proceso'])
        for mesa in mesas
    }

    return render(request, 'restaurantes/mesas_restaurante.html', {
        'restaurante': restaurante,
        'mesas': mesas,
        'pedidos_por_mesa': pedidos_por_mesa
    })
