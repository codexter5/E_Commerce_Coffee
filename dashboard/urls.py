from django.urls import path

from . import views

app_name = "dashboard"
urlpatterns = [
    path("", views.home, name="home"),

    path("users/", views.users_list, name="users_list"),
    path("users/add/", views.user_create, name="user_create"),
    path("users/<int:pk>/edit/", views.user_edit, name="user_edit"),
    path("users/<int:pk>/delete/", views.user_delete, name="user_delete"),

    path("products/", views.products_list, name="products_list"),
    path("products/add/", views.product_create, name="product_create"),
    path("products/<int:pk>/edit/", views.product_edit, name="product_edit"),
    path("products/<int:pk>/delete/", views.product_delete, name="product_delete"),

    path("categories/", views.categories_list, name="categories_list"),
    path("categories/add/", views.category_create, name="category_create"),
    path("categories/<int:pk>/edit/", views.category_edit, name="category_edit"),
    path("categories/<int:pk>/delete/", views.category_delete, name="category_delete"),

    path("orders/", views.orders_list, name="orders_list"),
    path("orders/<str:order_number>/", views.order_detail, name="order_detail"),

    path("seller/", views.seller_home, name="seller_home"),
    path("seller/products/", views.seller_products_list, name="seller_products_list"),
    path("seller/products/add/", views.seller_product_create, name="seller_product_create"),
    path("seller/products/<int:pk>/edit/", views.seller_product_edit, name="seller_product_edit"),
    path("seller/products/<int:pk>/delete/", views.seller_product_delete, name="seller_product_delete"),
    path("seller/orders/", views.seller_orders_list, name="seller_orders_list"),
    path("seller/orders/<str:order_number>/", views.seller_order_detail, name="seller_order_detail"),

    path("delivery/", views.delivery_home, name="delivery_home"),
    path("delivery/available/", views.delivery_available_list, name="delivery_available_list"),
    path("delivery/orders/", views.delivery_my_orders_list, name="delivery_my_orders_list"),
    path("delivery/orders/<str:order_number>/", views.delivery_order_detail, name="delivery_order_detail"),
]
