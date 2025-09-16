from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .utils import get_or_create_active_cart

@receiver(user_logged_in)
def merge_cart_on_login(sender, request, user, **kwargs):
        get_or_create_active_cart(request)
