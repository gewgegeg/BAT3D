from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import UserViewSet

router = DefaultRouter()
router.register('', UserViewSet)

urlpatterns = [
    path('profile/', UserViewSet.as_view({'get': 'me', 'put': 'me', 'patch': 'me'}), name='user-profile'),
    path('', include(router.urls)),
] 