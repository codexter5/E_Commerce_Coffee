from .models import Wishlist


def wishlist_summary(request):
    if not request.user.is_authenticated:
        return {"wishlist_product_ids": set(), "wishlist_count": 0}
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
    product_ids = set(wishlist.products.values_list("pk", flat=True))
    return {"wishlist_product_ids": product_ids, "wishlist_count": len(product_ids)}
