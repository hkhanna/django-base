from django.conf import settings
from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from . import models


@admin.register(models.User)
class UserAdmin(DefaultUserAdmin):
    fieldsets = (
        (None, {"fields": ("id", "uuid", "email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "email_history")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_locked",
                    "is_staff",
                    "is_superuser",
                    # "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "password1", "password2")}),
    )
    list_display = ("email", "first_name", "last_name", "is_staff")
    list_filter = ("is_staff", "is_superuser", "is_active", "groups")
    search_fields = ("email", "first_name", "last_name", "email_history")
    ordering = ("email",)
    filter_horizontal = ("groups", "user_permissions")
    readonly_fields = ("id", "uuid")

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        obj.sync_changed_email()


class EmailMessageWebhookAdminInline(admin.TabularInline):
    model = models.EmailMessageWebhook
    fields = ("__str__", "received_at", "status")
    readonly_fields = ("__str__", "received_at", "status")
    can_delete = False
    show_change_link = True
    ordering = ("-received_at",)

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(models.EmailMessage)
class EmailMessageAdmin(admin.ModelAdmin):
    readonly_fields = ("created_at",)
    list_display = ("__str__", "created_at", "status")
    list_filter = ("status", "template_prefix")
    inlines = [EmailMessageWebhookAdminInline]


@admin.register(models.EmailMessageWebhook)
class EmailMessageWebhookAdmin(admin.ModelAdmin):
    readonly_fields = ("received_at",)
    list_display = ("__str__", "email_message", "received_at", "status")
    list_filter = ("email_message__template_prefix",)


admin.site.unregister(Group)
admin.site.index_title = "Index"
admin.site.site_header = (
    f"{settings.SITE_CONFIG['name']} Administration ({settings.ENVIRONMENT})"
)
admin.site.site_title = f"{settings.SITE_CONFIG['name']} Administration"
