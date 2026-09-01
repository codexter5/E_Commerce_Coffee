from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile
from decimal import Decimal
class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "password1", "password2")
class UserForm(forms.ModelForm):
    class Meta: model = User; fields = ("first_name", "last_name", "email")
class ProfileForm(forms.ModelForm):
    class Meta: model = Profile; fields = ("phone", "address", "city", "postal_code")


class WalletTransferForm(forms.Form):
    recipient = forms.CharField(max_length=150, label="Recipient username")
    amount = forms.DecimalField(min_value=Decimal("0.01"), max_digits=12, decimal_places=2)
    note = forms.CharField(max_length=160, required=False)
