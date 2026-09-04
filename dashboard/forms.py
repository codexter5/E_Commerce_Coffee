from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from accounts.models import Profile
from core.form_utils import apply_bootstrap_styles
from orders.models import Order
from products.models import Category, Product


class AdminUserCreateForm(UserCreationForm):
    """Used by admins to create any kind of account (buyer, seller, delivery, admin)
    from inside the dashboard, without touching /admin/."""

    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=Profile.Role.choices, initial=Profile.Role.BUYER)

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "role", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_bootstrap_styles(self)

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            user.profile.role = self.cleaned_data["role"]
            user.profile.save(update_fields=["role"])
        return user


class AdminUserEditForm(forms.ModelForm):
    """Used by admins to edit an existing account's details, role, and access."""

    role = forms.ChoiceField(choices=Profile.Role.choices)

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "is_active")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["role"].initial = self.instance.profile.role
        apply_bootstrap_styles(self)

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            user.profile.role = self.cleaned_data["role"]
            user.profile.save(update_fields=["role"])
        return user


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = (
            "category", "seller", "name", "slug", "description", "brand", "sku",
            "price", "discount_price", "stock_quantity", "image", "featured", "is_active",
        )
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["seller"].queryset = User.objects.filter(profile__role="SELLER").order_by("username")
        self.fields["seller"].required = False
        apply_bootstrap_styles(self)


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ("name", "slug", "image")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_bootstrap_styles(self)


class OrderStatusForm(forms.Form):
    """Lets an admin force an order into any status, bypassing the normal
    buyer/seller/delivery-role transition rules in orders.workflow."""

    status = forms.ChoiceField(choices=Order.Status.choices)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_bootstrap_styles(self)
