import inspect
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from django.contrib.auth.models import Group

from . import models, services, utils


class BaseModelAdmin(admin.ModelAdmin):
    """Enforce use of services to save and update models"""

    def get_save_func(self, obj, change):
        """Get the create or update function for the object being saved."""
        # Object can be either the instance or its children instances.
        func_str = obj._meta.app_label + ".services." + utils.get_snake_case(obj)
        if change:
            func_str += "_update"
        else:
            func_str += "_create"
        return utils.get_function_from_path(func_str)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            func = self.get_save_func(instance, not instance._state.adding)
            sig = inspect.signature(func)
            required_kwargs = {}
            # Sometimes the <model>_create or <model>_update method requires
            # a keyword argument. If it does, pull it from the instance, if possible.
            for param in sig.parameters.values():
                # Skip optional params
                if param.default != inspect.Parameter.empty:
                    continue

                # Skip **kwargs, obviously.
                if param.kind == inspect.Parameter.VAR_KEYWORD:
                    continue

                # Skip instance and save because we always provide those here.
                if param.name in ("instance", "save"):
                    continue

                required_kwargs[param.name] = getattr(instance, param.name)

            func(instance=instance, save=True, **required_kwargs)

        for obj in formset.deleted_objects:
            obj.delete()

    def save_model(self, request, obj, form, change):
        func = self.get_save_func(obj, change)
        func(instance=obj, save=True, **form.cleaned_data)


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
class EmailMessageAdmin(BaseModelAdmin):
    readonly_fields = ("created_at",)
    list_display = ("__str__", "to_email", "created_at", "status")
    list_filter = ("status", "template_prefix")
    inlines = [EmailMessageAttachmentAdminInline, EmailMessageWebhookAdminInline]
    actions = ["resend"]

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
    readonly_fields = ("received_at",)
    list_display = ("__str__", "email_message", "received_at", "status")
    list_filter = ("email_message__template_prefix",)


@admin.register(models.Event)
class EventAdmin(BaseModelAdmin):
    pass


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
class OrgAdmin(BaseModelAdmin):
    list_display = (
        "name",
        "slug",
        "domain",
        "is_active",
        "owner",
        "primary_plan",
        "current_period_end",
        "created_at",
    )
    list_filter = (
        "is_active",
        "primary_plan",
    )
    readonly_fields = ("created_at", "updated_at")
    search_fields = ("name", "slug", "domain")
    prepopulated_fields = {"slug": ["name"]}
    date_hierarchy = "created_at"
    inlines = [
        OverriddenOrgSettingAdminInline,
        OrgUserSettingDefaultAdminInline,
        OrgUserAdminInline,
    ]


@admin.register(models.OrgUser)
class OrgUserAdmin(BaseModelAdmin):
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
class PlanAdmin(BaseModelAdmin):
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


@admin.register(models.GlobalSetting)
class GlobalSettingAdmin(BaseModelAdmin):
    list_display = (
        "slug",
        "created_at",
        "type",
        "value",
    )
    search_fields = ("slug",)


@admin.register(models.OrgSetting)
class OrgSettingAdmin(BaseModelAdmin):
    list_display = (
        "slug",
        "created_at",
        "type",
        "default",
    )
    search_fields = ("slug",)


@admin.register(models.OrgUserSetting)
class OrgUserSettingAdmin(BaseModelAdmin):
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
        (
            "Personal info",
            {"fields": ("first_name", "last_name", "display_name", "email_history")},
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    # "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "created_at")}),
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

    def user_change_password(self, *args, **kwargs):
        # This seems like a Django bug. Change password view shouldn't choke
        # if we pass extra context (i.e., the current environment) to the view.
        kwargs.pop("extra_context", None)
        return super().user_change_password(*args, **kwargs)


admin.site.index_title = "Index"
admin.site.site_header = (
    f"{settings.SITE_CONFIG['name']} Administration ({settings.ENVIRONMENT})"
)
admin.site.site_title = f"{settings.SITE_CONFIG['name']} Administration"
