# cart/signals.py
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .utils import get_or_create_active_cart

@receiver(user_logged_in)
def merge_cart_on_login(sender, request, user, **kwargs):
    # Solo invoca util — ya hace el merge si aplica
    get_or_create_active_cart(request)
