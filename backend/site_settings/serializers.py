from rest_framework import serializers
from .models import HomePageSettings, HeroSlideImage, AboutUsImage, WorkGalleryImage

class HomePageSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = HomePageSettings
        fields = '__all__'

class HeroSlideImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = HeroSlideImage
        fields = ['id', 'image', 'order']

class AboutUsImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AboutUsImage
        fields = ['id', 'image', 'order']

class WorkGalleryImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkGalleryImage
        # Intentionally excluding title, description, link for now as per user request for API simplification
        # They remain in the model for potential future use or direct Django admin management.
        fields = ['id', 'image', 'order'] 