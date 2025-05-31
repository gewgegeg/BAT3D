from rest_framework import serializers
from .models import Cart, CartItem
from products.serializers import ProductSerializer, PrintingServiceSerializer

class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    printing_service = PrintingServiceSerializer(read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            'id', 'product', 'printing_service', 'quantity',
            'weight', 'printing_time', 'total_price'
        ]

    def get_total_price(self, obj):
        return obj.get_total_price()

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_cost = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'items', 'total_cost', 'created', 'updated']

    def get_total_cost(self, obj):
        return sum(item.get_total_price() for item in obj.items.all()) 