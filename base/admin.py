from django.conf import settings
from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from . import models


@admin.register(models.User)
class UserAdmin(DefaultUserAdmin):
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name")}),
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
    search_fields = ("email", "first_name", "last_name", "previous_emails")
    ordering = ("email",)
    filter_horizontal = ("groups", "user_permissions")


@admin.register(models.EmailMessage)
class EmailMessageAdmin(admin.ModelAdmin):
    readonly_fields = ("created_at",)
    list_display = ("__str__", "created_at", "status")


admin.site.unregister(Group)
admin.site.index_title = "Index"
admin.site.site_header = (
    f"{settings.SITE_CONFIG['name']} Administration ({settings.ENVIRONMENT})"
)
admin.site.site_title = f"{settings.SITE_CONFIG['name']} Administration"
