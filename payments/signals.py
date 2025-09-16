# payments/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from .models import Payment, PaymentStatus
from orders.models import OrderStatus
from catalog.models import Inventory

@receiver(post_save, sender=Payment)
def on_payment_change(sender, instance: Payment, created, **kwargs):
    # Actua cuando pasa a CAPTURADO (o FALLIDO/REEMBOLSADO para liberar)
    if instance.estado == PaymentStatus.CAPTURADO:
        with transaction.atomic():
            orden = instance.orden
            # Descontar stock y liberar reservado
            for det in orden.detalles.select_related('producto__inventario'):
                inv = det.producto.inventario
                inv.stock = inv.stock - det.cantidad
                inv.reservado = max(0, inv.reservado - det.cantidad)
                inv.save(update_fields=['stock','reservado'])
            orden.estado = OrderStatus.PAGADA
            orden.save(update_fields=['estado'])

    elif instance.estado in (PaymentStatus.FALLIDO, PaymentStatus.REEMBOLSADO):
        # Liberar reservado
        orden = instance.orden
        for det in orden.detalles.select_related('producto__inventario'):
            inv = det.producto.inventario
            inv.reservado = max(0, inv.reservado - det.cantidad)
            inv.save(update_fields=['reservado'])
