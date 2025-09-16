from django.urls import path, include
from django.contrib.auth import views as auth_views
from .views import signup
from .forms import EmailAuthenticationForm
from . import views

app_name = "accounts"

urlpatterns = [
    path("logout/", views.logout_now, name="logout"),
    path("login/", auth_views.LoginView.as_view(template_name="accounts/login.html", authentication_form=EmailAuthenticationForm), name="login"),
    path("signup/", signup, name="signup"),
    path("profile/", views.profile_edit, name="profile"),
    path("", include("django.contrib.auth.urls")),
]
