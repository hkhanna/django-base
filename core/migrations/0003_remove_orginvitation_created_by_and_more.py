# Generated by Django 4.2.8 on 2024-01-24 23:42

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0002_alter_user_options_remove_user_date_joined_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="orginvitation",
            name="created_by",
        ),
        migrations.RemoveField(
            model_name="orginvitation",
            name="email_messages",
        ),
        migrations.RemoveField(
            model_name="orginvitation",
            name="invitee",
        ),
        migrations.RemoveField(
            model_name="orginvitation",
            name="org",
        ),
        migrations.RemoveConstraint(
            model_name="org",
            name="unique_personal_active_org",
        ),
        migrations.RemoveField(
            model_name="org",
            name="is_personal",
        ),
        migrations.AlterField(
            model_name="plan",
            name="is_default",
            field=models.BooleanField(
                default=False,
                help_text="Used by an org when no plan is specified. Only one plan can be default, so setting this will unset any other default plan.",
            ),
        ),
        migrations.DeleteModel(
            name="OrgInvitation",
        ),
    ]