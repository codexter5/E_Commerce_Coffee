from django.contrib.auth.models import User
from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile, Wallet
from .security import clear_attempts, client_ip, register_failed_attempt

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


@receiver(user_login_failed)
def handle_failed_login(sender, credentials, request=None, **kwargs):
    """Tracks failed attempts per username+IP so StyledAuthenticationForm can
    lock out repeated brute-force guesses, without penalizing everyone else
    trying to log into that same username from a different network."""
    username = (credentials or {}).get("username", "")
    if username and request is not None:
        register_failed_attempt(f"{username}:{client_ip(request)}")


@receiver(user_logged_in)
def handle_successful_login(sender, user, request=None, **kwargs):
    if request is not None:
        clear_attempts(f"{user.get_username()}:{client_ip(request)}")
