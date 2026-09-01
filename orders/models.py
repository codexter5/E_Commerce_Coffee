import uuid
from django.contrib.auth.models import User
from django.db import models
from products.models import Product
class Order(models.Model):
    class Status(models.TextChoices): PENDING="pending", "Pending"; PROCESSING="processing", "Processing"; SHIPPED="shipped", "Shipped"; DELIVERED="delivered", "Delivered"; CANCELLED="cancelled", "Cancelled"
    order_number = models.CharField(max_length=20, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="orders")
    full_name = models.CharField(max_length=160); email = models.EmailField(); phone = models.CharField(max_length=30)
    shipping_address = models.TextField(); city = models.CharField(max_length=80); postal_code = models.CharField(max_length=20)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2); status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    def save(self, *args, **kwargs):
        if not self.order_number: self.order_number = f"ORD-{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)
    def __str__(self): return self.order_number
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="order_items")
    product_name = models.CharField(max_length=220); price = models.DecimalField(max_digits=12, decimal_places=2); quantity = models.PositiveIntegerField()
    @property
    def total(self): return self.price * self.quantity
