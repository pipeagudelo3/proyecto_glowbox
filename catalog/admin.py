from django.contrib import admin
from .models import Category, Product, Inventory

class InventoryInline(admin.StackedInline):
    model = Inventory
    can_delete = False
    extra = 0

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("nombre", "slug")
    search_fields = ("nombre", "slug")
    prepopulated_fields = {"slug": ("nombre",)}

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("nombre", "categoria", "precio", "activo", "created_at")
    list_filter = ("categoria", "activo")
    search_fields = ("nombre", "slug", "categoria__nombre")
    prepopulated_fields = {"slug": ("nombre",)}
    inlines = [InventoryInline]

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ("sku", "producto", "stock", "reservado")
    search_fields = ("sku", "producto__nombre")
