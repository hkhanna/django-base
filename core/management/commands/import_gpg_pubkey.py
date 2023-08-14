from django.conf import settings
from django.core.management.base import BaseCommand


PUBKEY_FILEPATH = settings.BASE_DIR / "base-fedora.asc"


class Command(BaseCommand):
    help = "Import GPG public key"

    def handle(self, *args, **options):
        import gnupg

        gpg = gnupg.GPG()
        import_result = gpg.import_keys_file(PUBKEY_FILEPATH)
        key = gpg.list_keys()[0]
        assert settings.DBBACKUP_GPG_RECIPIENT in key["uids"][0]
