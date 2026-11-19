from django.contrib import admin

from .models import Alert, AlertChannel, Event, Notification


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    readonly_fields = ["matched_at"]
    list_display = ["title", "category", "source", "occurred_at", "matched_at"]
    list_filter = ["category", "source", "matched_at"]
    search_fields = ["title", "summary"]
    date_hierarchy = "occurred_at"


class AlertChannelInline(admin.TabularInline):
    model = AlertChannel
    extra = 1


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ["name", "user", "active"]
    list_select_related = ["user"]
    list_filter = ["active"]
    search_fields = ["name", "description", "user__username"]
    inlines = [AlertChannelInline]


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["event", "alert_channel", "status", "attempts", "created_at"]
    list_filter = ["status", "alert_channel__channel"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
