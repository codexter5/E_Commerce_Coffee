from django.db.models import Avg, Q
from django.views.generic import DetailView, ListView
from .models import Category, Product
class ProductListView(ListView):
    model = Product; template_name = "products/list.html"; context_object_name = "products"; paginate_by = 12
    def get_queryset(self):
        qs = Product.objects.active().select_related("category").annotate(avg_rating=Avg("reviews__rating"))
        q = self.request.GET.get("q", "").strip()
        if q: qs = qs.filter(Q(name__icontains=q) | Q(description__icontains=q) | Q(brand__icontains=q))
        return qs.order_by({"price_asc": "price", "price_desc": "-price", "newest": "-created_at"}.get(self.request.GET.get("sort"), "-created_at"))
class ProductDetailView(DetailView):
    model = Product; template_name = "products/detail.html"; context_object_name = "product"
    def get_queryset(self): return Product.objects.active().select_related("category").annotate(avg_rating=Avg("reviews__rating"))
class CategoryListView(ListView): model = Category; template_name = "products/categories.html"; context_object_name = "categories"
class CategoryDetailView(ProductListView):
    def get_queryset(self): return super().get_queryset().filter(category__slug=self.kwargs["slug"])
