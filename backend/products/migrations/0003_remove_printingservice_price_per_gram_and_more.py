# Generated by Django 5.0.1 on 2025-05-21 20:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0002_alter_product_image'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='printingservice',
            name='price_per_gram',
        ),
        migrations.RemoveField(
            model_name='printingservice',
            name='price_per_hour',
        ),
        migrations.AlterField(
            model_name='printingservice',
            name='icon',
            field=models.ImageField(blank=True, null=True, upload_to='service_icons/', verbose_name='icon'),
        ),
    ]
