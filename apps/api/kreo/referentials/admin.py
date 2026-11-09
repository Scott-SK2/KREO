from django.contrib import admin

from .models import City, Discipline


@admin.register(Discipline)
class DisciplineAdmin(admin.ModelAdmin):
    list_display = ("slug", "parent", "active", "sort_order")
    list_filter = ("active", "parent")


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ("postal_code", "__str__", "active")
