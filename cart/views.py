from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from products.models import Product
from .models import CartItem
from .services import get_cart
def detail(request):
    items = get_cart(request).items.select_related("product")
    return render(request, "cart/detail.html", {"items": items, "subtotal": sum((i.total for i in items), 0)})
@require_POST
def add(request, product_id):
    product = get_object_or_404(Product.objects.active(), pk=product_id)
    item, created = CartItem.objects.get_or_create(cart=get_cart(request), product=product)
    item.quantity = min(item.quantity + (0 if created else 1), product.stock_quantity); item.save()
    messages.success(request, f"{product.name} added to cart."); return redirect(request.POST.get("next") or "cart:detail")
@require_POST
def update(request, item_id):
    item = get_object_or_404(CartItem, pk=item_id, cart=get_cart(request)); qty = int(request.POST.get("quantity", 1))
    if qty <= 0: item.delete()
    else: item.quantity = min(qty, item.product.stock_quantity); item.save()
    return redirect("cart:detail")
@require_POST
def remove(request, item_id):
    get_object_or_404(CartItem, pk=item_id, cart=get_cart(request)).delete(); return redirect("cart:detail")
