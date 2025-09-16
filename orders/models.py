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
    AUTORIZADO  = "AUTORIZADO", "Autorizado"
    CAPTURADO   = "CAPTURADO", "Capturado"
    FALLIDO     = "FALLIDO", "Fallido"
    REEMBOLSADO = "REEMBOLSADO", "Reembolsado"
    CANCELADO   = "CANCELADO", "Cancelado"   



class Order(UUIDModel, TimeStampedModel):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="orders"
    )
    numero = models.CharField(max_length=24, unique=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    # estado del pedido
    status = models.CharField(
        max_length=12, choices=OrderStatus.choices, default=OrderStatus.PENDIENTE
    )

    # datos de envío 
    shipping_name = models.CharField(max_length=120, blank=True)
    shipping_phone = models.CharField(max_length=30, blank=True)
    shipping_address = models.CharField(max_length=255, blank=True)
    shipping_carrier = models.CharField(max_length=40, blank=True)   
    tracking_code    = models.CharField(max_length=60, blank=True) 

    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    def set_tracking(self, carrier: str, code: str):
    
        self.shipping_carrier = (carrier or "").strip()
        self.tracking_code = (code or "").strip()
        if self.status == OrderStatus.PAGADA:
            self.mark_shipped()  # setea status=ENVIADA y shipped_at
        else:
            self.save(update_fields=["shipping_carrier", "tracking_code"])

    def __str__(self):
        return f"{self.numero} · {self.get_status_display()}"

   
    def mark_paid(self):
        if self.status in {OrderStatus.PENDIENTE, OrderStatus.CANCELADA}:
            self.status = OrderStatus.PAGADA
            self.save(update_fields=["status"])

    def mark_shipped(self):
        if self.status == OrderStatus.PAGADA:
            self.status = OrderStatus.ENVIADA
            self.shipped_at = timezone.now()
            self.save(update_fields=["status", "shipped_at"])

    def mark_delivered(self):
        if self.status == OrderStatus.ENVIADA:
            self.status = OrderStatus.ENTREGADA
            self.delivered_at = timezone.now()
            self.save(update_fields=["status", "delivered_at"])

    def cancel(self):
        if self.status in {OrderStatus.PENDIENTE, OrderStatus.PAGADA}:
            self.status = OrderStatus.CANCELADA
            self.save(update_fields=["status"])


class OrderItem(UUIDModel, TimeStampedModel):
    orden = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    producto = models.ForeignKey(Product, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario

    def __str__(self):
        return f"{self.producto} x{self.cantidad}"


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
    orden = models.ForeignKey("Order", on_delete=models.CASCADE, related_name="payments")
    proveedor = models.CharField(max_length=40, default="manual")
    transaction_id = models.CharField(max_length=80, blank=True)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=12, choices=PaymentStatus.choices, default=PaymentStatus.AUTORIZADO)

    # ✅ Flags de idempotencia
    reserved_applied = models.BooleanField(default=False)
    captured_applied = models.BooleanField(default=False)

    def authorize(self, transaction_id=None):
        self.status = PaymentStatus.AUTORIZADO
        if transaction_id:
            self.transaction_id = transaction_id
        self.save(update_fields=["status", "transaction_id"])

    def capture(self, transaction_id=None):
        self.status = PaymentStatus.CAPTURADO
        if transaction_id:
            self.transaction_id = transaction_id
        self.save(update_fields=["status", "transaction_id"])

    def fail(self):
        self.status = PaymentStatus.FALLIDO
        self.save(update_fields=["status"])

    def refund(self):
        self.status = PaymentStatus.REEMBOLSADO
        self.save(update_fields=["status"])

    def cancel(self):
        self.status = PaymentStatus.CANCELADO
        self.save(update_fields=["status"])