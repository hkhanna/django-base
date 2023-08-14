# Generated by Django 4.2.3 on 2023-08-08 17:10

from django.db import migrations, models
import django.utils.timezone
import uuid


class Migration(migrations.Migration):
    dependencies = [
        ("core", "20230717_orgusersettingdefault_delete_ousettingdefault_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="GlobalSetting",
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
                ("slug", models.SlugField(max_length=254, unique=True)),
                (
                    "type",
                    models.CharField(
                        choices=[("bool", "Boolean"), ("int", "Integer")],
                        max_length=127,
                    ),
                ),
                ("value", models.IntegerField()),
            ],
            options={
                "abstract": False,
            },
        ),
    ]