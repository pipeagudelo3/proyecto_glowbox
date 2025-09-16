# cart/utils.py
from django.utils.crypto import get_random_string  # por si lo usas en otro lado
from .models import Cart, CartStatus, CartItem
from catalog.models import Product


def _ensure_session_key(request):
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


def get_or_create_active_cart(request):
    """
    - Invitado: carrito ligado a session_key (1 activo).
    - Logueado: carrito ligado a usuario (1 activo). Fusiona si hay uno de sesión.
    """
    session_key = _ensure_session_key(request)

    # carrito de sesión
    sess_cart = None
    cart_id = request.session.get("cart_id")
    if cart_id:
        try:
            # ❌ NO importes Cart aquí. Ya está importado arriba.
            sess_cart = Cart.objects.get(id=cart_id)
        except Cart.DoesNotExist:
            sess_cart = None

    if not sess_cart:
        sess_cart = Cart.objects.create(session_key=session_key, estado=CartStatus.ABIERTO)
        request.session["cart_id"] = str(sess_cart.id)

    # si hay usuario autenticado: fusionar con su activo
    if request.user.is_authenticated:
        user_cart = Cart.objects.filter(usuario=request.user, estado=CartStatus.ABIERTO).first()
        if user_cart and user_cart.id != sess_cart.id:
            # pasar items del de sesión al del usuario
            sess_cart.merge_into(user_cart)
            sess_cart.expire()
            request.session["cart_id"] = str(user_cart.id)
            sess_cart = user_cart
        else:
            # Reclamar carrito de sesión para el usuario
            if not sess_cart.usuario_id:
                sess_cart.usuario = request.user
                sess_cart.save(update_fields=["usuario"])
    return sess_cart


def add_product_to_cart(cart: Cart, product: Product, qty: int = 1):
    item, created = CartItem.objects.get_or_create(
        cart=cart, producto=product,
        defaults={"cantidad": qty, "precio_unitario": product.precio}
    )
    if not created:
        item.cantidad += qty
    item.precio_unitario = product.precio  # actualiza por si cambió
    item.save()
    return item
