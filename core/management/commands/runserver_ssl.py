import ssl
from pathlib import Path

from django.conf import settings
from django.core.management.base import CommandError
from django.contrib.staticfiles.management.commands.runserver import Command as RunServerCommand
from django.core.servers.basehttp import WSGIServer


class SSLWSGIServer(WSGIServer):
    """Same as Django's dev WSGIServer, but wraps the listening socket in TLS
    once it's bound. certfile/keyfile are set as class attributes right
    before this server class is handed to django.core.servers.basehttp.run(),
    since that function's call site doesn't let us pass extra constructor
    arguments through."""

    certfile = None
    keyfile = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certfile=self.certfile, keyfile=self.keyfile)
        self.socket = context.wrap_socket(self.socket, server_side=True)


class Command(RunServerCommand):
    help = (
        "Runs the development server over HTTPS using a local self-signed "
        "certificate (see `generate_dev_cert`). For local testing only -- "
        "browsers will warn about the untrusted certificate, which is "
        "expected. Real deployments should terminate TLS at a reverse proxy "
        "or hosting platform, not here."
    )
    protocol = "https"

    def add_arguments(self, parser):
        super().add_arguments(parser)
        default_dir = Path(settings.BASE_DIR) / "certs"
        parser.add_argument("--cert", default=str(default_dir / "dev-cert.pem"), help="Path to the TLS certificate file.")
        parser.add_argument("--key", default=str(default_dir / "dev-key.pem"), help="Path to the TLS private key file.")

    def execute(self, *args, **options):
        certfile = Path(options.pop("cert"))
        keyfile = Path(options.pop("key"))
        if not certfile.exists() or not keyfile.exists():
            raise CommandError(
                f"Certificate not found at {certfile} or key not found at {keyfile}.\n"
                f"Run `python manage.py generate_dev_cert` first, or pass --cert/--key "
                f"to point at your own certificate."
            )
        SSLWSGIServer.certfile = str(certfile)
        SSLWSGIServer.keyfile = str(keyfile)
        self.server_cls = SSLWSGIServer
        return super().execute(*args, **options)
