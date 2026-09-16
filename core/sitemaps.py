from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = "daily"

    def items(self):
        return ["core:home", "products:list", "products:categories"]

    def location(self, item):
        return reverse(item)
