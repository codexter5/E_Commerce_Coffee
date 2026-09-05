from django.contrib import messages
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.models import Profile
from notifications.models import Notification
from orders.models import Order
from orders.workflow import NOTIFICATION_DETAILS, TRANSITIONS, transition_order
from products.models import Category, Product

from .decorators import admin_required, delivery_required, seller_required
from .forms import AdminUserCreateForm, AdminUserEditForm, CategoryForm, OrderStatusForm, ProductForm, SellerProductForm


def _is_admin(user):
    return getattr(getattr(user, "profile", None), "role", None) == "ADMIN" or user.is_superuser


@admin_required
def home(request):
    stats = {
        "total_users": User.objects.count(),
        "total_buyers": Profile.objects.filter(role=Profile.Role.BUYER).count(),
        "total_sellers": Profile.objects.filter(role=Profile.Role.SELLER).count(),
        "total_delivery": Profile.objects.filter(role=Profile.Role.DELIVERY).count(),
        "total_admins": Profile.objects.filter(role=Profile.Role.ADMIN).count(),
        "total_products": Product.objects.count(),
        "low_stock_products": Product.objects.filter(stock_quantity__lte=5, is_active=True).count(),
        "total_orders": Order.objects.count(),
        "pending_orders": Order.objects.exclude(status__in=[Order.Status.COMPLETED, Order.Status.CANCELLED]).count(),
        "revenue": Order.objects.filter(is_paid=True).aggregate(total=Sum("total_amount"))["total"] or 0,
    }
    recent_orders = Order.objects.select_related("user").order_by("-created_at")[:8]
    low_stock = Product.objects.filter(stock_quantity__lte=5, is_active=True).order_by("stock_quantity")[:8]
    return render(request, "dashboard/home.html", {"stats": stats, "recent_orders": recent_orders, "low_stock": low_stock, "active": "home"})


# ---------------------------------------------------------------- Users ----

@admin_required
def users_list(request):
    users = User.objects.select_related("profile").order_by("-date_joined")
    q = request.GET.get("q", "").strip()
    role = request.GET.get("role", "").strip()
    if q:
        users = users.filter(Q(username__icontains=q) | Q(email__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q))
    if role:
        users = users.filter(profile__role=role)
    page_obj = Paginator(users, 20).get_page(request.GET.get("page"))
    return render(request, "dashboard/users_list.html", {
        "page_obj": page_obj, "q": q, "role": role, "roles": Profile.Role.choices, "active": "users",
    })


@admin_required
def user_create(request):
    form = AdminUserCreateForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        messages.success(request, f"Account \"{user.username}\" was created.")
        return redirect("dashboard:users_list")
    return render(request, "dashboard/user_form.html", {"form": form, "mode": "create", "active": "users"})


@admin_required
def user_edit(request, pk):
    user = get_object_or_404(User.objects.select_related("profile"), pk=pk)
    form = AdminUserEditForm(request.POST or None, instance=user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"Account \"{user.username}\" was updated.")
        return redirect("dashboard:users_list")
    return render(request, "dashboard/user_form.html", {"form": form, "mode": "edit", "target_user": user, "active": "users"})


@admin_required
@require_POST
def user_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    if user.pk == request.user.pk:
        messages.error(request, "You cannot delete your own account while logged in.")
    elif user.is_superuser:
        messages.error(request, "Superuser accounts can't be deleted from the dashboard.")
    else:
        username = user.username
        user.delete()
        messages.success(request, f"Account \"{username}\" was deleted.")
    return redirect("dashboard:users_list")


# ------------------------------------------------------------- Products ----

@admin_required
def products_list(request):
    products = Product.objects.select_related("category", "seller").order_by("-created_at")
    q = request.GET.get("q", "").strip()
    if q:
        products = products.filter(Q(name__icontains=q) | Q(sku__icontains=q) | Q(brand__icontains=q))
    page_obj = Paginator(products, 20).get_page(request.GET.get("page"))
    return render(request, "dashboard/products_list.html", {"page_obj": page_obj, "q": q, "active": "products"})


