from django.contrib.auth.models import User
from django.db import models
from products.models import Product
class Review(models.Model):
    product=models.ForeignKey(Product,on_delete=models.CASCADE,related_name="reviews"); user=models.ForeignKey(User,on_delete=models.CASCADE,related_name="reviews")
    rating=models.PositiveSmallIntegerField(); comment=models.TextField(); created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)
    class Meta: constraints=[models.UniqueConstraint(fields=["product","user"],name="unique_product_review")]
