from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0005_order_payment_method_order_is_paid"),
    ]

    operations = [
        migrations.AddField(model_name="order", name="accepted_at", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="order", name="ready_at", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="order", name="picked_up_at", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="order", name="delivered_at", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="order", name="completed_at", field=models.DateTimeField(blank=True, null=True)),
    ]
