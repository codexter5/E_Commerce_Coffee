from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, UserCreationForm
from django.contrib.auth.models import User
from decimal import Decimal

from core.form_utils import apply_bootstrap_styles
from .models import Profile
from .security import client_ip, is_locked_out


class StyledAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_bootstrap_styles(self)

    def clean(self):
        # Checked before Django's own username/password check runs, so a
        # locked-out attacker can't keep guessing passwords -- and this
        # doesn't touch valid users elsewhere, since it's keyed to this
        # specific username+IP combination, not the account globally.
        username = self.cleaned_data.get("username")
        if username and self.request is not None:
            identifier = f"{username}:{client_ip(self.request)}"
            if is_locked_out(identifier):
                raise forms.ValidationError(
                    "Too many failed login attempts. Please wait a few minutes before trying again.",
                    code="locked_out",
                )
        return super().clean()


class StyledPasswordResetForm(PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_bootstrap_styles(self)


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_bootstrap_styles(self)


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_bootstrap_styles(self)


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("phone", "address", "city", "postal_code")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_bootstrap_styles(self)


class WalletTransferForm(forms.Form):
    recipient = forms.CharField(max_length=150, label="Recipient username")
    amount = forms.DecimalField(min_value=Decimal("0.01"), max_digits=12, decimal_places=2)
    note = forms.CharField(max_length=160, required=False, widget=forms.Textarea(attrs={"rows": 3}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_bootstrap_styles(self)
