import os
from django.apps import apps
import importlib

from django.core.management.base import BaseCommand
from django.db import transaction
from django_celery_beat.models import IntervalSchedule, CrontabSchedule, PeriodicTask


class Command(BaseCommand):
    help = f"""Setup celery beat periodic tasks."""

    @transaction.atomic
    def handle(self, *args, **kwargs):
        print("Deleting all periodic tasks and schedules...\n")

        # Grab the periodic variable from the top level of every app's tasks.py.
        periodic_specs = []

        # Iterate over all installed apps
        for app_config in apps.get_app_configs():
            # Check if tasks.py exists in the app's directory
            tasks_path = os.path.join(app_config.path, "tasks.py")

            if os.path.exists(tasks_path):
                # Dynamically import the tasks module from the app
                module_name = f"{app_config.name}.tasks"
                tasks_module = importlib.import_module(module_name)

                # Check if the `periodic` variable exists in the module
                if hasattr(tasks_module, "periodic"):
                    periodic = getattr(tasks_module, "periodic")
                    periodic_specs += periodic

        IntervalSchedule.objects.all().delete()
        CrontabSchedule.objects.all().delete()
        PeriodicTask.objects.all().delete()

        for periodic_task in periodic_specs:
            print(f"Setting up {periodic_task['task'].name}")

            cron, _ = CrontabSchedule.objects.get_or_create(**periodic_task["cron"])

            PeriodicTask.objects.create(
                name=periodic_task["name"],
                task=periodic_task["task"].name,
                crontab=cron,
                enabled=periodic_task["enabled"],
            )
