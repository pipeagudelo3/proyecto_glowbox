from django.db import transaction
from django.utils import timezone
from .models import Cart, CartStatus
from orders.models import Order, OrderDetail, OrderStatus
from catalog.models import Inventory

def checkout_cart(cart: Cart, perfil=None) -> Order:
    if cart.status != CartStatus.ABIERTO:
        raise ValueError("El carrito debe estar ABIERTO para checkout")

    with transaction.atomic():
        cart.bloquear()

        orden = Order.objects.create(
            perfil=perfil,
            numero=f"ORD-{str(cart.id)[:8]}",
            estado=OrderStatus.PENDIENTE,
            total=0
        )

        for it in cart.items.select_related('producto__inventario'):
            OrderDetail.objects.create(
                orden=orden,
                producto=it.producto,
                cantidad=it.cantidad,
                precio_unitario=it.precio_unitario
            )
            # reservar inventario
            inv = it.producto.inventario
            inv.reservado = inv.reservado + it.cantidad
            inv.save(update_fields=['reservado'])

        orden.recompute_total()
        return orden
