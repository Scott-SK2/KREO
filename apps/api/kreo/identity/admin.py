from django.contrib import admin

from .models import BetaInvitation, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "status", "is_staff", "is_moderator", "created_at")
    list_filter = ("status", "is_staff", "is_moderator")
    search_fields = ("email",)
    readonly_fields = ("password", "created_at", "updated_at")


@admin.register(BetaInvitation)
class BetaInvitationAdmin(admin.ModelAdmin):
    list_display = ("code", "inviter", "used_by", "expires_at", "used_at")
    list_filter = ("used_at",)
