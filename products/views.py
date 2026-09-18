from django.db.models import Avg, Q
from django.views.generic import DetailView, ListView
from .models import Category, Product
from .services import get_frequently_bought_together, get_related_products, product_json_ld
class ProductListView(ListView):
    model = Product; template_name = "products/list.html"; context_object_name = "products"; paginate_by = 12
    def get_queryset(self):
        qs = Product.objects.active().select_related("category").annotate(avg_rating=Avg("reviews__rating"))
        q = self.request.GET.get("q", "").strip()
        if q: qs = qs.filter(Q(name__icontains=q) | Q(description__icontains=q) | Q(brand__icontains=q))
        return qs.order_by({"price_asc": "price", "price_desc": "-price", "newest": "-created_at"}.get(self.request.GET.get("sort"), "-created_at"))
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("q", "").strip()
        return context
class ProductDetailView(DetailView):
    model = Product; template_name = "products/detail.html"; context_object_name = "product"
    def get_queryset(self): return Product.objects.active().select_related("category").annotate(avg_rating=Avg("reviews__rating"))
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object
        context["product_json_ld"] = product_json_ld(self.request, product)
        context["whatsapp_message"] = f"Hi, I'm interested in {product.name} ({self.request.build_absolute_uri()})."
        frequently_bought = get_frequently_bought_together(product, limit=4)
        context["frequently_bought_together"] = frequently_bought
        # Prefer real "customers also bought" signal; fall back to same-category
        # picks (topped up if there's not quite enough purchase history yet).
        if len(frequently_bought) >= 4:
            context["related_products"] = frequently_bought
        else:
            exclude_ids = {product.pk} | {p.pk for p in frequently_bought}
            filler = get_related_products(product, limit=4 - len(frequently_bought))
            context["related_products"] = list(frequently_bought) + [p for p in filler if p.pk not in exclude_ids]
        return context
class CategoryListView(ListView): model = Category; template_name = "products/categories.html"; context_object_name = "categories"
class CategoryDetailView(ProductListView):
    def get_queryset(self): return super().get_queryset().filter(category__slug=self.kwargs["slug"])
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["category"] = Category.objects.get(slug=self.kwargs["slug"])
        return context
