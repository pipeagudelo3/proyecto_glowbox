# orders/signals.py
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Payment, PaymentStatus, OrderStatus
from catalog.models import Inventory


@receiver(post_save, sender=Payment)
def sync_inventory_with_payment(sender, instance: Payment, created, **kwargs):
    """
    Mantiene inventario y orden sincronizados con el estado del pago.
    - AUTORIZADO  -> reservar inventario (1 sola vez)
    - CAPTURADO   -> descontar stock (1 sola vez) y marcar orden PAGADA
    - FALLIDO/CANCELADO/REEMBOLSADO -> liberar reserva si no se capturó
    """
    orden = instance.orden

    # AUTORIZADO => reservar
    if instance.status == PaymentStatus.AUTORIZADO and not instance.reserved_applied:
        with transaction.atomic():
            for it in orden.items.select_related("producto__inventario"):
                inv = getattr(it.producto, "inventario", None)
                if inv:
                    inv.reservar(it.cantidad)
            instance.reserved_applied = True
            instance.save(update_fields=["reserved_applied"])

    # CAPTURADO => comprometer y marcar orden como PAGADA
    elif instance.status == PaymentStatus.CAPTURADO and not instance.captured_applied:
        with transaction.atomic():
            for it in orden.items.select_related("producto__inventario"):
                inv = getattr(it.producto, "inventario", None)
                if inv:
                    inv.comprometer(it.cantidad)

            # ⚠️ aquí usamos 'status' (NO 'estado')
            if hasattr(orden, "status"):
                orden.status = OrderStatus.PAGADA
                orden.save(update_fields=["status"])

            instance.captured_applied = True
            instance.save(update_fields=["captured_applied"])

    # FALLIDO / CANCELADO / REEMBOLSADO => liberar reserva si existía y no se capturó
    elif instance.status in {PaymentStatus.FALLIDO, PaymentStatus.CANCELADO, PaymentStatus.REEMBOLSADO}:
        if instance.reserved_applied and not instance.captured_applied:
            with transaction.atomic():
                for it in orden.items.select_related("producto__inventario"):
                    inv = getattr(it.producto, "inventario", None)
                    if inv:
                        inv.liberar(it.cantidad)
