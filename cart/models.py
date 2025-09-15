from django.db import models, transaction
from core.models import UUIDModel, TimeStampedModel
from catalog.models import Product

class CartStatus(models.TextChoices):
    ABIERTO = 'ABIERTO', 'Abierto'
    BLOQUEADO = 'BLOQUEADO', 'Bloqueado'
    EXPIRADO = 'EXPIRADO', 'Expirado'

class Cart(UUIDModel, TimeStampedModel):
    # opcional: relacionar a un usuario/perfil si está autenticado
    status = models.CharField(max_length=10, choices=CartStatus.choices, default=CartStatus.ABIERTO)

    def total(self):
        return sum(i.subtotal() for i in self.items.select_related('producto'))

    def bloquear(self):
        if self.status != CartStatus.ABIERTO:
            raise ValueError("Solo se puede bloquear un carrito ABIERTO")
        self.status = CartStatus.BLOQUEADO
        self.save(update_fields=['status'])

    def expirar(self):
        self.status = CartStatus.EXPIRADO
        self.save(update_fields=['status'])

class CartItem(UUIDModel, TimeStampedModel):
    carrito = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='en_carritos')
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def subtotal(self):
        return self.precio_unitario * self.cantidad

    class Meta:
        unique_together = ('carrito', 'producto')
