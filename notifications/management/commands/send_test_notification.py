from django.core.management.base import BaseCommand

from notifications.services import notification_config_status, send_test_notification


class Command(BaseCommand):
    help = "Send a real test email/WhatsApp message using the current .env settings, and print exactly what happened."

    def add_arguments(self, parser):
        parser.add_argument("--email", help="Email address to send the test message to.")
        parser.add_argument("--phone", help="Phone number to send the test WhatsApp message to (local or +E.164).")

    def handle(self, *args, **options):
        status = notification_config_status()
        self.stdout.write(self.style.MIGRATE_HEADING("Current notification configuration:"))
        self.stdout.write(f"  Channels enabled: {status['channels'] or '(none -- set ORDER_NOTIFICATION_CHANNELS in .env)'}")

        email_status = status["email"]
        self.stdout.write(f"  Email backend: {email_status['backend']}")
        if email_status["is_console_backend"]:
            self.stdout.write(self.style.WARNING(
                "    -> This is the console backend: messages print here, they are NOT actually emailed. "
                "Set EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend in .env to send for real."
            ))
        self.stdout.write(f"  EMAIL_HOST_USER set: {email_status['host_user_set']}, EMAIL_HOST_PASSWORD set: {email_status['host_password_set']}")

        wa_status = status["whatsapp"]
        self.stdout.write(f"  Twilio SID set: {wa_status['sid_set']}, token set: {wa_status['token_set']}, from set: {wa_status['from_set']}")
        self.stdout.write("")

        email = options.get("email")
        phone = options.get("phone")
        if not email and not phone:
            self.stdout.write(self.style.WARNING(
                "No --email or --phone given -- showing configuration only. "
                "Pass --email you@example.com and/or --phone 98XXXXXXXX to actually send a test message."
            ))
            return

        results = send_test_notification(email=email, phone=phone)
        self.stdout.write(self.style.MIGRATE_HEADING("Test send results:"))
        for channel, detail in results.items():
            style = self.style.ERROR if "FAILED" in str(detail) or channel == "error" else self.style.SUCCESS
            self.stdout.write(f"  {channel}: {style(str(detail))}")
