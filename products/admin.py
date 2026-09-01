from django.contrib import admin
from .models import Category, Product
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin): prepopulated_fields = {"slug": ("name",)}; list_display = ("name",)
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "current_price", "stock_quantity", "is_active", "featured")
    list_filter = ("is_active", "featured", "category"); search_fields = ("name", "sku", "brand"); prepopulated_fields = {"slug": ("name",)}
