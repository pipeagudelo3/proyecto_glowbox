# accounts/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.apps import apps

User = get_user_model()
Profile = apps.get_model("accounts", "Profile")  # obtenido cuando las apps ya están listas

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        name = (instance.email or "").split("@")[0]
        Profile.objects.create(user=instance, nombre=name or instance.email)
