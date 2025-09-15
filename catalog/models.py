from django.db import models
from django.db.models import F, Q
from django.db.models.functions import Lower
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.text import slugify
from core.models import UUIDModel, TimeStampedModel


# ---------- Utils ----------
def unique_slugify(instance, value, slug_field_name="slug", max_len=180):
    """
    Genera un slug único a partir de `value`. Si existe, agrega sufijos -2, -3...
    """
    base = slugify(value or "")[:max_len]
    if not base:
        base = str(instance.pk)[:8]  # fallback
    slug = base
    Model = type(instance)
    i = 2
    while Model.objects.filter(**{slug_field_name: slug}).exclude(pk=instance.pk).exists():
        suffix = f"-{i}"
        slug = (base[: max_len - len(suffix)]) + suffix
        i += 1
    return slug


# ---------- Category ----------
class Category(UUIDModel):
    nombre = models.CharField(max_length=120, unique=True)
    descripcion = models.TextField(blank=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)

    class Meta:
        ordering = ['nombre']

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.nombre)
            slug = base
            i = 2
            # garantizar unicidad si existen nombres repetidos
            from django.db.models import Q
            while Category.objects.filter(Q(slug=slug)).exclude(pk=self.pk).exists():
                slug = f"{base}-{i}"
                i += 1
            self.slug = slug
        return super().save(*args, **kwargs)


# ---------- Product ----------
class ProductQuerySet(models.QuerySet):
    def activos(self):
        return self.filter(activo=True)

    def disponibles(self):
        # disponible si stock > reservado
        return self.activos().filter(inventario__stock__gt=F("inventario__reservado"))


class ProductManager(models.Manager):
    def get_queryset(self):
        return ProductQuerySet(self.model, using=self._db)

    def activos(self):
        return self.get_queryset().activos()

    def disponibles(self):
        return self.get_queryset().disponibles()


class Product(UUIDModel, TimeStampedModel):
    categoria = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="productos")
    nombre = models.CharField(max_length=160)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    imagen_url = models.URLField(blank=True)
    activo = models.BooleanField(default=True)
    slug = models.SlugField(max_length=180, unique=True, blank=True)

    objects = ProductManager()

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(check=Q(precio__gte=0), name="product_precio_gte_0"),
            models.UniqueConstraint(Lower("slug"), name="uniq_product_slug_ci"),
        ]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["activo"]),
            models.Index(fields=["categoria", "activo"]),
            models.Index(fields=["-created_at"]),
        ]

    def clean(self):
        if self.precio is None or self.precio < 0:
            raise ValidationError({"precio": "El precio debe ser mayor o igual a 0."})

    def save(self, *args, **kwargs):
        if not self.slug and self.nombre:
            self.slug = unique_slugify(self, self.nombre, slug_field_name="slug", max_len=180)
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre

    def get_absolute_url(self):
        return reverse("catalog:product_detail", kwargs={"slug": self.slug})

    # Aliases útiles para templates (evita {% firstof %})
    @property
    def name(self):
        return self.nombre

    @property
    def price(self):
        return self.precio


# ---------- Inventory ----------
class Inventory(UUIDModel):
    producto = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="inventario")
    sku = models.CharField(max_length=80, unique=True)
    stock = models.PositiveIntegerField(default=0)
    reservado = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.CheckConstraint(check=Q(stock__gte=0), name="inv_stock_gte_0"),
            models.CheckConstraint(check=Q(reservado__gte=0), name="inv_reservado_gte_0"),
            models.CheckConstraint(check=Q(reservado__lte=F("stock")), name="inv_reservado_lte_stock"),
        ]
        indexes = [
            models.Index(fields=["sku"]),
        ]

    # Ajuste directo (positivo o negativo) con F expressions
    def actualizarStock(self, cantidad: int):
        self.stock = F("stock") + cantidad
        self.save(update_fields=["stock"])
        # refrescar valores reales del objeto
        self.refresh_from_db(fields=["stock"])

    # Helpers para reserva/liberación (checkout/pagos)
    def puede_reservar(self, cantidad: int) -> bool:
        return (self.stock - self.reservado) >= cantidad

    def reservar(self, cantidad: int):
        if cantidad <= 0:
            return
        if not self.puede_reservar(cantidad):
            raise ValidationError("No hay stock suficiente para reservar.")
        self.reservado = F("reservado") + cantidad
        self.save(update_fields=["reservado"])
        self.refresh_from_db(fields=["reservado"])

    def liberar(self, cantidad: int):
        if cantidad <= 0:
            return
        self.reservado = models.functions.Greatest(F("reservado") - cantidad, 0)
        self.save(update_fields=["reservado"])
        self.refresh_from_db(fields=["reservado"])

    def __str__(self):
        return f"{self.sku} (stock={self.stock} reservado={self.reservado})"
