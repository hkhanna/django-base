# Generated by Django 3.2.13 on 2022-11-01 16:05

from django.db import migrations
from email.utils import parseaddr


def forwards_func(apps, schema_editor):
    EmailMessage = apps.get_model("base", "EmailMessage")
    for email_message in EmailMessage.objects.all():
        email_message.sender_name, email_message.sender_email = parseaddr(
            email_message.sender
        )

        email_message.reply_to_name, email_message.reply_to_email = parseaddr(
            email_message.reply_to
        )

        email_message.full_clean()
        email_message.save()


class Migration(migrations.Migration):

    dependencies = [
        ("base", "0008_auto_20221101_1523"),
    ]

    operations = [
        migrations.RunPython(
            forwards_func, reverse_code=migrations.RunPython.noop, elidable=True
        )
    ]