from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Profile, Wallet

@receiver(post_save, sender=User)
def make_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
        Wallet.objects.create(user=instance)