@admin_required
def product_create(request):
    form = ProductForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        product = form.save()
        messages.success(request, f"Product \"{product.name}\" was created.")
        return redirect("dashboard:products_list")
    return render(request, "dashboard/product_form.html", {"form": form, "mode": "create", "active": "products"})


@admin_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form = ProductForm(request.POST or None, request.FILES or None, instance=product)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"Product \"{product.name}\" was updated.")
        return redirect("dashboard:products_list")
    return render(request, "dashboard/product_form.html", {"form": form, "mode": "edit", "product": product, "active": "products"})


@admin_required
@require_POST
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    name = product.name
    product.delete()
    messages.success(request, f"Product \"{name}\" was deleted.")
    return redirect("dashboard:products_list")


# ------------------------------------------------------------ Categories ----

@admin_required
def categories_list(request):
    categories = Category.objects.annotate(product_count=Count("products")).order_by("name")
    return render(request, "dashboard/categories_list.html", {"categories": categories, "active": "categories"})


@admin_required
def category_create(request):
    form = CategoryForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        category = form.save()
        messages.success(request, f"Category \"{category.name}\" was created.")
        return redirect("dashboard:categories_list")
    return render(request, "dashboard/category_form.html", {"form": form, "mode": "create", "active": "categories"})


@admin_required
def category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)
    form = CategoryForm(request.POST or None, request.FILES or None, instance=category)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"Category \"{category.name}\" was updated.")
        return redirect("dashboard:categories_list")
    return render(request, "dashboard/category_form.html", {"form": form, "mode": "edit", "category": category, "active": "categories"})


@admin_required
@require_POST
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if category.products.exists():
        messages.error(request, f"Can't delete \"{category.name}\" while it still has products in it.")
    else:
        name = category.name
        category.delete()
        messages.success(request, f"Category \"{name}\" was deleted.")
    return redirect("dashboard:categories_list")


# ---------------------------------------------------------------- Orders ----

@admin_required
def orders_list(request):
    orders = Order.objects.select_related("user", "seller", "delivery_person").order_by("-created_at")
    status = request.GET.get("status", "").strip()
    q = request.GET.get("q", "").strip()
    if status:
        orders = orders.filter(status=status)
    if q:
        orders = orders.filter(Q(order_number__icontains=q) | Q(full_name__icontains=q) | Q(email__icontains=q))
    page_obj = Paginator(orders, 20).get_page(request.GET.get("page"))
    return render(request, "dashboard/orders_list.html", {
        "page_obj": page_obj, "status": status, "q": q, "statuses": Order.Status.choices, "active": "orders",
    })


@admin_required
def order_detail(request, order_number):
    order = get_object_or_404(Order.objects.prefetch_related("items"), order_number=order_number)
    form = OrderStatusForm(request.POST or None, initial={"status": order.status})
    if request.method == "POST" and form.is_valid():
        new_status = form.cleaned_data["status"]
        if new_status != order.status:
            with transaction.atomic():
                order.status = new_status
                order.save(update_fields=["status"])
                notification_type, message = NOTIFICATION_DETAILS.get(new_status, (None, None))
                if notification_type and order.user_id and order.user_id != request.user.pk:
                    Notification.objects.create(
                        recipient=order.user, order=order, notification_type=notification_type,
                        message=f"Order {order.order_number}: {message} (updated by admin)",
                    )
            messages.success(request, f"Order {order.order_number} status set to {order.get_status_display()}.")
        return redirect("dashboard:order_detail", order_number=order.order_number)
    return render(request, "dashboard/order_detail.html", {"order": order, "form": form, "active": "orders"})


# ===================================================================
# Seller dashboard — scoped to the logged-in seller's own catalog and
# their own orders. Admins may also open these pages (useful for
# support), but ownership checks below still apply to admins visiting
# as a "seller of record" unless they truly are the seller/owner.
# ===================================================================

def _seller_product_queryset(request):
    if _is_admin(request.user):
        return Product.objects.all()
    return Product.objects.filter(seller=request.user)


def _seller_order_queryset(request):
    if _is_admin(request.user):
        return Order.objects.all()
    return Order.objects.filter(seller=request.user)


