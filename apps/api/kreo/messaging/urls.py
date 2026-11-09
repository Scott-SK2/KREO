from django.urls import path

from . import views

urlpatterns = [
    path("conversations", views.ConversationListView.as_view(), name="conversations"),
    path(
        "conversations/<uuid:conversation_id>/messages",
        views.ConversationMessagesView.as_view(),
        name="conversation-messages",
    ),
    path(
        "conversations/<uuid:conversation_id>/read",
        views.ConversationReadView.as_view(),
        name="conversation-read",
    ),
]
