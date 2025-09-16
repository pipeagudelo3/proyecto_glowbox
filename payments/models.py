# payments/models.py
from django.db import models, transaction
from core.models import UUIDModel, TimeStampedModel
from orders.models import Order, OrderStatus
from catalog.models import Inventory

class PaymentStatus(models.TextChoices):
    AUTORIZADO = 'AUTORIZADO', 'Autorizado'
    CAPTURADO = 'CAPTURADO', 'Capturado'
    FALLIDO = 'FALLIDO', 'Fallido'
    REEMBOLSADO = 'REEMBOLSADO', 'Reembolsado'

class Payment(UUIDModel, TimeStampedModel):
    orden = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='pago')
    proveedor = models.CharField(max_length=40)       
    transaction_id = models.CharField(max_length=80, unique=True)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_pago = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(max_length=12, choices=PaymentStatus.choices, default=PaymentStatus.AUTORIZADO)
