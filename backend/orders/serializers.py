from rest_framework import serializers
from .models import Order, OrderItem
from products.models import Product, PrintingService
from products.serializers import ProductSerializer, PrintingServiceSerializer
from users.serializers import UserSerializer

class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        write_only=True,
        source='product',
        required=False
    )
    printing_service = PrintingServiceSerializer(read_only=True)
    printing_service_id = serializers.PrimaryKeyRelatedField(
        queryset=PrintingService.objects.all(),
        write_only=True,
        source='printing_service',
        required=False
    )
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'order', 'product', 'product_id',
            'printing_service', 'printing_service_id',
            'price', 'quantity', 'weight', 'printing_time'
        ]
        read_only_fields = ['order']
    
    def validate(self, data):
        """
        Проверяем, что указан либо продукт, либо услуга печати
        """
        product = data.get('product')
        printing_service = data.get('printing_service')
        
        if not product and not printing_service:
            raise serializers.ValidationError(
                "Either product or printing service must be specified."
            )
        if product and printing_service:
            raise serializers.ValidationError(
                "Cannot specify both product and printing service."
            )
            
        if printing_service:
            if not data.get('weight'):
                raise serializers.ValidationError(
                    "Weight must be specified for printing service."
                )
            if not data.get('printing_time'):
                raise serializers.ValidationError(
                    "Printing time must be specified for printing service."
                )
        
        return data

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user = UserSerializer(read_only=True)
    date = serializers.DateTimeField(source='created', read_only=True)
    total = serializers.DecimalField(source='get_total_cost', max_digits=10, decimal_places=2, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 
            'user',
            'address', 
            'date',
            'updated',
            'status',
            'status_display',
            'paid', 
            'stripe_payment_id',
            'yookassa_payment_id',
            'items',
            'total'
        ]
        read_only_fields = [
            'user',
            'date',
            'updated',
            'paid',
            'stripe_payment_id',
            'yookassa_payment_id',
            'status_display',
            'items',
            'total'
        ]
    
    def create(self, validated_data):
        user_context = self.context['request'].user
        validated_data['user'] = user_context
        return super().create(validated_data) 