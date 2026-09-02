from django.db import migrations


def normalize_statuses(apps, schema_editor):
    Order = apps.get_model("orders", "Order")
    mapping = {
        "pending": "PLACED",
        "processing": "PREPARING",
        "shipped": "OUT_FOR_DELIVERY",
        "delivered": "DELIVERED",
        "cancelled": "CANCELLED",
    }
    for old_status, new_status in mapping.items():
        Order.objects.filter(status=old_status).update(status=new_status)


class Migration(migrations.Migration):
    dependencies = [("orders", "0003_order_delivery_person_order_seller_and_more")]

    operations = [migrations.RunPython(normalize_statuses, migrations.RunPython.noop)]
