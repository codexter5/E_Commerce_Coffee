from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from products.models import Product
from .forms import ReviewForm
from .models import Review
@login_required
def save(request, product_id):
    product=get_object_or_404(Product,pk=product_id); review=Review.objects.filter(product=product,user=request.user).first(); form=ReviewForm(request.POST,instance=review)
    if form.is_valid():
        obj=form.save(commit=False); obj.product=product; obj.user=request.user; obj.save()
    return redirect(product.get_absolute_url())
@login_required
def delete(request, pk):
    review=get_object_or_404(Review,pk=pk,user=request.user); slug=review.product.slug; review.delete(); return redirect("products:detail",slug=slug)
