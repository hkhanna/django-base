from django.conf import settings
from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin

from . import models, services, utils


class BaseModelAdmin(admin.ModelAdmin):
    def check(self, **kwargs):
        assert hasattr(self, "create_fn")
        assert hasattr(self, "update_fn")

        return super().check(**kwargs)

    def save_model(self, request, obj, form, change):
        if change:
            update_fn_str = getattr(self, "update_fn")
            update_fn = utils.get_function_from_path(update_fn_str)
            update_fn(instance=obj, **form.cleaned_data)
        else:
            create_fn_str = getattr(self, "create_fn")
            create_fn = utils.get_function_from_path(create_fn_str)
            create_fn(**form.cleaned_data)


class EmailMessageWebhookAdminInline(admin.TabularInline):
    model = models.EmailMessageWebhook
    fields = ("__str__", "received_at", "status")
    readonly_fields = ("__str__", "received_at", "status")
    can_delete = False
    show_change_link = True
    ordering = ("-received_at",)

    def has_add_permission(self, request, obj=None):
        return False


class EmailMessageAttachmentAdminInline(admin.TabularInline):
    model = models.EmailMessageAttachment
    fields = ("uuid", "filename", "file", "mimetype", "created_at")
    readonly_fields = ("uuid", "created_at")
    can_delete = True
    extra = 0


@admin.register(models.EmailMessage)
class EmailMessageAdmin(admin.ModelAdmin):
    readonly_fields = ("created_at",)
    list_display = ("__str__", "to_email", "created_at", "status")
    list_filter = ("status", "template_prefix")
    inlines = [EmailMessageAttachmentAdminInline, EmailMessageWebhookAdminInline]
    actions = ["resend"]

    def save_model(self, request, obj, form, change):
        if change:
            services.email_message_update(instance=obj, **form.cleaned_data)
        else:
            services.email_message_create(**form.cleaned_data)

    @admin.action(description="Resend emails")
    def resend(self, request, queryset):
        count = 0
        for email_message in queryset.all():
            duplicate = services.email_message_duplicate(original=email_message)
            services.email_message_queue(email_message=duplicate, cooldown_allowed=2)
            count += 1

        if count == 1:
            self.message_user(request, "Resent 1 email message")
        else:
            self.message_user(request, f"Resent {count} email messages")


@admin.register(models.EmailMessageWebhook)
class EmailMessageWebhookAdmin(BaseModelAdmin):
    create_fn = "core.services.email_message_webhook_create"
    update_fn = "core.services.email_message_webhook_update"

    readonly_fields = ("received_at",)
    list_display = ("__str__", "email_message", "received_at", "status")
    list_filter = ("email_message__template_prefix",)


admin.site.register(models.Event)
admin.site.unregister(Group)


class OrgUserAdminInline(admin.TabularInline):
    model = models.OrgUser
    fields = ("user", "created_at", "updated_at", "last_accessed_at")
    readonly_fields = ("created_at", "updated_at", "last_accessed_at")
    ordering = ("-last_accessed_at",)
    show_change_link = True
    extra = 0


class OrgUserOrgUserSettingAdminInline(admin.TabularInline):
    model = models.OrgUserOrgUserSetting
    extra = 0


class PlanOrgSettingAdminInline(admin.TabularInline):
    model = models.PlanOrgSetting
    extra = 0


class OverriddenOrgSettingAdminInline(admin.TabularInline):
    model = models.OverriddenOrgSetting
    extra = 0


class OrgUserSettingDefaultAdminInline(admin.TabularInline):
    model = models.OrgUserSettingDefault
    extra = 0


@admin.register(models.Org)
class OrgAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
        "is_active",
        "owner",
        "is_personal",
        "primary_plan",
        "current_period_end",
        "created_at",
        "updated_at",
    )
    list_filter = (
        "is_active",
        "is_personal",
        "primary_plan",
    )
    readonly_fields = ("created_at", "updated_at")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ["name"]}
    date_hierarchy = "created_at"
    inlines = [
        OverriddenOrgSettingAdminInline,
        OrgUserSettingDefaultAdminInline,
        OrgUserAdminInline,
    ]


@admin.register(models.OrgUser)
class OrgUserAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "org",
        "created_at",
        "last_accessed_at",
    )
    fields = ("id", "user", "org", "created_at", "updated_at", "last_accessed_at")
    readonly_fields = ("id", "created_at", "updated_at", "last_accessed_at")
    date_hierarchy = "last_accessed_at"
    inlines = [OrgUserOrgUserSettingAdminInline]


@admin.register(models.Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = (
        "slug",
        "name",
        "is_default",
        "created_at",
        "updated_at",
    )
    fields = ("id", "name", "slug", "is_default", "created_at", "updated_at")
    readonly_fields = ("id", "slug", "created_at", "updated_at")
    search_fields = ("name",)
    inlines = [PlanOrgSettingAdminInline]

    def save_model(self, request, obj, form, change):
        if change:
            services.plan_update(instance=obj, **form.cleaned_data)
        else:
            services.plan_create(**form.cleaned_data)


@admin.register(models.GlobalSetting)
class GlobalSettingAdmin(BaseModelAdmin):
    create_fn = "core.services.global_setting_create"
    update_fn = "core.services.global_setting_update"

    list_display = (
        "slug",
        "created_at",
        "type",
        "value",
    )
    search_fields = ("slug",)


@admin.register(models.OrgSetting)
class OrgSettingAdmin(BaseModelAdmin):
    create_fn = "core.services.org_setting_create"
    update_fn = "core.services.org_setting_update"

    list_display = (
        "slug",
        "created_at",
        "type",
        "default",
    )
    search_fields = ("slug",)


@admin.register(models.OrgUserSetting)
class OrgUserSettingAdmin(BaseModelAdmin):
    create_fn = "core.services.org_user_setting_create"
    update_fn = "core.services.org_user_setting_update"

    list_display = (
        "slug",
        "created_at",
        "type",
        "default",
    )
    search_fields = ("slug",)


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


admin.site.index_title = "Index"
admin.site.site_header = (
    f"{settings.SITE_CONFIG['name']} Administration ({settings.ENVIRONMENT})"
)
admin.site.site_title = f"{settings.SITE_CONFIG['name']} Administration"
