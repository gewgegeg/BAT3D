from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReviewViewSet, ReviewManagementViewSet

router = DefaultRouter()
router.register(r'reviews', ReviewViewSet, basename='review')
router.register(r'management/reviews', ReviewManagementViewSet, basename='review-management')

urlpatterns = [
    path('', include(router.urls)),
] 