from django.contrib import admin
from .models import Order, OrderItem, Payment, OrderStatus


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("numero", "usuario", "status", "total", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("numero", "usuario__email", "shipping_name", "shipping_phone", "shipping_address")
    readonly_fields = ("created_at", "updated_at", "shipped_at", "delivered_at", "total")

    actions = ["marcar_pagada", "marcar_enviada", "marcar_entregada", "cancelar"]

    def marcar_pagada(self, request, queryset):
        count = 0
        for o in queryset:
            if o.status in {OrderStatus.PENDIENTE, OrderStatus.CANCELADA}:
                o.mark_paid()
                count += 1
        self.message_user(request, f"{count} pedido(s) marcados como PAGADA.")
    marcar_pagada.short_description = "Marcar seleccionadas como PAGADA"

    def marcar_enviada(self, request, queryset):
        count = 0
        for o in queryset:
            if o.status == OrderStatus.PAGADA:
                o.mark_shipped()
                count += 1
        self.message_user(request, f"{count} pedido(s) marcados como ENVIADA.")
    marcar_enviada.short_description = "Marcar seleccionadas como ENVIADA"

    def marcar_entregada(self, request, queryset):
        count = 0
        for o in queryset:
            if o.status == OrderStatus.ENVIADA:
                o.mark_delivered()
                count += 1
        self.message_user(request, f"{count} pedido(s) marcados como ENTREGADA.")
    marcar_entregada.short_description = "Marcar seleccionadas como ENTREGADA"

    def cancelar(self, request, queryset):
        count = 0
        for o in queryset:
            if o.status in {OrderStatus.PENDIENTE, OrderStatus.PAGADA}:
                o.cancel()
                count += 1
        self.message_user(request, f"{count} pedido(s) cancelados.")
    cancelar.short_description = "Cancelar seleccionadas"


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("orden", "producto", "cantidad", "precio_unitario")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("orden", "proveedor", "monto", "status", "created_at")
    list_filter = ("status", "proveedor")
    search_fields = ("orden__numero", "transaction_id")
