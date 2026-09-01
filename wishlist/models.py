from django.contrib.auth.models import User
from django.db import models
from products.models import Product
class Wishlist(models.Model):
    user=models.OneToOneField(User,on_delete=models.CASCADE,related_name="wishlist")
    products=models.ManyToManyField(Product,blank=True,related_name="wishlists")
