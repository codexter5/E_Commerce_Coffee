from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from .forms import ProfileForm, RegistrationForm, UserForm, WalletTransferForm
from .models import WalletTransfer
from .services import transfer_funds

def register(request):
    if request.user.is_authenticated: return redirect("core:home")
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save(); login(request, user)
        messages.success(request, "Welcome! Your account is ready.")
        return redirect("core:home")
    return render(request, "accounts/register.html", {"form": form})

@login_required
def profile(request):
    user_form = UserForm(request.POST or None, instance=request.user)
    profile_form = ProfileForm(request.POST or None, instance=request.user.profile)
    if request.method == "POST" and user_form.is_valid() and profile_form.is_valid():
        user_form.save(); profile_form.save(); messages.success(request, "Profile updated.")
        return redirect("accounts:profile")
    return render(request, "accounts/profile.html", {"user_form": user_form, "profile_form": profile_form, "wallet": request.user.wallet})


@login_required
def wallet(request):
    form = WalletTransferForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            transfer = transfer_funds(request.user, form.cleaned_data["recipient"], form.cleaned_data["amount"], form.cleaned_data["note"])
        except ValueError as error:
            form.add_error(None, str(error))
        except User.DoesNotExist:
            form.add_error("recipient", "No account exists with that username.")
        else:
            messages.success(request, f"Transfer {transfer.reference} completed.")
            return redirect("accounts:wallet")
    transfers = WalletTransfer.objects.filter(sender=request.user) | WalletTransfer.objects.filter(recipient=request.user)
    return render(request, "accounts/wallet.html", {"form": form, "wallet": request.user.wallet, "transfers": transfers.order_by("-created_at")[:20]})
