from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.conf import settings
import stripe
from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderItemSerializer

stripe.api_key = settings.STRIPE_SECRET_KEY

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=user)
    
    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        order = self.get_object()
        serializer = OrderItemSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(order=order)
            order_serializer = OrderSerializer(order)
            return Response(order_serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def remove_item(self, request, pk=None):
        order = self.get_object()
        try:
            item_id = request.data.get('item_id')
            item = order.items.get(id=item_id)
            item.delete()
            order_serializer = OrderSerializer(order)
            return Response(order_serializer.data)
        except OrderItem.DoesNotExist:
            return Response(
                {'error': 'Item not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'], url_path='payment')
    def create_payment(self, request, pk=None):
        order = self.get_object()
        
        try:
            # Создаем платежную сессию Stripe
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'rub',
                        'unit_amount': int(order.get_total_cost() * 100),
                        'product_data': {
                            'name': f'Order #{order.id}',
                        },
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=request.data.get('success_url', 'http://localhost:3000/order/success'),
                cancel_url=request.data.get('cancel_url', 'http://localhost:3000/order/cancel'),
            )
            
            return Response({
                'session_id': session.id,
                'stripe_public_key': settings.STRIPE_PUBLIC_KEY
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'], url_path='payment/confirm')
    def confirm_payment(self, request, pk=None):
        order = self.get_object()
        session_id = request.data.get('session_id')
        
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            
            if session.payment_status == 'paid':
                order.paid = True
                order.stripe_payment_id = session.payment_intent
                order.status = 'processing'
                order.save()
                
                return Response({'status': 'Payment confirmed'})
            
            return Response(
                {'error': 'Payment not completed'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class AdminOrderPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = 'page_size' # Позволяет клиенту переопределить page_size, если нужно
    max_page_size = 100 # Опционально: максимальный размер страницы

class OrderManagementViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().order_by('-created') # Все заказы, последние сверху
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAdminUser]
    pagination_class = AdminOrderPagination # <--- Применяем кастомную пагинацию
    http_method_names = ['get', 'put', 'patch', 'head', 'options'] # Запрещаем POST (создание) и DELETE

    # Можно добавить фильтрацию и поиск, если нужно
    # filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    # filterset_fields = ['status', 'paid', 'user__email']
    # search_fields = ['id', 'user__email', 'address']
    # ordering_fields = ['created', 'status', 'total_cost']

    # perform_update можно переопределить для кастомной логики, 
    # например, отправки уведомлений при смене статуса
    # def perform_update(self, serializer):
    #     # ... ваша логика ...
    #     super().perform_update(serializer)
