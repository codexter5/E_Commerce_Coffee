from django.urls import path
from . import views
app_name="reviews"
urlpatterns=[path("save/<int:product_id>/",views.save,name="save"),path("delete/<int:pk>/",views.delete,name="delete")]
