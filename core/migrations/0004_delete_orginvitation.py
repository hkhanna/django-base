# Generated by Django 4.2.8 on 2024-01-24 16:08

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0003_remove_org_unique_personal_active_org_and_more"),
    ]

    operations = [
        migrations.DeleteModel(
            name="OrgInvitation",
        ),
    ]
