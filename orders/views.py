from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.db import transaction
from django.utils.crypto import get_random_string
from django.contrib.auth.decorators import login_required
from .models import Order, OrderItem, Payment, PaymentStatus
from cart.models import Cart, CartItem

def _get_cart(request):
    cart_id = request.session.get("cart_id")
    if not cart_id:
        return None
    try:
        return Cart.objects.get(id=cart_id)
    except Cart.DoesNotExist:
        return None

@transaction.atomic
def checkout(request):
    """
    Crea la orden desde el carrito y CAPTURA el pago (simulado).
    Limpia el carrito al final.
    """
    cart = _get_cart(request)
    if not cart or not cart.items.exists():
        return redirect("catalog:product_list")

    # Crear orden
    num = get_random_string(10).upper()
    orden = Order.objects.create(
        usuario=request.user if request.user.is_authenticated else None,
        numero=num,
        total=0,
    )

    # Items
    total = 0
    for it in cart.items.select_related("producto"):
        OrderItem.objects.create(
            orden=orden,
            producto=it.producto,
            cantidad=it.cantidad,
            precio_unitario=it.producto.precio,
        )
        total += it.producto.precio * it.cantidad

    orden.total = total
    orden.save(update_fields=["total"])

    # Pago (simulado) → CAPTURAR inmediatamente
    pago = Payment.objects.create(
        orden=orden,
        proveedor="manual",
        monto=orden.total,
        status=PaymentStatus.AUTORIZADO,
    )
    pago.capture(transaction_id=f"MAN-{num}")

    # Vaciar carrito
    cart.items.all().delete()

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
