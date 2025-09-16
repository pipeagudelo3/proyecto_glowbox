from django.conf import settings
from django.db import models, transaction
from django.db.models import Sum, F
from django.utils import timezone

from core.models import UUIDModel, TimeStampedModel
from catalog.models import Product, Inventory
from cart.models import Cart, CartItem


class OrderStatus(models.TextChoices):
    PENDIENTE = "PENDIENTE", "Pendiente"
    PAGADA    = "PAGADA", "Pagada"
    ENVIADA   = "ENVIADA", "Enviada"
    ENTREGADA = "ENTREGADA", "Entregada"
    CANCELADA = "CANCELADA", "Cancelada"


class PaymentStatus(models.TextChoices):
    AUTORIZADO = "AUTORIZADO", "Autorizado"
    CAPTURADO  = "CAPTURADO", "Capturado"
    FALLIDO    = "FALLIDO", "Fallido"
    REEMBOLSADO= "REEMBOLSADO", "Reembolsado"


class Order(UUIDModel, TimeStampedModel):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="ordenes"
    )
    numero = models.CharField(max_length=30, unique=True)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    estado = models.CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.PENDIENTE)

    def __str__(self):
        return f"Orden #{self.numero} ({self.estado})"

    def recompute_total(self):
        agg = self.items.aggregate(s=Sum(F("precio_unitario") * F("cantidad")))
        self.total = agg["s"] or 0
        self.save(update_fields=["total"])
        return self.total


class OrderItem(UUIDModel):
    orden = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    producto = models.ForeignKey(Product, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.producto} x{self.cantidad}"

    @property
    def subtotal(self):
        return self.precio_unitario * self.cantidad


class Payment(UUIDModel, TimeStampedModel):
    orden = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name="payment_record"   # <- antes chocaba con 'pago'
    )
    proveedor = models.CharField(max_length=40, default="manual")
    transaction_id = models.CharField(max_length=80, blank=True)
    monto = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.AUTORIZADO)
    fecha_pago = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Pago {self.status} ${self.monto} para {self.orden}"

    def capture(self, transaction_id: str | None = None):
        """
        Captura el pago (simulado). Dispara signal para actualizar stock y orden.
        """
        self.status = PaymentStatus.CAPTURADO
        if transaction_id:
            self.transaction_id = transaction_id
        self.fecha_pago = timezone.now()
        self.save(update_fields=["status", "transaction_id", "fecha_pago"])
