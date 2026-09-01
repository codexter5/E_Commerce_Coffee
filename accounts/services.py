from django.contrib.auth.models import User
from django.db import transaction
from .models import Wallet, WalletTransfer


def transfer_funds(sender, recipient_username, amount, note=""):
    recipient = User.objects.get(username=recipient_username)
    if recipient == sender:
        raise ValueError("You cannot transfer funds to yourself.")
    first_user, second_user = sorted((sender, recipient), key=lambda user: user.pk)
    with transaction.atomic():
        wallets = {
            wallet.user_id: wallet
            for wallet in Wallet.objects.select_for_update().filter(user__in=(first_user, second_user))
        }
        sender_wallet = wallets[sender.pk]
        if sender_wallet.balance < amount:
            raise ValueError("Insufficient wallet balance.")
        sender_wallet.balance -= amount
        wallets[recipient.pk].balance += amount
        sender_wallet.save(update_fields=("balance", "updated_at"))
        wallets[recipient.pk].save(update_fields=("balance", "updated_at"))
        return WalletTransfer.objects.create(sender=sender, recipient=recipient, amount=amount, note=note)