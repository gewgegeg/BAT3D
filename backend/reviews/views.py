from rest_framework import viewsets, permissions
from .models import Review
from .serializers import ReviewSerializer

class ReviewViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A viewset for viewing published reviews.
    """
    queryset = Review.objects.filter(is_visible=True)
    serializer_class = ReviewSerializer
    permission_classes = [permissions.AllowAny]

class ReviewManagementViewSet(viewsets.ModelViewSet):
    """
    A viewset for managing reviews in the admin panel.
    """
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAdminUser] # Only admins can manage reviews 