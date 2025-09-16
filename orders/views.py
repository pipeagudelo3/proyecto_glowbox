# orders/views.py
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.crypto import get_random_string

from cart.utils import get_or_create_active_cart

from .forms import TrackingForm
from .models import (
    Order,
    OrderItem,
    Payment,
    PaymentStatus,
    OrderStatus,   # asume que tienes un Enum/choices con ENVIADA, etc.
)


# ----------------------------
# Utilidades de inventario
# ----------------------------
def _get_disponible(inv) -> int:
    """
    Obtiene el disponible del inventario.
    - Si el modelo tiene un método/propiedad 'disponible', lo usa.
    - Si no, calcula: stock - reservado.
    """
    disp_attr = getattr(inv, "disponible", None)
    try:
        valor = disp_attr() if callable(disp_attr) else disp_attr
        return int(valor)
    except Exception:
        stock = getattr(inv, "stock", 0) or 0
        reservado = getattr(inv, "reservado", 0) or 0
        return int(stock - reservado)


def _validate_cart_stock(cart):
    """
    Lanza ValidationError si algún item del carrito excede el stock disponible.
    """
    for it in cart.items.select_related("producto__inventario"):
        inv = getattr(it.producto, "inventario", None)
        if not inv:
            continue
        disponible = _get_disponible(inv)
        if int(it.cantidad) > disponible:
            raise ValidationError(
                f"Stock insuficiente para {it.producto.nombre} (disponible: {disponible})."
            )


# ----------------------------
# Checkout
# ----------------------------
@transaction.atomic
def checkout(request):
    cart = get_or_create_active_cart(request)

    # 1) Debe iniciar sesión
    if not request.user.is_authenticated:
        messages.warning(request, "Primero debes iniciar sesión.")
        login_url = reverse("login")  # nombre de tu URL de login
        return redirect(f"{login_url}?{urlencode({'next': request.path})}")

    # 2) Validar stock
    try:
        _validate_cart_stock(cart)
    except ValidationError as e:
        messages.error(request, str(e))
        return redirect("cart:detail")

    # 3) Bloquear carrito para evitar carreras
    cart.lock()

    # 4) Crear la orden
    numero = f"GB-{get_random_string(8).upper()}"
    orden = Order.objects.create(
        usuario=request.user,
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

    # 5) Crear pago AUTORIZADO -> CAPTURAR (tu flujo manual)
    pago = Payment.objects.create(
        orden=orden,
        proveedor="manual",
        monto=orden.total,
        status=PaymentStatus.AUTORIZADO,
    )

    # CAPTURADO (dispara señales si las definiste para afectar stock)
    pago.capture(transaction_id=f"MAN-{numero}")

    # 6) Limpiar/expirar carrito
    cart.items.all().delete()
    cart.expire()
    request.session.pop("cart_id", None)

    # 7) Ir a página de éxito
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


# ----------------------------
# Tracking (solo staff)
# ----------------------------
@login_required
@user_passes_test(lambda u: u.is_staff)
def set_tracking(request, numero):
    """
    Edita tracking de la orden (carrier + tracking_code).
    Requiere un TrackingForm que sea ModelForm de Order con
    fields = ["shipping_carrier", "tracking_code"]  (ajusta a tus nombres).
    """
    orden = get_object_or_404(Order, numero=numero)

    if request.method == "POST":
        # Si tu form es ModelForm de Order, úsalo con instance:
        form = TrackingForm(request.POST, instance=orden)
        if form.is_valid():
            orden = form.save(commit=False)

            # Si tienes un método helper:
            # if hasattr(orden, "set_tracking"):
            #     orden.set_tracking(orden.shipping_carrier, orden.tracking_code)

            # Marcar como enviada (ajusta al nombre real del choice)
            try:
                orden.status = OrderStatus.ENVIADA
            except Exception:
                # si tu campo se llama 'estado' o el choice es distinto, ajusta aquí
                setattr(orden, "estado", getattr(OrderStatus, "ENVIADA", "ENVIADA"))

            orden.save()
            messages.success(request, "Guía registrada. La orden queda ENVIADA.")
            return redirect("orders:order_detail", numero=orden.numero)
    else:
        form = TrackingForm(instance=orden)

    return render(request, "orders/track_form.html", {"form": form, "orden": orden})
