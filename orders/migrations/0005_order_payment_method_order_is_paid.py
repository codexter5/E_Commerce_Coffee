from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0004_normalize_legacy_statuses"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="payment_method",
            field=models.CharField(
                choices=[
                    ("CARD", "Credit / Debit Card"),
                    ("KHALTI", "Khalti"),
                    ("ESEWA", "eSewa"),
                    ("COD", "Cash on Delivery"),
                ],
                default="CARD",
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name="order",
            name="is_paid",
            field=models.BooleanField(default=False),
        ),
    ]
