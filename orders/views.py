from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from cart.services import get_cart
from .forms import CardPaymentForm, CheckoutForm, EsewaPaymentForm, KhaltiPaymentForm
from .models import Order, OrderItem
from .payment_gateway import CashOnDeliveryGateway, DummyCardGateway, DummyEsewaGateway, DummyKhaltiGateway
from .security import transaction_hash, transaction_signature
from .workflow import notify_order_placed, transition_order


# Each supported payment method pairs a gateway-specific form (None for methods that
# need no extra input, like Cash on Delivery) with a simulator that "charges" the order.
PAYMENT_METHODS = {
    Order.PaymentMethod.CARD: {"form": CardPaymentForm, "gateway": DummyCardGateway()},
    Order.PaymentMethod.KHALTI: {"form": KhaltiPaymentForm, "gateway": DummyKhaltiGateway()},
    Order.PaymentMethod.ESEWA: {"form": EsewaPaymentForm, "gateway": DummyEsewaGateway()},
    Order.PaymentMethod.COD: {"form": None, "gateway": CashOnDeliveryGateway()},
}


def _charge(method, gateway, total, cleaned_data):
    if method == Order.PaymentMethod.CARD:
        return gateway.charge(total, cleaned_data["card_number"], cleaned_data["expiry"], cleaned_data["cvv"])
    if method == Order.PaymentMethod.KHALTI:
        return gateway.charge(total, cleaned_data["khalti_id"], cleaned_data["pin"])
    if method == Order.PaymentMethod.ESEWA:
        return gateway.charge(total, cleaned_data["esewa_id"], cleaned_data["password"], cleaned_data["otp"])
    return gateway.charge(total)


def _create_order(user, form, items, cart, payment_reference, payment_method, is_paid):
    with transaction.atomic():
        for item in items:
            if item.quantity > item.product.stock_quantity:
                return None
        order = form.save(commit=False)
        order.user = user
        order.total_amount = sum(item.total for item in items)
        order.payment_method = payment_method
        order.is_paid = is_paid
        sellers = {item.product.seller for item in items if item.product.seller_id}
        order.seller = sellers.pop() if len(sellers) == 1 else None
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
        order.payment_reference = payment_reference
        order.transaction_hash = transaction_hash(order, payment_reference)
        order.transaction_signature = transaction_signature(order, payment_reference)
        order.save(update_fields=["payment_reference", "transaction_hash", "transaction_signature"])
        notify_order_placed(order)
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
    total = sum(item.total for item in items)

    method = request.POST.get("payment_method") or request.GET.get("method") or Order.PaymentMethod.CARD
    if method not in PAYMENT_METHODS:
        method = Order.PaymentMethod.CARD
    form_class = PAYMENT_METHODS[method]["form"]
    gateway = PAYMENT_METHODS[method]["gateway"]

    # Only bind the form (and attempt a charge) when the POST was actually submitted
    # for the currently selected method, so switching tabs doesn't show stale errors.
    is_submission = request.method == "POST" and request.POST.get("payment_method") == method
    form = form_class(request.POST if is_submission else None) if form_class else None

    if is_submission and (form is None or form.is_valid()):
        cleaned_data = form.cleaned_data if form else {}
        result = _charge(method, gateway, total, cleaned_data)
        if result.successful:
            order_form = CheckoutForm(data=checkout_data)
            order = _create_order(
                request.user, order_form, items, cart, result.reference,
                payment_method=method, is_paid=(method != Order.PaymentMethod.COD),
            )
            if order:
                request.session.pop("checkout_data", None)
                return render(request, "orders/payment.html", {"paid": True, "order": order, "result": result})
            messages.error(request, "Stock changed while you were paying. Please review your cart.")
            return redirect("cart:detail")
        messages.error(request, result.message)

    return render(request, "orders/payment.html", {
        "form": form,
        "total": total,
        "method": method,
        "payment_methods": Order.PaymentMethod.choices,
        "gateway_name": gateway.name,
    })


@login_required
def success(request, order_number):
    return render(request, "orders/success.html", {"order": Order.objects.get(order_number=order_number, user=request.user)})
@login_required
def history(request): return render(request, "orders/history.html", {"orders": request.user.orders.prefetch_related("items").all()})


@login_required
@require_POST
def transition(request, order_number, new_status):
    order = get_object_or_404(Order, order_number=order_number)
    try:
        transition_order(order, request.user, new_status.upper())
    except ValueError as error:
        messages.error(request, str(error))
    else:
        messages.success(request, f"Order {order.order_number} updated.")
    return redirect(request.POST.get("next") or "orders:history")
