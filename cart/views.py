from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from .models import Cart, CartItem, CartStatus
from catalog.models import Product

def _ensure_cart(request):
    cid = request.session.get('cart_id')
    cart = None
    if cid:
        try: cart = Cart.objects.get(id=cid)
        except Cart.DoesNotExist: pass
    if not cart:
        cart = Cart.objects.create()
        request.session['cart_id'] = str(cart.id)
    return cart

def detail(request):
    cart = _ensure_cart(request)
    return render(request, 'cart/detail.html', {'cart': cart})

@require_POST
def add(request, product_id):
    cart = _ensure_cart(request)
    if cart.status != CartStatus.ABIERTO:
        return redirect('cart:detail')

    product = get_object_or_404(Product, id=product_id)
    available = product.inventario.stock - product.inventario.reservado

    item, created = CartItem.objects.get_or_create(
        carrito=cart, producto=product,
        defaults={'precio_unitario': product.precio, 'cantidad': 1}
    )
    if not created:
        if item.cantidad + 1 > available:
            messages.warning(request, "No hay stock suficiente.")
        else:
            item.cantidad += 1
            item.save(update_fields=['cantidad'])
    else:
        if 1 > available:
            item.delete()
            messages.warning(request, "Sin stock disponible.")

    return redirect('cart:detail')

@require_POST
def increment(request, product_id):
    cart = _ensure_cart(request)
    product = get_object_or_404(Product, id=product_id)
    item = get_object_or_404(CartItem, carrito=cart, producto=product)

    available = product.inventario.stock - product.inventario.reservado
    if item.cantidad + 1 > available:
        messages.warning(request, "No puedes superar el stock disponible.")
    else:
        item.cantidad += 1
        item.save(update_fields=['cantidad'])
    return redirect('cart:detail')

@require_POST
def decrement(request, product_id):
    cart = _ensure_cart(request)
    product = get_object_or_404(Product, id=product_id)
    item = get_object_or_404(CartItem, carrito=cart, producto=product)

    if item.cantidad > 1:
        item.cantidad -= 1
        item.save(update_fields=['cantidad'])
    else:
        item.delete()
    return redirect('cart:detail')

@require_POST
def remove(request, product_id):
    cart = _ensure_cart(request)
    cart.items.filter(producto_id=product_id).delete()
    return redirect('cart:detail')

@require_POST
def checkout(request):
    # por ahora sin lógica; luego conectamos órdenes/pagos
    return redirect('cart:detail')
