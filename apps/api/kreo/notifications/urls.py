from django.urls import path

from . import views

urlpatterns = [
    path("notifications", views.NotificationListView.as_view(), name="notifications"),
    path("notifications/read", views.NotificationReadView.as_view(), name="notifications-read"),
    path(
        "me/notification-preferences",
        views.NotificationPreferencesView.as_view(),
        name="notification-preferences",
    ),
    path("devices", views.DeviceTokenView.as_view(), name="devices"),
]