@seller_required
def seller_home(request):
    products = Product.objects.filter(seller=request.user)
    orders = Order.objects.filter(seller=request.user)
    stats = {
        "total_products": products.count(),
        "active_products": products.filter(is_active=True).count(),
        "low_stock_products": products.filter(stock_quantity__lte=5, is_active=True).count(),
        "out_of_stock_products": products.filter(stock_quantity=0).count(),
        "total_orders": orders.count(),
        "new_orders": orders.filter(status=Order.Status.PLACED).count(),
        "in_progress_orders": orders.filter(status__in=[Order.Status.ACCEPTED, Order.Status.PREPARING]).count(),
        "revenue": orders.filter(is_paid=True).aggregate(total=Sum("total_amount"))["total"] or 0,
    }
    recent_orders = orders.select_related("user").order_by("-created_at")[:8]
    low_stock = products.filter(stock_quantity__lte=5, is_active=True).order_by("stock_quantity")[:8]
    return render(request, "dashboard/seller_home.html", {
        "stats": stats, "recent_orders": recent_orders, "low_stock": low_stock, "active": "seller_home",
    })


@seller_required
def seller_products_list(request):
    products = _seller_product_queryset(request).select_related("category").order_by("-created_at")
    q = request.GET.get("q", "").strip()
    if q:
        products = products.filter(Q(name__icontains=q) | Q(sku__icontains=q) | Q(brand__icontains=q))
    page_obj = Paginator(products, 20).get_page(request.GET.get("page"))
    return render(request, "dashboard/seller_products_list.html", {"page_obj": page_obj, "q": q, "active": "seller_products"})


@seller_required
def seller_product_create(request):
    form = SellerProductForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        product = form.save(commit=False)
        product.seller = request.user
        product.save()
        messages.success(request, f"Product \"{product.name}\" was added to your storefront.")
        return redirect("dashboard:seller_products_list")
    return render(request, "dashboard/seller_product_form.html", {"form": form, "mode": "create", "active": "seller_products"})


@seller_required
def seller_product_edit(request, pk):
    product = get_object_or_404(_seller_product_queryset(request), pk=pk)
    form = SellerProductForm(request.POST or None, request.FILES or None, instance=product)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"Product \"{product.name}\" was updated.")
        return redirect("dashboard:seller_products_list")
    return render(request, "dashboard/seller_product_form.html", {
        "form": form, "mode": "edit", "product": product, "active": "seller_products",
    })


@seller_required
@require_POST
def seller_product_delete(request, pk):
    product = get_object_or_404(_seller_product_queryset(request), pk=pk)
    name = product.name
    product.delete()
    messages.success(request, f"Product \"{name}\" was removed from your storefront.")
    return redirect("dashboard:seller_products_list")


@seller_required
def seller_orders_list(request):
    orders = _seller_order_queryset(request).select_related("user").order_by("-created_at")
    status = request.GET.get("status", "").strip()
    q = request.GET.get("q", "").strip()
    if status:
        orders = orders.filter(status=status)
    if q:
        orders = orders.filter(Q(order_number__icontains=q) | Q(full_name__icontains=q))
    page_obj = Paginator(orders, 20).get_page(request.GET.get("page"))
    return render(request, "dashboard/seller_orders_list.html", {
        "page_obj": page_obj, "status": status, "q": q, "statuses": Order.Status.choices, "active": "seller_orders",
    })


@seller_required
def seller_order_detail(request, order_number):
    order = get_object_or_404(_seller_order_queryset(request).prefetch_related("items"), order_number=order_number)
    next_steps = TRANSITIONS.get(order.status, {})
    seller_next_steps = [status for status, role in next_steps.items() if role == "SELLER"]
    if request.method == "POST":
        new_status = request.POST.get("new_status")
        try:
            transition_order(order, request.user, new_status)
        except ValueError as exc:
            messages.error(request, str(exc))
        else:
            messages.success(request, f"Order {order.order_number} moved to {order.get_status_display()}.")
        return redirect("dashboard:seller_order_detail", order_number=order.order_number)
    return render(request, "dashboard/seller_order_detail.html", {
        "order": order, "seller_next_steps": seller_next_steps,
        "status_labels": dict(Order.Status.choices), "active": "seller_orders",
    })


