import uuid
from django.contrib.auth.models import User
from django.db import models
from products.models import Product
class Order(models.Model):
    class Status(models.TextChoices):
        PLACED="PLACED", "Placed"; ACCEPTED="ACCEPTED", "Accepted"; PREPARING="PREPARING", "Preparing"; READY_FOR_DELIVERY="READY_FOR_DELIVERY", "Ready for delivery"; ASSIGNED="ASSIGNED", "Assigned"; PICKED_UP="PICKED_UP", "Picked up"; OUT_FOR_DELIVERY="OUT_FOR_DELIVERY", "Out for delivery"; DELIVERED="DELIVERED", "Delivered"; COMPLETED="COMPLETED", "Completed"; CANCELLED="CANCELLED", "Cancelled"
    class PaymentMethod(models.TextChoices):
        CARD = "CARD", "Credit / Debit Card"
        KHALTI = "KHALTI", "Khalti"
        ESEWA = "ESEWA", "eSewa"
        COD = "COD", "Cash on Delivery"
    order_number = models.CharField(max_length=20, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="orders")
    seller = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, related_name="seller_orders")
    delivery_person = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="delivery_orders")
    full_name = models.CharField(max_length=160); email = models.EmailField(); phone = models.CharField(max_length=30)
    shipping_address = models.TextField(); city = models.CharField(max_length=80); postal_code = models.CharField(max_length=20)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2); status = models.CharField(max_length=30, choices=Status.choices, default=Status.PLACED)
    payment_method = models.CharField(max_length=10, choices=PaymentMethod.choices, default=PaymentMethod.CARD)
    is_paid = models.BooleanField(default=False)
    payment_reference = models.CharField(max_length=80, blank=True)
    transaction_hash = models.CharField(max_length=64, blank=True)
    transaction_signature = models.CharField(max_length=64, blank=True)
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
