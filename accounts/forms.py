# accounts/forms.py
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UsernameField
from .models import Profile

User = get_user_model()

class CustomUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label="Contraseña", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirmar contraseña", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ("email",)
        widgets = {
            "email": forms.EmailInput(attrs={"autocomplete": "email", "placeholder": "tu@correo.com"})
        }

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if not email:
            raise forms.ValidationError("El email es obligatorio.")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este email ya está registrado.")
        return email

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1")
        p2 = cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Las contraseñas no coinciden.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"].lower()
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class EmailAuthenticationForm(AuthenticationForm):
    # Usa el tipo de UsernameField de tu modelo; renombramos la etiqueta a "Email"
    username = UsernameField(
        label="Email",
        widget=forms.EmailInput(attrs={"autofocus": True, "autocomplete": "email", "placeholder": "tu@correo.com"})
    )


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["nombre", "telefono", "direccion"]
        widgets = {
            "nombre": forms.TextInput(attrs={"placeholder": "Nombre completo"}),
            "telefono": forms.TextInput(attrs={"placeholder": "+57 ..."}),
            "direccion": forms.TextInput(attrs={"placeholder": "Calle, número, barrio, ciudad"}),
        }