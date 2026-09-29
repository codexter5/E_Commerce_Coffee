import json

from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Count, Sum

from orders.models import OrderItem
from .models import Product


def product_json_ld(request, product):
    """Builds schema.org Product structured data as a JSON string, safe to
    drop straight into a <script type="application/ld+json"> tag. Built with
    json.dumps rather than hand-written template string interpolation, since
    that was silently producing invalid JSON (missing quotes around every
    value) -- Google couldn't have parsed any of it. `</` is escaped so a
    product name/description containing that sequence can't break out of the
    surrounding <script> tag.
    """
    data = {
        "@context": "https://schema.org/",
        "@type": "Product",
        "name": product.name,
        "description": " ".join(product.description.split()[:40]),
        "sku": product.sku,
        "offers": {
            "@type": "Offer",
            "priceCurrency": "NPR",
            "price": str(product.current_price),
            "availability": "https://schema.org/InStock" if product.stock_quantity else "https://schema.org/OutOfStock",
            "url": request.build_absolute_uri(product.get_absolute_url()),
        },
    }
    if product.brand:
        data["brand"] = {"@type": "Brand", "name": product.brand}
    if product.image:
        data["image"] = request.build_absolute_uri(product.image.url)
    avg_rating = getattr(product, "avg_rating", None)
    if avg_rating:
        data["aggregateRating"] = {
            "@type": "AggregateRating",
            "ratingValue": round(avg_rating, 1),
            "reviewCount": product.reviews.count(),
        }
    return json.dumps(data, cls=DjangoJSONEncoder).replace("</", "<\\/")


def get_related_products(product, limit=4):
    """Same-category products, excluding the product itself -- the simplest
    reliable "you might also like" signal when there's no purchase history
    to draw on yet (e.g. a brand new product)."""
    return (
        Product.objects.active()
        .filter(category=product.category)
        .exclude(pk=product.pk)
        .select_related("category")
        .order_by("-featured", "-created_at")[:limit]
    )


def get_frequently_bought_together(product, limit=4):
    """Products that showed up in the same real orders as this one, ranked by
    how often that co-occurrence happened -- an actual "customers who bought
    this also bought" signal drawn from order history, not a guess."""
    order_ids = OrderItem.objects.filter(product=product).values_list("order_id", flat=True)
    co_products = (
        OrderItem.objects.filter(order_id__in=order_ids)
        .exclude(product=product)
        .values("product")
        .annotate(co_count=Count("id"))
        .order_by("-co_count")[:limit]
    )
    product_ids = [row["product"] for row in co_products]
    if not product_ids:
        return []
    products = Product.objects.active().filter(pk__in=product_ids).select_related("category")
    by_id = {p.pk: p for p in products}
    return [by_id[pid] for pid in product_ids if pid in by_id]


def get_trending_products(limit=8, exclude_ids=None):
    """Best-sellers by units sold across all order history; falls back to the
    newest active products once there isn't enough order history left to
    fill the list (e.g. a brand new store, or after excluding other items)."""
    exclude_ids = list(exclude_ids or [])
    top = (
        OrderItem.objects.exclude(product_id__in=exclude_ids)
        .values("product")
        .annotate(units_sold=Sum("quantity"))
        .order_by("-units_sold")[:limit]
    )
    product_ids = [row["product"] for row in top]
    products = Product.objects.active().filter(pk__in=product_ids).select_related("category")
    by_id = {p.pk: p for p in products}
    ordered = [by_id[pid] for pid in product_ids if pid in by_id]
    if len(ordered) < limit:
        seen_ids = {p.pk for p in ordered} | set(exclude_ids)
        filler = Product.objects.active().exclude(pk__in=seen_ids).select_related("category").order_by("-created_at")
        ordered.extend(filler[: limit - len(ordered)])
    return ordered


def get_collaborative_recommendations(user, limit=8, exclude_ids=None):
    """Basic item-based collaborative filtering. For every product this user
    has bought, find OTHER customers' orders that also contain it, then
    score every other product in *those* orders by how many of them it
    co-occurs with. A candidate that shows up alongside several of the
    user's purchases, across several different customers, scores higher than
    one that only overlapped once -- the standard "customers who bought what
    you bought also bought" signal, built from the order-history co-purchase
    matrix rather than from category membership. Two products end up related
    here purely because real customers keep buying them together, even if
    they sit in different categories."""
    purchased_ids = list(
        OrderItem.objects.filter(order__user=user).values_list("product_id", flat=True).distinct()
    )
    if not purchased_ids:
        return []

    excluded = set(exclude_ids or []) | set(purchased_ids)

    # Other customers' orders that contain at least one of this user's
    # purchases -- the "neighborhood" of similar shopping baskets.
    neighbor_order_ids = (
        OrderItem.objects.filter(product_id__in=purchased_ids)
        .exclude(order__user=user)
        .values_list("order_id", flat=True)
        .distinct()
    )
    scored = (
        OrderItem.objects.filter(order_id__in=neighbor_order_ids)
        .exclude(product_id__in=excluded)
        .values("product_id")
        .annotate(co_occurrence=Count("order_id", distinct=True))
        .order_by("-co_occurrence")[:limit]
    )
    product_ids = [row["product_id"] for row in scored]
    if not product_ids:
        return []
    products = Product.objects.active().filter(pk__in=product_ids).select_related("category")
    by_id = {p.pk: p for p in products}
    return [by_id[pid] for pid in product_ids if pid in by_id]


def get_recommended_for_user(user, limit=8):
    """Personalized picks for the signed-in user, in priority order:
    1. Item-based collaborative filtering (what similar customers' orders
       also contained -- see get_collaborative_recommendations).
    2. Same-category products not already covered, for when there's too
       little cross-customer overlap to fill the list.
    3. Trending best-sellers, as a last resort.
    Falls back straight to trending for anonymous visitors or accounts with
    no order history yet (there's nothing to base a personalized list on)."""
    if not getattr(user, "is_authenticated", False):
        return get_trending_products(limit=limit)

    purchased_product_ids = list(
        OrderItem.objects.filter(order__user=user).values_list("product_id", flat=True)
    )
    if not purchased_product_ids:
        return get_trending_products(limit=limit)

    recommended = get_collaborative_recommendations(user, limit=limit)
    seen_ids = set(purchased_product_ids) | {p.pk for p in recommended}

    if len(recommended) < limit:
        category_ids = (
            Product.objects.filter(pk__in=purchased_product_ids).values_list("category_id", flat=True).distinct()
        )
        category_fill = list(
            Product.objects.active()
            .filter(category_id__in=category_ids)
            .exclude(pk__in=seen_ids)
            .select_related("category")
            .order_by("-featured", "-created_at")[: limit - len(recommended)]
        )
        recommended.extend(category_fill)
        seen_ids |= {p.pk for p in category_fill}

    if len(recommended) < limit:
        filler = get_trending_products(limit=limit - len(recommended), exclude_ids=list(seen_ids))
        recommended.extend(filler)

    return recommended
