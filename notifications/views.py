from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from .models import Notification


@login_required
def listing(request):
    notifications = Notification.objects.filter(recipient=request.user)
    if request.GET.get("unread") == "true":
        notifications = notifications.filter(is_read=False)
    notifications = notifications.select_related("order")[:50]
    return JsonResponse({
        "notifications": [
            {
                "id": notification.id,
                "order_id": notification.order_id,
                "order_number": notification.order.order_number if notification.order else None,
                "type": notification.notification_type,
                "message": notification.message,
                "read": notification.is_read,
                "created_at": notification.created_at.isoformat(),
            }
            for notification in notifications
        ]
    })


@login_required
@require_POST
def mark_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.is_read = True
    notification.save(update_fields=["is_read"])
    return JsonResponse({"success": True})
