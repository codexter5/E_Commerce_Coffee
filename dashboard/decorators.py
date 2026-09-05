from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def _role(user):
    return getattr(getattr(user, "profile", None), "role", None)


def admin_required(view_func):
    """Restrict a view to accounts with Profile.role == ADMIN (or Django superusers)."""

    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if _role(request.user) != "ADMIN" and not request.user.is_superuser:
            messages.error(request, "You need admin access to view that page.")
            return redirect("core:home")
        return view_func(request, *args, **kwargs)

    return wrapper


def seller_required(view_func):
    """Restrict a view to accounts with Profile.role == SELLER (admins may also pass)."""

    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        role = _role(request.user)
        if role not in ("SELLER", "ADMIN") and not request.user.is_superuser:
            messages.error(request, "You need a seller account to view that page.")
            return redirect("core:home")
        return view_func(request, *args, **kwargs)

    return wrapper


def delivery_required(view_func):
    """Restrict a view to accounts with Profile.role == DELIVERY (admins may also pass)."""

    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        role = _role(request.user)
        if role not in ("DELIVERY", "ADMIN") and not request.user.is_superuser:
            messages.error(request, "You need a delivery account to view that page.")
            return redirect("core:home")
        return view_func(request, *args, **kwargs)

    return wrapper
