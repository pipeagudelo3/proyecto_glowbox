# catalog/management/commands/seed_catalog.py
"""
Comando para poblar el catálogo con datos de ejemplo.

Uso:
  python manage.py seed_catalog
  python manage.py seed_catalog --reset
  python manage.py seed_catalog --reset --min-stock=8 --max-stock=50
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
import random
import string

from catalog.models import Category, Product, Inventory

# Importar condicionalmente modelos de otras apps para un "reset profundo"
try:
    from cart.models import CartItem, Cart
except Exception:
    CartItem = Cart = None

try:
    from orders.models import OrderItem, Order, Payment
except Exception:
    OrderItem = Order = Payment = None


# --------------------------
# Dataset de ejemplo
# --------------------------
DATASET = {
    "Accesorios": {
        "desc": "Bolsos, gorras, cinturones, accesorios para complementar tu outfit.",
        "products": [
            ("Bolso Supreme x North face", "89.90",
             "https://images.unsplash.com/photo-1520975954732-35dd22f47525?auto=format&fit=crop&w=1200&q=60"),
            ("Gorra Glowbox Logo", "24.90",
             "https://images.unsplash.com/photo-1519681393784-d120267933ba?auto=format&fit=crop&w=1200&q=60"),
            ("Cinturón Minimal", "19.90",
             "https://images.unsplash.com/photo-1562184552-875a64d2d7b8?auto=format&fit=crop&w=1200&q=60"),
            ("Bolso bandolera urbano", "39.90",
             "https://images.unsplash.com/photo-1519681390377-3f6f18b1c6f4?auto=format&fit=crop&w=1200&q=60"),
        ],
    },
    "Calzado": {
        "desc": "Zapatos y tenis para estilo diario o deportivo.",
        "products": [
            ("New balance rebel v4", "200.00",
             "https://images.unsplash.com/photo-1525966222134-fcfa99b8ae77?auto=format&fit=crop&w=1200&q=60"),
            ("Nike Air 270", "149.90",
             "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=1200&q=60"),
            ("Adidas Ultraboost", "159.90",
             "https://images.unsplash.com/photo-1543508282-6319a3e2621f?auto=format&fit=crop&w=1200&q=60"),
            ("Converse Chuck 70", "89.90",
             "https://images.unsplash.com/photo-1519741497674-611481863552?auto=format&fit=crop&w=1200&q=60"),
        ],
    },
    "Camisetas y Polos": {
        "desc": "Básicos, gráficos y ediciones especiales.",
        "products": [
            ("Camiseta Nike", "25.00",
             "https://images.unsplash.com/photo-1520975869010-6f61d4d8b9c1?auto=format&fit=crop&w=1200&q=60"),
            ("Camiseta Glowbox Classic", "19.90",
             "https://images.unsplash.com/photo-1519733883369-a019f9f0a49d?auto=format&fit=crop&w=1200&q=60"),
            ("Polo Essential", "29.90",
             "https://images.unsplash.com/photo-1532996122721-709c2a1f081c?auto=format&fit=crop&w=1200&q=60"),
            ("Camiseta Oversize", "27.90",
             "https://images.unsplash.com/photo-1541462608143-67571c6738dd?auto=format&fit=crop&w=1200&q=60"),
        ],
    },
    "Chaquetas y Abrigos": {
        "desc": "Cazadoras, impermeables y colaboraciones icónicas.",
        "products": [
            ("Chaqueta Supreme x North Face", "499.99",
             "https://images.unsplash.com/photo-1520975928319-2f3f2b6e0f24?auto=format&fit=crop&w=1200&q=60"),
            ("Abrigo Puffer Glow", "129.90",
             "https://images.unsplash.com/photo-1519345182560-3f2917c472ef?auto=format&fit=crop&w=1200&q=60"),
            ("Cazadora Denim", "79.90",
             "https://images.unsplash.com/photo-1512436991641-6745cdb1723f?auto=format&fit=crop&w=1200&q=60"),
            ("Rompe vientos Técnico", "89.90",
             "https://images.unsplash.com/photo-1556306535-abd7f01f9e56?auto=format&fit=crop&w=1200&q=60"),
        ],
    },
    "Pantalones": {
        "desc": "Cargo, denim y joggers.",
        "products": [
            ("Pantalón Cargo Olive", "129.90",
             "https://images.unsplash.com/photo-1516826957135-70087f47b0c8?auto=format&fit=crop&w=1200&q=60"),
            ("Jogger Urbano", "49.90",
             "https://images.unsplash.com/photo-1541099649105-f69ad21f3246?auto=format&fit=crop&w=1200&q=60"),
            ("Jean Slim Indigo", "59.90",
             "https://images.unsplash.com/photo-1519741497674-611481863552?auto=format&fit=crop&w=1200&q=60"),
            ("Chino Beige", "54.90",
             "https://images.unsplash.com/photo-1520975869010-6f61d4d8b9c1?auto=format&fit=crop&w=1200&q=60"),
        ],
    },
    "Ofertas": {
        "desc": "Descuentos de temporada y últimas tallas.",
        "products": [
            ("Camiseta Básica (2x1)", "14.90",
             "https://images.unsplash.com/photo-1512436991641-6745cdb1723f?auto=format&fit=crop&w=1200&q=60"),
            ("Sudadera Glowbox", "39.90",
             "https://images.unsplash.com/photo-1519741497674-611481863552?auto=format&fit=crop&w=1200&q=60"),
            ("Short Training", "24.90",
             "https://images.unsplash.com/photo-1520975928319-2f3f2b6e0f24?auto=format&fit=crop&w=1200&q=60"),
            ("Gorra Logo", "12.90",
             "https://images.unsplash.com/photo-1519681390377-3f6f18b1c6f4?auto=format&fit=crop&w=1200&q=60"),
        ],
    },
}


# --------------------------
# Utilidades
# --------------------------
def _unique_sku(prefix: str = "GB") -> str:
    """Genera un SKU único (best effort)."""
    for _ in range(10):
        letters = "".join(random.choices(string.ascii_uppercase, k=3))
        numbers = random.randint(10000, 99999)
        sku = f"{prefix}-{letters}{numbers}"
        if not Inventory.objects.filter(sku=sku).exists():
            return sku
    # si falla, devolvemos uno sin comprobar (muy improbable colisión)
    return f"{prefix}-{random.randint(100000, 999999)}"


class Command(BaseCommand):
    help = "Crea categorías, productos e inventario de ejemplo para la tienda."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Elimina catálogo y relacionadas (carritos/pedidos) antes de poblar.",
        )
        parser.add_argument("--min-stock", type=int, default=6)
        parser.add_argument("--max-stock", type=int, default=40)

    @transaction.atomic
    def handle(self, *args, **opts):
        reset = opts["reset"]
        min_s = int(opts["min_stock"])
        max_s = int(opts["max_stock"])
        if min_s > max_s:
            min_s, max_s = max_s, min_s

        if reset:
            self.stdout.write(self.style.WARNING("Borrando datos relacionados…"))

            # 1) Borrar dependencias que protegen a Product
            if CartItem:
                CartItem.objects.all().delete()
            if Cart:
                Cart.objects.all().delete()

            # Pagos -> Items -> Órdenes (por si on_delete no es CASCADE)
            if Payment:
                Payment.objects.all().delete()
            if OrderItem:
                OrderItem.objects.all().delete()
            if Order:
                Order.objects.all().delete()

            # 2) Ahora sí: inventario, productos, categorías
            Inventory.objects.all().delete()
            Product.objects.all().delete()
            Category.objects.all().delete()

        # ---- Sembrar datos ----
        total_cat = total_prod = total_inv = 0

        for cat_name, meta in DATASET.items():
            cat, _ = Category.objects.get_or_create(
                nombre=cat_name,
                defaults={"descripcion": meta.get("desc", "")},
            )
            total_cat += 1

            for name, price_str, img in meta["products"]:
                price = Decimal(price_str)

                prod, created = Product.objects.get_or_create(
                    nombre=name,
                    defaults={
                        "categoria": cat,
                        "descripcion": "",
                        "precio": price,
                        "imagen_url": img,
                        "activo": True,
                    },
                )

                if not created:
                    # Actualiza datos básicos si ya existed
                    prod.categoria = cat
                    prod.precio = price
                    prod.imagen_url = img
                    prod.activo = True
                    prod.save()

                total_prod += 1

                inv, inv_created = Inventory.objects.get_or_create(
                    producto=prod,
                    defaults={
                        "sku": _unique_sku(),
                        "stock": random.randint(min_s, max_s),
                        "reservado": 0,
                    },
                )
                # Si ya existía y estamos en reset, refrescamos stock y SKU si falta
                if not inv_created and reset:
                    inv.stock = random.randint(min_s, max_s)
                    inv.reservado = 0
                    if not inv.sku:
                        inv.sku = _unique_sku()
                    inv.save()

                total_inv += 1

        self.stdout.write(self.style.SUCCESS("✓ Catálogo sembrado correctamente"))
        self.stdout.write(self.style.SUCCESS(f"  Categorías: {total_cat}"))
        self.stdout.write(self.style.SUCCESS(f"  Productos:  {total_prod}"))
        self.stdout.write(self.style.SUCCESS(f"  Inventarios:{total_inv}"))
