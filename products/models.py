from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(unique=True)
    image = models.ImageField(upload_to="categories/", blank=True)
    class Meta: verbose_name_plural = "categories"; ordering = ("name",)
    def __str__(self): return self.name
    def get_absolute_url(self): return reverse("products:category", args=[self.slug])

class ProductQuerySet(models.QuerySet):
    def active(self): return self.filter(is_active=True)

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    name = models.CharField(max_length=220)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    discount_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    stock_quantity = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to="products/", blank=True)
    seller = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, related_name="products")
    brand = models.CharField(max_length=120, blank=True)
    sku = models.CharField(max_length=80, unique=True)
    featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = ProductQuerySet.as_manager()
    class Meta: ordering = ("-created_at",)
    def __str__(self): return self.name
    @property
    def current_price(self): return self.discount_price if self.discount_price is not None else self.price
    def get_absolute_url(self): return reverse("products:detail", args=[self.slug])
