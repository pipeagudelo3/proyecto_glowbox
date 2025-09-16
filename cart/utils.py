from django.utils.crypto import get_random_string 
from .models import Cart, CartStatus, CartItem
from catalog.models import Product
from django.utils import timezone
from datetime import timedelta
from django.db import transaction
from django.conf import settings 

def _ensure_session_key(request):
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


def _ensure_session_key(request):
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


def _is_stale(cart) -> bool:
    ttl = getattr(settings, "CART_TTL_MINUTES", 45)
    return cart.updated_at < (timezone.now() - timedelta(minutes=ttl))


def get_or_create_active_cart(request):
    """
    - Invitado: carrito ligado a session_key (1 activo).
    - Logueado: carrito ligado a usuario (1 activo). Fusiona si hay uno de sesión.
    """
    session_key = _ensure_session_key(request)

    
    sess_cart = None
    cid = request.session.get("cart_id")
    if cid:
        try:
            c = Cart.objects.get(id=cid)
            # válido solo si está ABIERTO
            if c.estado == CartStatus.ABIERTO:
                sess_cart = c
        except Cart.DoesNotExist:
            pass

    
    if not sess_cart:
        sess_cart = (
            Cart.objects.filter(session_key=session_key, estado=CartStatus.ABIERTO)
            .order_by("-updated_at")
            .first()
        )

    
    if not sess_cart:
        sess_cart = Cart.objects.create(session_key=session_key, estado=CartStatus.ABIERTO)
        request.session["cart_id"] = str(sess_cart.id)

    
    if _is_stale(sess_cart):
        sess_cart.items.all().delete()
        sess_cart.expire()  
        sess_cart = Cart.objects.create(session_key=session_key, estado=CartStatus.ABIERTO)
        request.session["cart_id"] = str(sess_cart.id)

   
    if request.user.is_authenticated:
        user_cart = (
            Cart.objects.filter(usuario=request.user, estado=CartStatus.ABIERTO)
            .exclude(id=sess_cart.id)
            .order_by("-updated_at")
            .first()
        )
        if user_cart:
            
            with transaction.atomic():
                sess_cart.merge_into(user_cart)  
                sess_cart.expire()
            request.session["cart_id"] = str(user_cart.id)
            sess_cart = user_cart
        else:
            
            if not sess_cart.usuario_id:
                sess_cart.usuario = request.user
                sess_cart.save(update_fields=["usuario"])

    
    request.session["cart_id"] = str(sess_cart.id)
    request.session.modified = True

    return sess_cart


def add_product_to_cart(cart: Cart, product: Product, qty: int = 1):
    item, created = CartItem.objects.get_or_create(
        cart=cart, producto=product,
        defaults={"cantidad": qty, "precio_unitario": product.precio}
    )
    if not created:
        item.cantidad += qty
    item.precio_unitario = product.precio  
    item.save()
    return item
