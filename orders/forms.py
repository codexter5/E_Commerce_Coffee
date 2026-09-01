from django import forms
from .models import Order


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ("full_name", "email", "phone", "shipping_address", "city", "postal_code")


class CardPaymentForm(forms.Form):
    cardholder_name = forms.CharField(max_length=120, label="Cardholder name")
    card_number = forms.CharField(max_length=19, min_length=12, label="Card number")
    expiry = forms.CharField(max_length=5, min_length=5, label="Expiry (MM/YY)", help_text="Use the demo values shown below.")
    cvv = forms.CharField(max_length=4, min_length=3, label="CVV", strip=False, widget=forms.PasswordInput)
