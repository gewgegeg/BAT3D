from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import OrderViewSet, OrderManagementViewSet

router = DefaultRouter()
router.register('', OrderViewSet, basename='orders')

# Роутер для управления заказами в админ-панели
management_router = DefaultRouter()
management_router.register(r'management/orders', OrderManagementViewSet, basename='management-order')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(management_router.urls)),
] 