from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from core.models import UUIDModel
from django.utils import timezone

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError("El usuario requiere un email")
        email = self.normalize_email(email)
        user = self.model(email=email, is_active=True, date_joined=timezone.now(), **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault('is_staff', True)
        extra.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra)

class User(UUIDModel, AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email

class Profile(UUIDModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    nombre = models.CharField(max_length=120)
    telefono = models.CharField(max_length=30, blank=True)
    direccion = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Perfil({self.nombre})"
