from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='name')),
                ('slug', models.SlugField(max_length=200, unique=True, verbose_name='slug')),
                ('description', models.TextField(blank=True, verbose_name='description')),
            ],
            options={
                'verbose_name': 'category',
                'verbose_name_plural': 'categories',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='PrintingMaterial',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='name')),
                ('description', models.TextField(verbose_name='description')),
                ('price_multiplier', models.DecimalField(decimal_places=2, max_digits=4, verbose_name='price multiplier')),
                ('color', models.CharField(max_length=50, verbose_name='color')),
                ('properties', models.TextField(blank=True, default='', verbose_name='properties')),
            ],
            options={
                'verbose_name': 'printing material',
                'verbose_name_plural': 'printing materials',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='name')),
                ('slug', models.SlugField(max_length=200, unique=True, verbose_name='slug')),
                ('image', models.ImageField(blank=True, upload_to='products/%Y/%m/%d/', verbose_name='image')),
                ('description', models.TextField(blank=True, verbose_name='description')),
                ('price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='price')),
                ('stock', models.PositiveIntegerField(verbose_name='stock')),
                ('available', models.BooleanField(default=True, verbose_name='available')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='created')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='updated')),
                ('category', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='products', to='products.category', verbose_name='category')),
            ],
            options={
                'verbose_name': 'product',
                'verbose_name_plural': 'products',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='PrintingService',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='name')),
                ('description', models.TextField(verbose_name='description')),
                ('base_price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='base price')),
                ('price_per_gram', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='price per gram')),
                ('price_per_hour', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='price per hour')),
                ('min_weight', models.DecimalField(decimal_places=2, default=10.0, max_digits=10, verbose_name='minimum weight')),
                ('max_weight', models.DecimalField(decimal_places=2, default=1000.0, max_digits=10, verbose_name='maximum weight')),
                ('available', models.BooleanField(default=True, verbose_name='available')),
                ('features', models.TextField(blank=True, default='', verbose_name='features')),
                ('icon', models.CharField(choices=[('speed', 'Fast Printing'), ('quality', 'High Quality'), ('modeling', '3D Modeling'), ('painting', 'Painting'), ('support', 'Support'), ('delivery', 'Delivery')], default='speed', max_length=50, verbose_name='icon')),
                ('estimated_delivery_days', models.PositiveIntegerField(default=3, verbose_name='estimated delivery days')),
                ('materials', models.ManyToManyField(blank=True, related_name='services', to='products.printingmaterial', verbose_name='materials')),
            ],
            options={
                'verbose_name': 'printing service',
                'verbose_name_plural': 'printing services',
                'ordering': ['name'],
            },
        ),
    ] 