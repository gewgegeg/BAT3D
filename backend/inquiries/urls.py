from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import ServiceInquiryViewSet, ServiceInquiryManagementViewSet

# Router for public API (submitting inquiries)
public_router = DefaultRouter()
public_router.register(r'service-inquiries', ServiceInquiryViewSet, basename='serviceinquiry')

# Router for management API (admin panel use)
management_router = DefaultRouter()
management_router.register(r'service-inquiries', ServiceInquiryManagementViewSet, basename='management-serviceinquiry')

urlpatterns = [
    path('', include(public_router.urls)),
    path('management/', include(management_router.urls)),
] 