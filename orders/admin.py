from django.contrib import admin
from .models import Order, OrderItem, Payment

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("producto", "cantidad", "precio_unitario", "subtotal")
    can_delete = False

    def subtotal(self, obj):
        return obj.subtotal

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("numero", "usuario", "estado", "total", "created_at")
    list_filter = ("estado", "created_at")
    search_fields = ("numero", "usuario__username", "usuario__email")
    inlines = [OrderItemInline]

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("orden", "status", "monto", "proveedor", "transaction_id", "fecha_pago")
    list_filter = ("status", "proveedor")
    search_fields = ("orden__numero", "transaction_id")
