from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from apps.accounts.views import (
    ChangePasswordView,
    LoginView,
    LogoutView,
    MeView,
    TwoFactorDisableView,
    TwoFactorSetupView,
    TwoFactorVerifyView,
    UserViewSet,
)

router = DefaultRouter()
router.register("users", UserViewSet, basename="user")

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("me/", MeView.as_view(), name="me"),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("2fa/setup/", TwoFactorSetupView.as_view(), name="2fa-setup"),
    path("2fa/verify/", TwoFactorVerifyView.as_view(), name="2fa-verify"),
    path("2fa/disable/", TwoFactorDisableView.as_view(), name="2fa-disable"),
] + router.urls
