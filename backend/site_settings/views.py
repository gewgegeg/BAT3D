from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, AllowAny
from .models import HomePageSettings, HeroSlideImage, AboutUsImage, WorkGalleryImage
from .serializers import (
    HomePageSettingsSerializer, 
    HeroSlideImageSerializer, 
    AboutUsImageSerializer, 
    WorkGalleryImageSerializer
)

# Create your views here.

class HomePageSettingsViewSet(viewsets.ViewSet):
    """
    A ViewSet for retrieving and updating the singleton HomePageSettings.
    Allows GET to retrieve and PUT/PATCH to update the settings.
    """
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        AllowAny for GET (list) requests, IsAdminUser for PUT/PATCH (update/partial_update).
        """
        if self.action == 'list':
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]

    def list(self, request):
        """Handle GET requests to retrieve the home page settings."""
        settings_instance = HomePageSettings.load() # Use the load method to get or create
        serializer = HomePageSettingsSerializer(settings_instance)
        return Response(serializer.data)

    def update(self, request):
        """Handle PUT requests to update the home page settings."""
        settings_instance = HomePageSettings.load()
        serializer = HomePageSettingsSerializer(settings_instance, data=request.data, partial=False) # Use partial=False for PUT
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def partial_update(self, request):
        """Handle PATCH requests to partially update the home page settings."""
        settings_instance = HomePageSettings.load()
        serializer = HomePageSettingsSerializer(settings_instance, data=request.data, partial=True) # Use partial=True for PATCH
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Note: We are not using a ModelViewSet because we want to enforce a singleton
# behavior through the .load() method and specific actions (list, update, partial_update).
# Standard retrieve, create, destroy actions for a specific pk are not applicable here in the typical sense.

class BaseOrderedImageViewSet(viewsets.ModelViewSet):
    """
    Base ViewSet for ordered image models (Hero, AboutUs, Works).
    Allows GET (list, retrieve), POST (create), PUT (update), PATCH (partial_update), DELETE (destroy).
    Permissions: AllowAny for list/retrieve, IsAdminUser for modifications.
    """
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny] # Publicly viewable images
        else:
            permission_classes = [IsAdminUser] # Only admins can modify
        return [permission() for permission in permission_classes]

class HeroSlideImageViewSet(BaseOrderedImageViewSet):
    queryset = HeroSlideImage.objects.all().order_by('order')
    serializer_class = HeroSlideImageSerializer
    pagination_class = None # Отключаем пагинацию

class AboutUsImageViewSet(BaseOrderedImageViewSet):
    queryset = AboutUsImage.objects.all().order_by('order')
    serializer_class = AboutUsImageSerializer
    pagination_class = None # Отключаем пагинацию

class WorkGalleryImageViewSet(BaseOrderedImageViewSet):
    queryset = WorkGalleryImage.objects.all().order_by('order')
    serializer_class = WorkGalleryImageSerializer
    pagination_class = None # Отключаем пагинацию
    # Gallery is limited to 9 items on frontend, but API doesn't enforce this directly.
    # Order is important.
