from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.crypto import get_random_string
from django.contrib import messages
from django.core.exceptions import ValidationError
from .models import Order, OrderItem, Payment, PaymentStatus
from cart.utils import get_or_create_active_cart
from cart.models import CartStatus
from django.urls import reverse
from urllib.parse import urlencode

def _validate_cart_stock(cart):
    for it in cart.items.select_related("producto__inventario"):
        inv = getattr(it.producto, "inventario", None)
        if inv and it.cantidad > inv.disponible:
            raise ValidationError(f"Stock insuficiente para {it.producto.nombre} (disponible: {inv.disponible}).")

@transaction.atomic
def checkout(request):
    cart = get_or_create_active_cart(request)
    if not request.user.is_authenticated:
        messages.warning(request, "Primero debes iniciar sesión.")
        login_url = reverse("login")         # normalmente el name es 'login'
        return redirect(f"{login_url}?{urlencode({'next': request.path})}")

    # Validación previa
    try:
        _validate_cart_stock(cart)
    except ValidationError as e:
        messages.error(request, str(e))
        return redirect("cart:detail")

    # Bloquear mientras creamos la orden
    cart.lock()

    # Crear orden
    numero = f"GB-{get_random_string(8).upper()}"
    orden = Order.objects.create(
        usuario=request.user if request.user.is_authenticated else None,
        numero=numero,
        total=0,
    )

    total = 0
    for it in cart.items.select_related("producto"):
        OrderItem.objects.create(
            orden=orden,
            producto=it.producto,
            cantidad=it.cantidad,
            precio_unitario=it.precio_unitario,
        )
        total += it.precio_unitario * it.cantidad

    orden.total = total
    orden.save(update_fields=["total"])

    # 1) AUTORIZAMOS (→ reserva por señal)
    pago = Payment.objects.create(
        orden=orden,
        proveedor="manual",
        monto=orden.total,
        status=PaymentStatus.AUTORIZADO,
    )

    # 2) Para tu flujo actual, CAPTURAMOS enseguida (→ descuenta stock por señal)
    pago.capture(transaction_id=f"MAN-{numero}")

    # Limpiar/expirar carrito
    cart.items.all().delete()
    cart.expire()
    try:
        del request.session["cart_id"]
    except KeyError:
        pass

    return redirect("orders:success", numero=orden.numero)


def success(request, numero: str):
    orden = get_object_or_404(Order, numero=numero)
    return render(request, "orders/checkout_success.html", {"orden": orden})


def order_detail(request, numero: str):
    orden = get_object_or_404(Order, numero=numero)
    return render(request, "orders/order_detail.html", {"orden": orden})


@login_required
def my_orders(request):
    qs = Order.objects.filter(usuario=request.user).order_by("-created_at")
    return render(request, "orders/my_orders.html", {"orders": qs})
