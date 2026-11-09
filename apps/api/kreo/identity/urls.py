from django.urls import path

from . import views

urlpatterns = [
    path("auth/register", views.RegisterView.as_view(), name="auth-register"),
    path("auth/verify-email", views.VerifyEmailView.as_view(), name="auth-verify-email"),
    path("auth/resend-verification", views.ResendVerificationView.as_view(), name="auth-resend"),
    path("auth/login", views.LoginView.as_view(), name="auth-login"),
    path("auth/refresh", views.RefreshView.as_view(), name="auth-refresh"),
    path("auth/logout", views.LogoutView.as_view(), name="auth-logout"),
    path("auth/password-reset", views.PasswordResetView.as_view(), name="auth-password-reset"),
    path(
        "auth/password-reset/confirm",
        views.PasswordResetConfirmView.as_view(),
        name="auth-password-reset-confirm",
    ),
    path("auth/phone/verify", views.PhoneVerifyView.as_view(), name="auth-phone-verify"),
    path("me", views.MeView.as_view(), name="me"),
    path("me/export", views.MeExportView.as_view(), name="me-export"),
    path("me/invitations", views.MyInvitationsView.as_view(), name="me-invitations"),
    path("admin/invitations", views.AdminInvitationsView.as_view(), name="admin-invitations"),
]
