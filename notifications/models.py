from django.contrib.auth.models import User
from django.db import models


class Notification(models.Model):
    class Type(models.TextChoices):
        ORDER_PLACED = "ORDER_PLACED", "Order placed"
        ORDER_ACCEPTED = "ORDER_ACCEPTED", "Order accepted"
        ORDER_PREPARING = "ORDER_PREPARING", "Order preparing"
        ORDER_READY = "ORDER_READY", "Ready for delivery"
        DELIVERY_ASSIGNED = "DELIVERY_ASSIGNED", "Delivery assigned"
        ORDER_PICKED_UP = "ORDER_PICKED_UP", "Order picked up"
        ORDER_OUT_FOR_DELIVERY = "ORDER_OUT_FOR_DELIVERY", "Out for delivery"
        ORDER_DELIVERED = "ORDER_DELIVERED", "Order delivered"
        ORDER_COMPLETED = "ORDER_COMPLETED", "Order completed"
        ORDER_CANCELLED = "ORDER_CANCELLED", "Order cancelled"

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    order = models.ForeignKey("orders.Order", on_delete=models.CASCADE, null=True, blank=True, related_name="notifications")
    notification_type = models.CharField(max_length=40, choices=Type.choices)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.recipient} - {self.notification_type}"
