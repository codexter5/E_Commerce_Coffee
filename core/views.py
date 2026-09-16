from django.http import HttpResponse
from django.views.generic import TemplateView

from products.models import Category, Product
from products.services import get_recommended_for_user


class HomeView(TemplateView):
    template_name = "core/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        products = Product.objects.active().select_related("category")
        context.update(
            featured_products=products.filter(featured=True)[:8],
            new_arrivals=products[:8],
            categories=Category.objects.all()[:4],
            trending_products=get_recommended_for_user(self.request.user, limit=8),
        )
        return context


def robots_txt(request):
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /dashboard/",
        "Disallow: /accounts/",
        "Disallow: /cart/",
        "Disallow: /orders/",
        "Disallow: /admin/",
        "",
        f"Sitemap: {request.scheme}://{request.get_host()}/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")

