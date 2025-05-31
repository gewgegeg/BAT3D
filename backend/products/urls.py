from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import (
    CategoryViewSet, 
    ProductViewSet, 
    PrintingServiceViewSet, 
    ProductManagementViewSet,
    CategoryManagementViewSet,
    PrintingServiceManagementViewSet
)

# Router for public API
router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'printing-services', PrintingServiceViewSet, basename='printingservice')
router.register(r'', ProductViewSet, basename='product')

# Router for management API (admin panel)
management_router = DefaultRouter()
management_router.register(r'products', ProductManagementViewSet, basename='management-product')
management_router.register(r'categories', CategoryManagementViewSet, basename='management-category')
management_router.register(r'printing-services', PrintingServiceManagementViewSet, basename='management-printing-service')
# TODO: Сюда же потом можно добавить management-category, management-service viewsets

urlpatterns = [
    path('', include(router.urls)),
    path('management/', include(management_router.urls)),
] 