from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import ServiceInquiry
from .serializers import ServiceInquirySerializer
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
import logging

# For Management ViewSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

logger = logging.getLogger(__name__)

# Create your views here.

class ServiceInquiryViewSet(viewsets.ModelViewSet):
    queryset = ServiceInquiry.objects.all()
    serializer_class = ServiceInquirySerializer
    # permission_classes = [permissions.AllowAny] # Allow anyone to submit an inquiry - REVISED BELOW

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        # For list, retrieve, update, delete, only admins for the public API aspect
        return [permissions.IsAdminUser()]

    def perform_create(self, serializer):
        inquiry = serializer.save()
        # Send email notification to admin
        try:
            admin_email = getattr(settings, 'ADMIN_EMAIL_FOR_INQUIRIES', None)
            if not admin_email:
                # Fallback to settings.ADMINS if ADMIN_EMAIL_FOR_INQUIRIES is not set
                if settings.ADMINS and settings.ADMINS[0] and len(settings.ADMINS[0]) > 1:
                    admin_email = settings.ADMINS[0][1]
            
            if admin_email:
                subject = f"Новый запрос на услугу: {inquiry.service.name if inquiry.service else 'Общий запрос'} от {inquiry.name}"
                context = {
                    'inquiry': inquiry,
                    'site_url': settings.SITE_URL 
                }
                text_message = render_to_string('inquiries/email/new_inquiry_admin_notification.txt', context)
                html_message = render_to_string('inquiries/email/new_inquiry_admin_notification.html', context)
                
                send_mail(
                    subject=subject,
                    message=text_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[admin_email],
                    html_message=html_message,
                    fail_silently=False
                )
                logger.info(f"Admin notification email sent for inquiry {inquiry.id} to {admin_email}")
            else:
                logger.warning(f"Admin email for inquiries not configured. Cannot send notification for inquiry {inquiry.id}.")
        except Exception as e:
            logger.error(f"Error sending admin notification email for inquiry {inquiry.id}: {e}")

    # Optional: Override list/retrieve for admin to provide more/different data if needed
    # def list(self, request, *args, **kwargs):
    #     queryset = self.filter_queryset(self.get_queryset().order_by('-created_at')) # Ensure ordering
    #     page = self.paginate_queryset(queryset)
    #     if page is not None:
    #         serializer = self.get_serializer(page, many=True)
    #         return self.get_paginated_response(serializer.data)

    #     serializer = self.get_serializer(queryset, many=True)
    #     return Response(serializer.data)

class ServiceInquiryManagementViewSet(viewsets.ModelViewSet):
    queryset = ServiceInquiry.objects.all()
    serializer_class = ServiceInquirySerializer
    permission_classes = [permissions.IsAdminUser] # Only admins can manage inquiries
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'service'] # Fields for filtering
    search_fields = ['name', 'email', 'phone', 'message', 'service__name'] # Fields for searching
    ordering_fields = ['created_at', 'updated_at', 'status', 'name', 'service__name'] # Fields for ordering
    # lookup_field = 'pk' # Default

    # Admins should not create inquiries via this management endpoint,
    # they should only manage existing ones. Creation is for users.
    # So, disable/override create action if necessary, or rely on permissions.
    # For now, IsAdminUser on the whole viewset means they could create if they wanted to.
    # A more granular permission or overriding create() to return 405 would be stricter.
