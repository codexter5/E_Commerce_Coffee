from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_profile_role'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='role',
            field=models.CharField(
                choices=[
                    ('BUYER', 'Buyer'),
                    ('SELLER', 'Seller'),
                    ('DELIVERY', 'Delivery Person'),
                    ('ADMIN', 'Admin'),
                ],
                default='BUYER',
                max_length=20,
            ),
        ),
    ]
