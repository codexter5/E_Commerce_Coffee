from django import forms

from core.form_utils import apply_bootstrap_styles
from .models import Order


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ("full_name", "email", "phone", "shipping_address", "city", "postal_code")
        widgets = {
            "shipping_address": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_bootstrap_styles(self)


class CardPaymentForm(forms.Form):
    cardholder_name = forms.CharField(max_length=120, label="Cardholder name")
    card_number = forms.CharField(max_length=19, min_length=12, label="Card number")
    expiry = forms.CharField(max_length=5, min_length=5, label="Expiry (MM/YY)", help_text="Use the demo values shown on the right.")
    cvv = forms.CharField(max_length=4, min_length=3, label="CVV", strip=False, widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_bootstrap_styles(self)


class KhaltiPaymentForm(forms.Form):
    khalti_id = forms.CharField(max_length=20, label="Khalti ID (mobile number)", help_text="Use the demo Khalti ID shown on the right.")
    pin = forms.CharField(max_length=10, min_length=4, label="MPIN", strip=False, widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_bootstrap_styles(self)


class EsewaPaymentForm(forms.Form):
    esewa_id = forms.CharField(max_length=20, label="eSewa ID")
    password = forms.CharField(max_length=32, label="Password", strip=False, widget=forms.PasswordInput)
    otp = forms.CharField(max_length=6, min_length=6, label="Token / OTP", help_text="Use the demo token shown on the right.")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_bootstrap_styles(self)
