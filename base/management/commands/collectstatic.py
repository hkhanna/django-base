import subprocess
from django.core.management import call_command
from django.contrib.staticfiles.management.commands.collectstatic import (
    Command as CollectStaticCommand,
)


class Command(CollectStaticCommand):
    def handle(self, *args, **options):
        subprocess.run(["npm", "run", "build", "--prefix", "base/frontend/"])
        super().handle(*args, **options)
