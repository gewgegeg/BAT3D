from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from django_filters import rest_framework as filters
from django.utils.text import slugify
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Category, Product, PrintingService
from .serializers import (
    CategorySerializer,
    ProductSerializer,
    PrintingServiceSerializer
)
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.response import Response

# Create your views here.

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAdminUser]
    lookup_field = 'slug'
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return super().get_permissions()

class ProductFilter(filters.FilterSet):
    min_price = filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = filters.NumberFilter(field_name='price', lookup_expr='lte')
    category = filters.CharFilter(field_name='category__slug')
    available = filters.BooleanFilter()
    
    class Meta:
        model = Product
        fields = ['category', 'available', 'min_price', 'max_price']

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAdminUser]
    filterset_class = ProductFilter
    lookup_field = 'pk'
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return super().get_permissions()
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == 'list' and 'available' not in self.request.query_params:
            queryset = queryset.filter(available=True)
        return queryset

class PrintingServiceViewSet(viewsets.ModelViewSet):
    queryset = PrintingService.objects.filter(available=True)
    serializer_class = PrintingServiceSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return super().get_permissions()
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action in ['list', 'retrieve']:
            return queryset.filter(available=True)
        return queryset

class ProductManagementViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all() # Для админки показываем все, не только available=True
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAdminUser] # Только администраторы могут управлять продуктами
    parser_classes = [MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProductFilter # Можно использовать тот же фильтр, если он подходит
    search_fields = ['name', 'description', 'category__name'] # Поля для поиска
    ordering_fields = ['name', 'price', 'stock', 'created_at'] # Поля для сортировки
    # lookup_field = 'id' # По умолчанию pk, что соответствует id

    def create(self, request, *args, **kwargs):
        # print("ProductManagementViewSet CREATE - Request Content-Type header:", request.content_type)
        # try:
        #     print("ProductManagementViewSet CREATE - Request body (first 500 bytes):", request.body[:500])
        # except Exception as e:
        #     print("ProductManagementViewSet CREATE - Error reading request.body:", e)
        # 
        # print("ProductManagementViewSet CREATE - Request data (after DRF parsing):", request.data)
        # print("ProductManagementViewSet CREATE - Request FILES (after DRF parsing):", request.FILES)
        
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            # print("ProductManagementViewSet CREATE - Validation error:", e)
            # print("ProductManagementViewSet CREATE - Serializer errors:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        name = serializer.validated_data.get('name')
        if not name:
            # Если имя не предоставлено, DRF должен был бы выдать ошибку валидации раньше,
            # если поле name обязательное. Если оно не обязательное и slug нужен,
            # то нужна другая логика генерации слага или установка slug как allow_blank=True.
            # Для текущего сценария предполагаем, что name всегда есть.
            super().perform_create(serializer) # Позволяем стандартному методу обработать (возможно, с ошибкой)
            return

        original_slug = slugify(name)
        slug = original_slug
        counter = 1
        # Product._meta.model это Product class (self.queryset.model)
        while self.queryset.model.objects.filter(slug=slug).exists():
            slug = f'{original_slug}-{counter}'
            counter += 1
        serializer.save(slug=slug)

class CategoryManagementViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAdminUser]
    # Для админ-панели обычно удобнее использовать ID для lookup
    # lookup_field = 'id' # Это значение по умолчанию, если не указано другое

    # Можно добавить фильтрацию, поиск, сортировку, если необходимо,
    # по аналогии с ProductManagementViewSet
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'slug', 'description']
    ordering_fields = ['name', 'slug']

    def perform_create(self, serializer):
        name = serializer.validated_data.get('name')
        if not name:
            super().perform_create(serializer)
            return

        original_slug = slugify(name)
        slug = original_slug
        counter = 1
        while self.queryset.model.objects.filter(slug=slug).exists():
            slug = f'{original_slug}-{counter}'
            counter += 1
        serializer.save(slug=slug)

class PrintingServiceManagementViewSet(viewsets.ModelViewSet):
    queryset = PrintingService.objects.all() # Показываем все услуги для админки
    serializer_class = PrintingServiceSerializer
    permission_classes = [permissions.IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]
    # lookup_field = 'id' # PK по умолчанию

    # Можно добавить фильтрацию, поиск, сортировку, если необходимо
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    # filterset_fields = ['available'] # Пример фильтрации по доступности
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'base_price', 'available']

    # Если для услуг нужна своя логика при создании/обновлении (например, обработка materials),
    # можно переопределить perform_create, perform_update
