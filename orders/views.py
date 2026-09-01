from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render
from cart.services import get_cart
from .forms import CardPaymentForm, CheckoutForm
from .models import Order, OrderItem
from .payment_gateway import DummyKhaltiGateway


def _create_order(user, form, items, cart):
    with transaction.atomic():
        for item in items:
            if item.quantity > item.product.stock_quantity:
                return None
        order = form.save(commit=False)
        order.user = user
        order.total_amount = sum(item.total for item in items)
        order.save()
        for item in items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                product_name=item.product.name,
                price=item.product.current_price,
                quantity=item.quantity,
            )
            item.product.stock_quantity -= item.quantity
            item.product.save(update_fields=["stock_quantity"])
        cart.items.all().delete()
    return order


@login_required
def checkout(request):
    cart = get_cart(request); items = list(cart.items.select_related("product"))
    if not items: return redirect("cart:detail")
    form = CheckoutForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        request.session["checkout_data"] = form.cleaned_data
        return redirect("orders:payment")
    return render(request, "orders/checkout.html", {"form": form, "items": items, "total": sum(i.total for i in items)})


@login_required
def payment(request):
    checkout_data = request.session.get("checkout_data")
    if not checkout_data:
        return redirect("orders:checkout")
    cart = get_cart(request); items = list(cart.items.select_related("product"))
    if not items:
        request.session.pop("checkout_data", None)
        return redirect("cart:detail")
    form = CardPaymentForm(request.POST or None)
    total = sum(item.total for item in items)
    if request.method == "POST" and form.is_valid():
        result = DummyKhaltiGateway().charge(total, form.cleaned_data["card_number"], form.cleaned_data["expiry"], form.cleaned_data["cvv"])
        if result.successful:
            order_form = CheckoutForm(data=checkout_data)
            order = _create_order(request.user, order_form, items, cart)
            if order:
                request.session.pop("checkout_data", None)
                return render(request, "orders/payment.html", {"paid": True, "order": order, "result": result})
            messages.error(request, "Stock changed while you were paying. Please review your cart.")
            return redirect("cart:detail")
        messages.error(request, result.message)
    return render(request, "orders/payment.html", {"form": form, "total": total, "gateway_name": DummyKhaltiGateway.name})


@login_required
def success(request, order_number):
    return render(request, "orders/success.html", {"order": Order.objects.get(order_number=order_number, user=request.user)})
@login_required
def history(request): return render(request, "orders/history.html", {"orders": request.user.orders.prefetch_related("items").all()})
