from django.contrib.auth import views as auth_views
from django.urls import path

from .forms import StyledAuthenticationForm, StyledPasswordResetForm
from . import views

app_name = "accounts"
urlpatterns = [
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html", authentication_form=StyledAuthenticationForm), name="login"),
    path("password_reset/", auth_views.PasswordResetView.as_view(template_name="registration/password_reset_form.html", form_class=StyledPasswordResetForm), name="password_reset"),
    path("register/", views.register, name="register"),
    path("profile/", views.profile, name="profile"),
    path("wallet/", views.wallet, name="wallet"),
]
