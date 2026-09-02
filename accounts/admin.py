from django.contrib import admin
from .models import Wallet, WalletTransfer

admin.site.register(Wallet)
admin.site.register(WalletTransfer)
from django.contrib import admin
from .models import Profile
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin): list_display = ("user", "role", "phone", "city"); list_filter = ("role",)
