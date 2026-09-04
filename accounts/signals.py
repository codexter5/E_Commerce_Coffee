from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Profile, Wallet

@receiver(post_save, sender=User)
def make_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
        Wallet.objects.create(user=instance)


@receiver(post_save, sender=Profile)
def sync_admin_staff_flag(sender, instance, **kwargs):
    """Keep Django admin access (is_staff) in sync with the ADMIN role, so an
    admin-role account can use both the custom dashboard and /admin/ without
    anyone having to flip is_staff by hand in two places."""
    should_be_staff = instance.role == Profile.Role.ADMIN
    if instance.user.is_staff != should_be_staff and not instance.user.is_superuser:
        User.objects.filter(pk=instance.user_id).update(is_staff=should_be_staff)
