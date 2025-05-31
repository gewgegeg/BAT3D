from rest_framework import serializers
from .models import Category, Product, PrintingService, PrintingMaterial

class PrintingMaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrintingMaterial
        fields = ['id', 'name', 'description', 'price_multiplier', 'color', 'properties']

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description']
        read_only_fields = []

class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        write_only=True,
        source='category'
    )
    image = serializers.ImageField(required=False, allow_null=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'category', 'category_id', 'name', 'slug',
            'image', 'description', 'price', 'stock', 'available',
            'created', 'updated'
        ]
        read_only_fields = ['created', 'updated', 'slug']

class PrintingServiceSerializer(serializers.ModelSerializer):
    materials = PrintingMaterialSerializer(many=True, read_only=True)
    image = serializers.ImageField(required=False, allow_null=True, use_url=True)
    
    class Meta:
        model = PrintingService
        fields = [
            'id', 'name', 'description', 'base_price',
            'available',
            'min_weight', 'max_weight', 'features', 'image',
            'materials',
            'estimated_delivery_days'
        ]
        
    def validate(self, data):
        """
        Проверяем, что все цены положительные
        """
        for field in ['base_price']:
            if field in data and data[field] is not None and data[field] < 0:
                raise serializers.ValidationError(
                    f"{field} cannot be negative."
                )
        return data 