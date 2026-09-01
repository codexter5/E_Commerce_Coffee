from .models import Cart
def get_cart(request):
    if request.user.is_authenticated: return Cart.objects.get_or_create(user=request.user)[0]
    if not request.session.session_key: request.session.create()
    return Cart.objects.get_or_create(session_key=request.session.session_key)[0]
