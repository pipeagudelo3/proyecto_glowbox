from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Payment, PaymentStatus, OrderStatus
from catalog.models import Inventory


@receiver(post_save, sender=Payment)
def on_payment_captured(sender, instance: Payment, created, **kwargs):
    if instance.status != PaymentStatus.CAPTURADO:
        return

    orden = instance.orden
    # Si ya estaba pagada, no repetir
    if orden.estado == OrderStatus.PAGADA:
        return

    with transaction.atomic():
        # Descontar stock
        for it in orden.items.select_related("producto"):
            inv = Inventory.objects.select_for_update().get(producto=it.producto)
            # stock no baja de cero (por seguridad)
            new_stock = max(0, inv.stock - it.cantidad)
            inv.stock = new_stock
            # si manejas 'reservado', podrías despejarlo aquí:
            if inv.reservado and inv.reservado >= it.cantidad:
                inv.reservado = inv.reservado - it.cantidad
            inv.save(update_fields=["stock", "reservado"])

        orden.estado = OrderStatus.PAGADA
        orden.save(update_fields=["estado"])
