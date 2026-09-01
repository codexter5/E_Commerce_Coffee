from django.urls import path
from . import views
app_name="wishlist"
urlpatterns=[path("",views.detail,name="detail"),path("toggle/<int:product_id>/",views.toggle,name="toggle")]
