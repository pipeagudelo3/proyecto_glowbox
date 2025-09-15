from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Product, Inventory

@receiver(post_save, sender=Product)
def create_inventory(sender, instance: Product, created, **kwargs):
    if created and not hasattr(instance, "inventario"):
        Inventory.objects.create(producto=instance, sku=f"SKU-{str(instance.id)[:8]}")
