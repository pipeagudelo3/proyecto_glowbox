# cart/management/commands/expire_carts.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from datetime import timedelta

from cart.models import Cart, CartStatus

class Command(BaseCommand):
    help = "Marca como EXPIRADO los carritos abiertos inactivos y limpia sus ítems."

    def add_arguments(self, parser):
        parser.add_argument("--minutes", type=int, default=getattr(settings, "CART_TTL_MINUTES", 45),
                            help="Minutos de inactividad para expirar (default settings.CART_TTL_MINUTES).")

    def handle(self, *args, **opts):
        ttl = opts["minutes"]
        limit = timezone.now() - timedelta(minutes=ttl)
        qs = Cart.objects.filter(estado=CartStatus.ABIERTO, updated_at__lt=limit)
        total = qs.count()
        for cart in qs:
            cart.items.all().delete()
            cart.expire()  # si no tienes el método, usa: cart.estado = CartStatus.EXPIRADO; cart.save(update_fields=["estado"])
        self.stdout.write(self.style.SUCCESS(f"Carritos expirados: {total} (>{ttl} minutos)."))
