# cart/management/commands/expire_carts.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from cart.models import Cart, CartStatus

class Command(BaseCommand):
    help = "Marca como EXPIRADO los carritos ABIERTO con +48h sin actualizar"

    def handle(self, *args, **options):
        limit = timezone.now() - timedelta(hours=48)
        qs = Cart.objects.filter(estado=CartStatus.ABIERTO, updated_at__lt=limit)
        count = qs.update(estado=CartStatus.EXPIRADO)
        self.stdout.write(self.style.SUCCESS(f"Carritos expirados: {count}"))
