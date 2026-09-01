from django.urls import path
from .views import CategoryDetailView, CategoryListView, ProductDetailView, ProductListView
app_name = "products"
urlpatterns = [path("", ProductListView.as_view(), name="list"), path("categories/", CategoryListView.as_view(), name="categories"), path("category/<slug:slug>/", CategoryDetailView.as_view(), name="category"), path("<slug:slug>/", ProductDetailView.as_view(), name="detail")]
