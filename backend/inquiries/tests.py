from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.core import mail
from django.conf import settings

from inquiries.models import ServiceInquiry
from products.models import PrintingService # Assuming PrintingService is in products.models

class ServiceInquiryViewSetTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.service = PrintingService.objects.create(
            name='Test Service for Inquiry',
            description='A test service',
            base_price=100.00,
            price_per_gram=1.0,
            price_per_hour=10.0
        )
        self.inquiry_data_with_service = {
            'name': 'Test User',
            'email': 'testuser@example.com',
            'phone': '1234567890',
            'message': 'This is a test inquiry for a specific service.',
            'service_id': self.service.pk
        }
        self.inquiry_data_general = {
            'name': 'Another User',
            'email': 'another@example.com',
            'message': 'This is a general test inquiry.'
        }
        self.admin_email_recipient = 'your_admin_email@example.com' # Default from settings template
        if hasattr(settings, 'ADMIN_EMAIL_FOR_INQUIRIES') and settings.ADMIN_EMAIL_FOR_INQUIRIES:
            self.admin_email_recipient = settings.ADMIN_EMAIL_FOR_INQUIRIES
        elif settings.ADMINS and settings.ADMINS[0] and len(settings.ADMINS[0]) > 1:
             self.admin_email_recipient = settings.ADMINS[0][1]

    def test_create_service_inquiry_with_service(self):
        url = reverse('serviceinquiry-list') # from public_router basename='serviceinquiry'
        response = self.client.post(url, self.inquiry_data_with_service, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ServiceInquiry.objects.count(), 1)
        inquiry = ServiceInquiry.objects.first()
        self.assertEqual(inquiry.name, self.inquiry_data_with_service['name'])
        self.assertEqual(inquiry.service, self.service)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to[0], self.admin_email_recipient)
        self.assertIn(self.service.name, mail.outbox[0].subject)

    def test_create_service_inquiry_general(self):
        url = reverse('serviceinquiry-list')
        response = self.client.post(url, self.inquiry_data_general, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ServiceInquiry.objects.count(), 1)
        inquiry = ServiceInquiry.objects.first()
        self.assertEqual(inquiry.name, self.inquiry_data_general['name'])
        self.assertIsNone(inquiry.service)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to[0], self.admin_email_recipient)
        self.assertIn('Общий запрос', mail.outbox[0].subject) # Check for general inquiry in subject

    def test_create_service_inquiry_invalid_data(self):
        url = reverse('serviceinquiry-list')
        invalid_data = {
            'name': 'Test User', 
            # Missing email and message
        }
        response = self.client.post(url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(ServiceInquiry.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    # TODO: Add tests for list, retrieve, update, delete for admin users via ManagementViewSet
    # These would require an authenticated admin user.
