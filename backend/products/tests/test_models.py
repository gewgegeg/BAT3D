from django.test import TestCase
from products.models import Category, Product, PrintingService
from decimal import Decimal

class CategoryModelTest(TestCase):
    def setUp(self):
        Product.objects.all().delete()
        Category.objects.all().delete()
        PrintingService.objects.all().delete()
        self.category = Category.objects.create(
            name='Test Category',
            description='Test Description',
            slug='test-category'
        )

    def test_category_creation(self):
        self.assertEqual(self.category.name, 'Test Category')
        self.assertEqual(self.category.description, 'Test Description')
        self.assertEqual(self.category.slug, 'test-category')

    def test_category_str(self):
        self.assertEqual(str(self.category), 'Test Category')

class ProductModelTest(TestCase):
    def setUp(self):
        Product.objects.all().delete()
        Category.objects.all().delete()
        PrintingService.objects.all().delete()
        self.category = Category.objects.create(
            name='Test Category',
            description='Test Description',
            slug='test-category'
        )
        self.product = Product.objects.create(
            name='Test Product',
            description='Test Description',
            price=Decimal('99.99'),
            category=self.category,
            stock=10,
            available=True,
            slug='test-product'
        )

    def test_product_creation(self):
        self.assertEqual(self.product.name, 'Test Product')
        self.assertEqual(self.product.price, Decimal('99.99'))
        self.assertEqual(self.product.category, self.category)
        self.assertEqual(self.product.stock, 10)
        self.assertTrue(self.product.available)

    def test_product_str(self):
        self.assertEqual(str(self.product), 'Test Product')

class PrintingServiceModelTest(TestCase):
    def setUp(self):
        Product.objects.all().delete()
        Category.objects.all().delete()
        PrintingService.objects.all().delete()
        self.service = PrintingService.objects.create(
            name='Test Service',
            description='Test Description',
            base_price=Decimal('10.00'),
            price_per_gram=Decimal('0.50'),
            price_per_hour=Decimal('5.00'),
            available=True,
            icon='speed',
            min_weight=Decimal('10.00'),
            max_weight=Decimal('1000.00')
        )

    def test_printing_service_creation(self):
        self.assertEqual(self.service.name, 'Test Service')
        self.assertEqual(self.service.base_price, Decimal('10.00'))
        self.assertEqual(self.service.price_per_gram, Decimal('0.50'))
        self.assertEqual(self.service.price_per_hour, Decimal('5.00'))
        self.assertTrue(self.service.available)

    def test_printing_service_str(self):
        self.assertEqual(str(self.service), 'Test Service') 