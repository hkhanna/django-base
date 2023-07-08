# Generated by Django 3.2.13 on 2022-10-30 23:51

from django.db import migrations

import uuid


def gen_uuid(apps, schema_editor):
    User = apps.get_model("base", "User")
    for row in User.objects.all():
        row.uuid = uuid.uuid4()
        row.save(update_fields=["uuid"])


class Migration(migrations.Migration):
    dependencies = [
        ("base", "0005_user_uuid"),
    ]

    operations = [
        migrations.RunPython(
            gen_uuid, reverse_code=migrations.RunPython.noop, elidable=True
        ),
    ]
