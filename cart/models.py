from django.conf import settings
from django.db import models
from django.db.models import F, Sum
from core.models import UUIDModel, TimeStampedModel
from catalog.models import Product

class CartStatus(models.TextChoices):
    ABIERTO    = "ABIERTO", "Abierto"
    BLOQUEADO  = "BLOQUEADO", "Bloqueado"
    EXPIRADO   = "EXPIRADO", "Expirado"

class Cart(UUIDModel, TimeStampedModel):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="carts"
    )
    session_key = models.CharField(max_length=64, blank=True, db_index=True)
    estado = models.CharField(max_length=12, choices=CartStatus.choices, default=CartStatus.ABIERTO)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        who = self.usuario.email if self.usuario_id else self.session_key or "anon"
        return f"Cart({who}) [{self.estado}]"

    # ————— Operaciones de estado —————
    def lock(self):
        if self.estado == CartStatus.ABIERTO:
            self.estado = CartStatus.BLOQUEADO
            self.save(update_fields=["estado"])

    def unlock(self):
        if self.estado == CartStatus.BLOQUEADO:
            self.estado = CartStatus.ABIERTO
            self.save(update_fields=["estado"])

    def expire(self):
        if self.estado != CartStatus.EXPIRADO:
            self.estado = CartStatus.EXPIRADO
            self.save(update_fields=["estado"])

    # ————— Totales —————
    @property
    def total(self):
        agg = self.items.aggregate(s=Sum(F("precio_unitario") * F("cantidad")))
        return agg["s"] or 0

    # ————— Merge —————
    def merge_into(self, other: "Cart"):
        """Pasa sus items al otro carrito (suma cantidades). No toca el estado."""
        for it in self.items.select_related("producto"):
            tgt, created = CartItem.objects.get_or_create(
                cart=other, producto=it.producto,
                defaults={"cantidad": it.cantidad, "precio_unitario": it.precio_unitario},
            )
            if not created:
                tgt.cantidad = F("cantidad") + it.cantidad
                tgt.save(update_fields=["cantidad"])
        # limpia items del cart origen
        self.items.all().delete()

class CartItem(UUIDModel, TimeStampedModel):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    producto = models.ForeignKey(Product, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = [("cart", "producto")]
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.producto} x{self.cantidad}"

    @property
    def subtotal(self):
        return self.precio_unitario * self.cantidad
