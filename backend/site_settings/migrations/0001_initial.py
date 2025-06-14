# Generated by Django 5.0.1 on 2025-05-20 03:29

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='HomePageSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('featured_products', models.JSONField(blank=True, default=list, help_text='List of product IDs or slugs to feature on the home page.', verbose_name='featured products')),
                ('featured_services', models.JSONField(blank=True, default=list, help_text='List of service IDs or slugs to feature on the home page.', verbose_name='featured services')),
            ],
            options={
                'verbose_name': 'Home Page Settings',
                'verbose_name_plural': 'Home Page Settings',
            },
        ),
    ]
