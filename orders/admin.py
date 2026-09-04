from django.contrib import admin
from .models import Order, OrderItem
class OrderItemInline(admin.TabularInline): model=OrderItem; readonly_fields=("product_name","price","quantity")
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin): list_display=("order_number","user","seller","delivery_person","total_amount","payment_method","is_paid","status","payment_reference","created_at"); readonly_fields=("payment_reference","transaction_hash","transaction_signature"); list_filter=("status","payment_method","is_paid"); inlines=[OrderItemInline]
