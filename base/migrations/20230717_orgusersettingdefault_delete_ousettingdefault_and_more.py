# Generated by Django 4.2.3 on 2023-08-08 15:14

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):
    dependencies = [
        ("base", "20230716_orguserorgusersetting_delete_orguserousetting_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="OrgUserSettingDefault",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "uuid",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        help_text="Secondary ID",
                        unique=True,
                        verbose_name="UUID",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        db_index=True, default=django.utils.timezone.now
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("value", models.IntegerField()),
                (
                    "org",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="org_user_setting_defaults",
                        to="base.org",
                    ),
                ),
                (
                    "setting",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="org_user_setting_defaults",
                        to="base.orgusersetting",
                    ),
                ),
            ],
        ),
        migrations.DeleteModel(
            name="OUSettingDefault",
        ),
        migrations.AddConstraint(
            model_name="orgusersettingdefault",
            constraint=models.UniqueConstraint(
                fields=("org", "setting"), name="unique_org_user_setting_defaults"
            ),
        ),
    ]
