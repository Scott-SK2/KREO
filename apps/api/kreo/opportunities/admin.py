from django.contrib import admin

from .models import Opportunity, OpportunityRole


class RoleInline(admin.TabularInline):
    model = OpportunityRole
    extra = 0


@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "project",
        "status",
        "has_intimate_scene",
        "moderated_at",
        "published_at",
    )
    list_filter = ("status", "has_intimate_scene")
    inlines = [RoleInline]
