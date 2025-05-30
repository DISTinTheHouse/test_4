from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import *
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import requests
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


@login_required
def dashboard_restaurante(request, slug):
    restaurante = get_object_or_404(Restaurante, slug=slug, socio=request.user.perfil)

    return render(request, 'restaurantes/dashboard_restaurante.html', {
        'restaurante': restaurante,
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


def agendar_cita(request, slug):
    restaurante = get_object_or_404(Restaurante, slug=slug)
    mesas_disponibles = Mesa.objects.filter(restaurante=restaurante, disponibilidad=True)

    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        telefono = request.POST.get('telefono')
        fecha = request.POST.get('fecha')
        hora = request.POST.get('hora')
        mesa_id = request.POST.get('mesa_id')

        if nombre and telefono and fecha and hora and mesa_id:
            mesa = get_object_or_404(Mesa, id=mesa_id, restaurante=restaurante)

            # Crear la cita
            cita = Cita.objects.create(
                restaurante=restaurante,
                mesa=mesa,
                nombre_cliente=nombre,
                telefono=telefono,
                fecha=fecha,
                hora=hora,
                confirmado=False,
                creada_en=timezone.now()
            )

            # Marcar la mesa como ocupada
            mesa.disponibilidad = False
            mesa.save()

            return redirect('confirmacion_agenda')  # define esta vista simple

    return render(request, 'restaurantes/agendar_publico.html', {
        'restaurante': restaurante,
        'mesas': mesas_disponibles,
    })


def agendar_mesa_publico(request, slug):
    restaurante = get_object_or_404(Restaurante, slug=slug)
    mesas_disponibles = Mesa.objects.filter(restaurante=restaurante, disponibilidad=True)

    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        telefono = request.POST.get('telefono')
        fecha = request.POST.get('fecha')
        hora = request.POST.get('hora')
        mesa_id = request.POST.get('mesa_id')

        if nombre and telefono and fecha and hora and mesa_id:
            mesa = get_object_or_404(Mesa, id=mesa_id, restaurante=restaurante)
            
            # Guardar la cita
            cita = Cita.objects.create(
                restaurante=restaurante,
                mesa=mesa,
                nombre_cliente=nombre,
                telefono=telefono,
                fecha=fecha,
                hora=hora,
            )

            mesa.disponibilidad = False
            mesa.save()

            return redirect('confirmacion_agenda', cita_id=cita.id)  # redirecciona a una vista de éxito

    return render(request, 'restaurantes/agendar_publico.html', {
        'restaurante': restaurante,
        'mesas': mesas_disponibles,
    })


from django.http import JsonResponse
from django.shortcuts import get_object_or_404
import requests


def enviar_confirmacion_whatsapp(request, cita_id):
    cita = get_object_or_404(Cita, id=cita_id)

    url = "https://graph.facebook.com/v17.0/683402724847602/messages"
    headers = {
        "Authorization": "Bearer EAARDEZAVONqsBOZChYeZBaG9TFpz35WzvGEhuFa77sxBy9eJjSI6CzYDgpuvJahl83ZAwKaxeIa8geTBei1dC6Wahy6ZCEWhn1M0vzSAz0OkXkW8kAIWrBXl8QxKbaQjyXAhvSzcUCZAiNj7YTjDTrKyQYSdp6ZBcTKj2aBvaQPR6pZCOAZAesj4Bup9dMaEiZCjRKeKStwQ1z4RfOrIJgBigOi0Ui",  # ← pega aquí el bueno
        "Content-Type": "application/json"
    }

    data = {
        "messaging_product": "whatsapp",
        "to": f"523338449486",  # ahora que ya confirmaste que es válido
        "type": "template",
        "template": {
            "name": "hello_world",
            "language": {"code": "en_US"},
        }
    }

    response = requests.post(url, headers=headers, json=data)
    print("Payload:", data)
    print("Status:", response.status_code)
    print("Respuesta:", response.json())
    return JsonResponse(response.json())


def confirmacion_agenda(request, cita_id):
    cita = get_object_or_404(Cita, id=cita_id)
    return render(request, 'restaurantes/confirmacion.html', {'cita': cita})


# Mensaje para el socio del restaurante
# mensaje_socio = (
#     f"📢 Nueva reservación en *{restaurante.nombre}*\n"
#     f"🙋 Cliente: {nombre}\n"
#     f"🪑 Mesa: {mesa.numero_mesa}\n"
#     f"📅 Fecha: {fecha}\n"
#     f"⏰ Hora: {hora} hrs"
# )

# # Teléfono del socio (asumiendo que existe en su perfil)
# telefono_socio = restaurante.socio.telefono  # Asegúrate que este campo existe

# # Limpieza del número
# telefono_socio = str(telefono_socio).replace("-", "").replace(" ", "")

# # WhatsApp Cloud API config
# headers = {
#     "Authorization": f"Bearer {WHATSAPP_TOKEN}",
#     "Content-Type": "application/json"
# }

# payload_socio = {
#     "messaging_product": "whatsapp",
#     "to": f"52{telefono_socio}",
#     "type": "text",
#     "text": {"body": mensaje_socio}
# }

# # Enviar mensaje al socio
# try:
#     requests.post(f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_ID}/messages", json=payload_socio, headers=headers)
# except Exception as e:
#     print("Error enviando WhatsApp al socio:", e)


# para los socios y configuración
@login_required
def configurar_restaurante(request, slug):
    restaurante = get_object_or_404(Restaurante, slug=slug)

    # Verificar que el usuario logueado es el socio del restaurante
    if restaurante.socio != request.user.perfil:
        return redirect('restaurantes_socio')  # Redirigir si no es el socio

    if request.method == 'POST':
        try:
            if 'add_mesa' in request.POST:
                Mesa.objects.create(
                    restaurante=restaurante,
                    numero_mesa=int(request.POST['numero_mesa']),
                    capacidad=int(request.POST['capacidad']),
                    descripcion=request.POST.get('descripcion', '')
                )
                messages.success(request, "✅ Mesa agregada correctamente.")

            elif 'add_barra' in request.POST:
                Barra.objects.create(
                    restaurante=restaurante,
                    numero_barra=int(request.POST['numero_barra']),
                    capacidad=int(request.POST['capacidad'])
                )
                messages.success(request, "✅ Barra agregada correctamente.")

            elif 'add_platillo' in request.POST:
                Platillo.objects.create(
                    restaurante=restaurante,
                    nombre=request.POST['nombre_platillo'],
                    descripcion=request.POST.get('descripcion_platillo', ''),
                    precio=float(request.POST['precio_platillo'])
                )
                messages.success(request, "✅ Platillo agregado correctamente.")

            elif 'add_bebida' in request.POST:
                Bebida.objects.create(
                    restaurante=restaurante,
                    nombre=request.POST['nombre_bebida'],
                    descripcion=request.POST.get('descripcion_bebida', ''),
                    precio=float(request.POST['precio_bebida'])
                )
                messages.success(request, "✅ Bebida agregada correctamente.")

        except Exception as e:
            messages.error(request, f"❌ Ocurrió un error al guardar los datos. Verifica los campos.")

        return redirect('configurar_restaurante', slug=restaurante.slug)

    # Mostrar la configuración actual
    secciones = ['mesas', 'barras', 'platillos', 'bebidas']
    return render(request, 'restaurantes/configurar_restaurante.html', {
        'restaurante': restaurante,
        'mesas': Mesa.objects.filter(restaurante=restaurante),
        'barras': Barra.objects.filter(restaurante=restaurante),
        'platillos': Platillo.objects.filter(restaurante=restaurante),
        'bebidas': Bebida.objects.filter(restaurante=restaurante),
        'secciones': secciones,
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
    
     # Obtiene los pedidos pendientes de esa mesa y restaurante
    pedidos = Pedido.objects.filter(
        restaurante=restaurante,
        mesa=mesa,
        estado__in=['completado', 'pendiente', 'en_proceso', 'completado']
    ).order_by('-id')

    # Calcula el total
    total_a_pagar = sum([
        (pedido.platillo.precio if pedido.platillo else pedido.bebida.precio) * pedido.cantidad
        for pedido in pedidos
    ])

    return render(request, 'restaurantes/pedido_rapido.html', {
        'restaurante': restaurante,
        'mesa': mesa,
        'platillos': platillos,
        'bebidas': bebidas,
        'pedidos': pedidos,
        'total_a_pagar': total_a_pagar,
    })


def cambiar_estado_pedido(request, slug, area, pedido_id):
    restaurante = get_object_or_404(Restaurante, slug=slug)
    pedido = get_object_or_404(Pedido, id=pedido_id, tipo=area, restaurante=restaurante)

    if pedido.estado == 'pendiente':
        pedido.estado = 'en_proceso'
    elif pedido.estado == 'en_proceso':
        pedido.estado = 'completado'

    pedido.save()
    messages.success(request, f"Pedido {pedido.id} actualizado a {pedido.estado}")
    return redirect('dashboard_pedidos', slug=slug, area=area)


@staff_member_required
def dashboard_pedidos(request, slug, area):
    if area not in ['cocina', 'barra']:
        return redirect('dashboard_pedidos', slug=slug, area='cocina')

    restaurante = get_object_or_404(Restaurante, slug=slug)

    pedidos = Pedido.objects.filter(
        tipo=area,
        restaurante=restaurante,
        estado__in=['pendiente', 'en_proceso']
    ).order_by('timestamp')

    return render(request, 'restaurantes/dashboard.html', {
        'restaurante': restaurante,
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

@login_required
def dashboard_pedidos_cocina(request, slug):
    restaurante = get_object_or_404(Restaurante, slug=slug)
    pedidos = Pedido.objects.filter(
        tipo='cocina',
        restaurante=restaurante,
        estado__in=['pendiente', 'en_proceso']
    ).order_by('timestamp')
    
    return render(request, 'restaurantes/dashboard.html', {
        'restaurante': restaurante,
        'area': 'cocina',
        'pedidos': pedidos
    })

def cambiar_estado_pedido_cocina(request, slug, pedido_id):
    restaurante = get_object_or_404(Restaurante, slug=slug)
    pedido = get_object_or_404(Pedido, id=pedido_id, tipo='cocina', restaurante=restaurante)

    if pedido.estado == 'pendiente':
        pedido.estado = 'en_proceso'
    elif pedido.estado == 'en_proceso':
        pedido.estado = 'completado'

    pedido.save()
    messages.success(request, f"Pedido {pedido.id} actualizado a {pedido.estado}")
    return redirect('dashboard_pedidos_cocina', slug=slug)

@login_required
def dashboard_pedidos_barra(request, slug):
    restaurante = get_object_or_404(Restaurante, slug=slug)
    pedidos = Pedido.objects.filter(
        tipo='barra',
        restaurante=restaurante,
        estado__in=['pendiente', 'en_proceso']
    ).order_by('timestamp')
    
    return render(request, 'restaurantes/dashboard.html', {
        'restaurante': restaurante,
        'area': 'barra',
        'pedidos': pedidos
    })

def cambiar_estado_pedido_barra(request, slug, pedido_id):
    restaurante = get_object_or_404(Restaurante, slug=slug)
    pedido = get_object_or_404(Pedido, id=pedido_id, tipo='barra', restaurante=restaurante)

    if pedido.estado == 'pendiente':
        pedido.estado = 'en_proceso'
    elif pedido.estado == 'en_proceso':
        pedido.estado = 'completado'

    pedido.save()
    messages.success(request, f"Pedido {pedido.id} actualizado a {pedido.estado}")
    return redirect('dashboard_pedidos_barra', slug=slug)
