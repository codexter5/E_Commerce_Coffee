from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from products.models import Product
from .models import Wishlist
@login_required
def detail(request):
    wishlist,_=Wishlist.objects.get_or_create(user=request.user); return render(request,"wishlist/detail.html",{"wishlist":wishlist})
@login_required
def toggle(request,product_id):
    wishlist,_=Wishlist.objects.get_or_create(user=request.user); product=get_object_or_404(Product,pk=product_id)
    wishlist.products.remove(product) if wishlist.products.filter(pk=product.pk).exists() else wishlist.products.add(product)
    return redirect(request.POST.get("next") or "wishlist:detail")
