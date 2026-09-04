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
from orders.workflow import NOTIFICATION_DETAILS
from products.models import Category, Product

from .decorators import admin_required
from .forms import AdminUserCreateForm, AdminUserEditForm, CategoryForm, OrderStatusForm, ProductForm


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
