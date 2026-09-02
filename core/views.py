from django.views.generic import TemplateView

from products.models import Category, Product


class HomeView(TemplateView):
    template_name = "core/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        products = Product.objects.active().select_related("category")
        context.update(
            featured_products=products.filter(featured=True)[:8],
            new_arrivals=products[:8],
            categories=Category.objects.all()[:4],
        )
        return context
