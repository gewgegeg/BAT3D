from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    HomePageSettingsViewSet,
    HeroSlideImageViewSet,
    AboutUsImageViewSet,
    WorkGalleryImageViewSet
)

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'hero-slides', HeroSlideImageViewSet, basename='hero-slide')
router.register(r'about-us-images', AboutUsImageViewSet, basename='about-us-image')
router.register(r'work-gallery-images', WorkGalleryImageViewSet, basename='work-gallery-image')

# The API URLs are now determined automatically by the router.
# urlpatterns = router.urls # This would replace the manual urlpatterns if only using router

# Since HomePageSettings is a singleton, we don't use a router that generates pk-based URLs.
# We define specific paths for the actions.
urlpatterns = [
    path(
        'settings/', 
        HomePageSettingsViewSet.as_view({
            'get': 'list', 
            'put': 'update',
            'patch': 'partial_update'
        }), 
        name='homepage-settings'
    ),
    # Add the router URLs to our urlpatterns
    path('', include(router.urls)), 
] 