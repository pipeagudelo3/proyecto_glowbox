# orders/models.py
from django.db import models
from core.models import UUIDModel, TimeStampedModel
from accounts.models import Profile
from catalog.models import Product

class OrderStatus(models.TextChoices):
    PENDIENTE = 'PENDIENTE', 'Pendiente'
    PAGADA = 'PAGADA', 'Pagada'
    ENVIADA = 'ENVIADA', 'Enviada'
    ENTREGADA = 'ENTREGADA', 'Entregada'
    CANCELADA = 'CANCELADA', 'Cancelada'

class Order(UUIDModel, TimeStampedModel):
    perfil = models.ForeignKey(Profile, on_delete=models.PROTECT, related_name='ordenes', null=True, blank=True)
    numero = models.CharField(max_length=30, unique=True)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    estado = models.CharField(max_length=12, choices=OrderStatus.choices, default=OrderStatus.PENDIENTE)

    def recompute_total(self):
        self.total = sum(d.subtotal() for d in self.detalles.all())
        self.save(update_fields=['total'])

class OrderDetail(UUIDModel):
    orden = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Product, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def subtotal(self):
        return self.precio_unitario * self.cantidad
