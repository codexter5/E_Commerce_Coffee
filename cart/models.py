from django.contrib.auth.models import User
from django.db import models
from products.models import Product
class Cart(models.Model):
    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.CASCADE, related_name="cart")
    session_key = models.CharField(max_length=40, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="cart_items")
    quantity = models.PositiveIntegerField(default=1)
    class Meta: constraints = [models.UniqueConstraint(fields=["cart", "product"], name="unique_cart_product")]
    @property
    def total(self): return self.product.current_price * self.quantity