# ===================================================================
# Delivery dashboard — riders claim unassigned "ready for delivery"
# orders, then walk their own claimed orders through pickup ->
# out-for-delivery -> delivered. Admins may also open these pages.
# ===================================================================

ACTIVE_DELIVERY_STATUSES = [Order.Status.ASSIGNED, Order.Status.PICKED_UP, Order.Status.OUT_FOR_DELIVERY]


def _delivery_available_queryset():
    return Order.objects.filter(status=Order.Status.READY_FOR_DELIVERY, delivery_person__isnull=True)


def _delivery_my_queryset(request):
    if _is_admin(request.user):
        return Order.objects.exclude(delivery_person__isnull=True)
    return Order.objects.filter(delivery_person=request.user)


@delivery_required
def delivery_home(request):
    available = _delivery_available_queryset()
    mine = _delivery_my_queryset(request)
    stats = {
        "available_count": available.count(),
        "active_deliveries": mine.filter(status__in=ACTIVE_DELIVERY_STATUSES).count(),
        "completed_deliveries": mine.filter(status__in=[Order.Status.DELIVERED, Order.Status.COMPLETED]).count(),
    }
    recent_available = available.order_by("ready_at")[:8]
    active_orders = mine.filter(status__in=ACTIVE_DELIVERY_STATUSES).select_related("user").order_by("-created_at")[:8]
    return render(request, "dashboard/delivery_home.html", {
        "stats": stats, "recent_available": recent_available, "active_orders": active_orders, "active": "delivery_home",
    })


@delivery_required
def delivery_available_list(request):
    orders = _delivery_available_queryset().order_by("ready_at")
    q = request.GET.get("q", "").strip()
    if q:
        orders = orders.filter(Q(order_number__icontains=q) | Q(city__icontains=q))
    page_obj = Paginator(orders, 20).get_page(request.GET.get("page"))
    return render(request, "dashboard/delivery_available_list.html", {"page_obj": page_obj, "q": q, "active": "delivery_available"})


@delivery_required
def delivery_my_orders_list(request):
    orders = _delivery_my_queryset(request).select_related("user").order_by("-created_at")
    status = request.GET.get("status", "").strip()
    q = request.GET.get("q", "").strip()
    if status:
        orders = orders.filter(status=status)
    if q:
        orders = orders.filter(Q(order_number__icontains=q) | Q(full_name__icontains=q))
    page_obj = Paginator(orders, 20).get_page(request.GET.get("page"))
    delivery_statuses = [
        (value, label) for value, label in Order.Status.choices
        if value in ("ASSIGNED", "PICKED_UP", "OUT_FOR_DELIVERY", "DELIVERED", "COMPLETED")
    ]
    return render(request, "dashboard/delivery_my_orders_list.html", {
        "page_obj": page_obj, "status": status, "q": q, "statuses": delivery_statuses, "active": "delivery_my_orders",
    })


@delivery_required
def delivery_order_detail(request, order_number):
    if _is_admin(request.user):
        qs = Order.objects.all()
    else:
        qs = Order.objects.filter(
            Q(delivery_person=request.user) | Q(status=Order.Status.READY_FOR_DELIVERY, delivery_person__isnull=True)
        )
    order = get_object_or_404(qs.prefetch_related("items"), order_number=order_number)
    next_steps = TRANSITIONS.get(order.status, {})
    delivery_next_steps = [status for status, role in next_steps.items() if role == "DELIVERY"]
    if request.method == "POST":
        new_status = request.POST.get("new_status")
        try:
            transition_order(order, request.user, new_status)
        except ValueError as exc:
            messages.error(request, str(exc))
        else:
            verb = "claimed" if new_status == "ASSIGNED" else "updated"
            messages.success(request, f"Order {order.order_number} {verb} — now {order.get_status_display()}.")
        return redirect("dashboard:delivery_order_detail", order_number=order.order_number)
    return render(request, "dashboard/delivery_order_detail.html", {
        "order": order, "delivery_next_steps": delivery_next_steps,
        "active": "delivery_my_orders" if order.delivery_person_id else "delivery_available",
    })
