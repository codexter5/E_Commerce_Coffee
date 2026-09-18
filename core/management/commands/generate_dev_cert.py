import shutil
import subprocess
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = (
        "Generates a self-signed TLS certificate for local HTTPS testing only "
        "(via `runserver_ssl`). Never use this certificate in production -- "
        "browsers will show a security warning since it isn't signed by a "
        "trusted authority, which is expected for local development."
    )

    def add_arguments(self, parser):
        parser.add_argument("--out-dir", default=str(Path(settings.BASE_DIR) / "certs"), help="Directory to write dev-cert.pem / dev-key.pem into.")
        parser.add_argument("--days", type=int, default=365, help="Certificate validity period in days.")
        parser.add_argument("--force", action="store_true", help="Overwrite existing cert/key files if present.")

    def handle(self, *args, **options):
        if shutil.which("openssl") is None:
            raise CommandError(
                "openssl was not found on PATH. Install it (it ships with most Linux/macOS "
                "systems; on Windows use WSL or Git Bash), or generate a cert with a tool of "
                "your choice and point `runserver_ssl --cert --key` at the files directly."
            )

        out_dir = Path(options["out_dir"])
        out_dir.mkdir(parents=True, exist_ok=True)
        certfile = out_dir / "dev-cert.pem"
        keyfile = out_dir / "dev-key.pem"

        if not options["force"] and (certfile.exists() or keyfile.exists()):
            raise CommandError(
                f"{certfile} or {keyfile} already exists. Pass --force to overwrite, "
                f"or delete them yourself first."
            )

        subprocess.run(
            [
                "openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
                "-keyout", str(keyfile), "-out", str(certfile),
                "-days", str(options["days"]),
                "-subj", "/CN=localhost",
                "-addext", "subjectAltName=DNS:localhost,IP:127.0.0.1",
            ],
            check=True,
            capture_output=True,
        )

        self.stdout.write(self.style.SUCCESS(f"Generated {certfile} and {keyfile} (valid {options['days']} days)."))
        self.stdout.write("Run the HTTPS dev server with:  python manage.py runserver_ssl")
