from django.contrib import admin

from .models import BuildEvent, WebhookDelivery


@admin.register(WebhookDelivery)
class WebhookDeliveryAdmin(admin.ModelAdmin):
    list_display = ("provider", "delivery_id", "project", "received_at")
    list_filter = ("provider",)
    search_fields = ("delivery_id", "project__name", "project__slug")
    autocomplete_fields = ("project",)
    readonly_fields = ("received_at",)


@admin.register(BuildEvent)
class BuildEventAdmin(admin.ModelAdmin):
    list_display = ("project", "status", "branch", "commit_sha", "duration", "created_at")
    list_filter = ("status",)
    search_fields = ("branch", "commit_sha", "project__name", "project__slug")
    autocomplete_fields = ("project",)
    readonly_fields = ("created_at",)
