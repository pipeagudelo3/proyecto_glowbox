# accounts/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import logout
from .forms import ProfileForm, CustomUserCreationForm
from .models import Profile

def signup(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            from django.contrib.auth import login as auth_login
            auth_login(request, user)
            messages.success(request, "¡Cuenta creada con éxito!")
            return redirect("catalog:product_list")
    else:
        form = CustomUserCreationForm()
    return render(request, "accounts/signup.html", {"form": form})


@login_required
def profile_edit(request):
    # Obtiene o crea el perfil del usuario
    profile, _ = Profile.objects.get_or_create(
        user=request.user,
        defaults={"nombre": request.user.email}
    )

    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Perfil actualizado.")
            return redirect("accounts:profile")
    else:
        form = ProfileForm(instance=profile)

    return render(request, "accounts/profile_form.html", {"form": form})

def logout_now(request):
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, "Has cerrado sesión.")
    return redirect("catalog:product_list")
