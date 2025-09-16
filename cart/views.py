# cart/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.db.models import F

from .utils import get_or_create_active_cart, add_product_to_cart
from .models import CartStatus, CartItem
from catalog.models import Product


def detail(request):
    """
    Muestra el carrito activo (por sesión o usuario).
    """
    cart = get_or_create_active_cart(request)
    return render(request, "cart/detail.html", {"cart": cart})


@require_POST
def add(request, product_id):
    """
    Agrega un producto al carrito (cantidad por defecto 1 o qty en POST).
    """
    cart = get_or_create_active_cart(request)
    if cart.estado != CartStatus.ABIERTO:
        return redirect("cart:detail")

    product = get_object_or_404(Product, id=product_id, activo=True)
    qty = int(request.POST.get("qty", 1))
    add_product_to_cart(cart, product, max(1, qty))
    return redirect("cart:detail")


@require_POST
def increment(request, item_id):
    """
    Incrementa en +1 la cantidad de un ítem del carrito.
    """
    cart = get_or_create_active_cart(request)
    if cart.estado != CartStatus.ABIERTO:
        return redirect("cart:detail")

    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    item.cantidad = F("cantidad") + 1
    item.save(update_fields=["cantidad"])
    return redirect("cart:detail")


@require_POST
def decrement(request, item_id):
    """
    Decrementa en -1 la cantidad de un ítem del carrito. Si llega a 0, elimina el ítem.
    """
    cart = get_or_create_active_cart(request)
    if cart.estado != CartStatus.ABIERTO:
        return redirect("cart:detail")

    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    if item.cantidad <= 1:
        item.delete()
    else:
        item.cantidad = F("cantidad") - 1
        item.save(update_fields=["cantidad"])
    return redirect("cart:detail")


@require_POST
def remove(request, item_id):
    """
    Elimina un ítem del carrito.
    """
    cart = get_or_create_active_cart(request)
    it = cart.items.filter(id=item_id).first()
    if it:
        it.delete()
    return redirect("cart:detail")


@require_POST
def clear(request):
    """
    Vacía el carrito por completo.
    """
    cart = get_or_create_active_cart(request)
    cart.items.all().delete()
    return redirect("cart:detail")
