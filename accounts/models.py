from django.contrib.auth.models import User
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal

class Profile(models.Model):
    class Role(models.TextChoices):
        BUYER = "BUYER", "Buyer"
        SELLER = "SELLER", "Seller"
        DELIVERY = "DELIVERY", "Delivery Person"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.BUYER)
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=80, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    def __str__(self): return f"{self.user.username}'s profile"


class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="wallet")
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"), validators=[MinValueValidator(Decimal("0.00"))])
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self): return f"{self.user.username}'s wallet"


class WalletTransfer(models.Model):
    sender = models.ForeignKey(User, on_delete=models.PROTECT, related_name="wallet_transfers_sent")
    recipient = models.ForeignKey(User, on_delete=models.PROTECT, related_name="wallet_transfers_received")
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    note = models.CharField(max_length=160, blank=True)
    reference = models.CharField(max_length=24, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.reference:
            from uuid import uuid4
            self.reference = f"WAL-{uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)
