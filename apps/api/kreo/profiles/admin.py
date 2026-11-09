from django.contrib import admin

from .models import ArtistProfile


@admin.register(ArtistProfile)
class ArtistProfileAdmin(admin.ModelAdmin):
    list_display = ("slug", "display_name", "visibility", "city", "created_at")
    search_fields = ("slug", "display_name")
