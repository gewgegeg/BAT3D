from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from products.models import Category, Product, PrintingService
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.utils.text import slugify

# Импорты для очистки данных из других приложений, если необходимо
from orders.models import Order, OrderItem # Предполагаем, что могут быть созданы
from cart.models import Cart, CartItem     # Предполагаем, что могут быть созданы

User = get_user_model()

def clear_all_data():
    # Вспомогательная функция для полной очистки
    # Удаляем в порядке зависимостей, чтобы избежать ForeignKey constraint errors
    OrderItem.objects.all().delete()
    Order.objects.all().delete()
    CartItem.objects.all().delete()
    Cart.objects.all().delete()
    Product.objects.all().delete()
    PrintingService.objects.all().delete()
    Category.objects.all().delete()
    User.objects.all().delete()

class ProductViewSetTest(TestCase):
    def setUp(self):
        clear_all_data() # Очистка перед каждым тестовым методом
        
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='p_testuser',
            email='p_test@example.com',
            password='testpass123'
        )
        self.admin_user = User.objects.create_superuser(
            username='p_admin',
            email='p_admin@example.com',
            password='admin123'
        )
        
        self.category = Category.objects.create(
            name='P_Test Category',
            slug=slugify('P_Test Category'),
            description='Test Description'
        )
        
        self.category2 = Category.objects.create(
            name='P_Another Category',
            slug=slugify('P_Another Category'),
            description='Another Description'
        )
        
        self.product = Product.objects.create(
            name='P_Test Product',
            slug=slugify('P_Test Product'),
            description='Test Description',
            price=Decimal('99.99'),
            category=self.category,
            stock=100,
            available=True
        )
        
        self.product2 = Product.objects.create(
            name='P_Expensive Product',
            slug=slugify('P_Expensive Product'),
            description='Expensive Description',
            price=Decimal('199.99'),
            category=self.category2,
            stock=50,
            available=True
        )
        
        self.product3 = Product.objects.create(
            name='P_Cheap Product',
            slug=slugify('P_Cheap Product'),
            description='Cheap Description',
            price=Decimal('49.99'),
            category=self.category,
            stock=200,
            available=True
        )
        
        self.printing_service = PrintingService.objects.create(
            name='P_Test Service for Product Tests',
            description='Test Description',
            price_per_gram=Decimal('0.5'),
            min_weight=Decimal('10.00'),
            max_weight=Decimal('1000.00'),
            base_price=Decimal('10.00'),
            price_per_hour=Decimal('5.00'),
            available=True
        )

    def test_get_products_list(self):
        url = reverse('product-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)
        product_names = {product['name'] for product in response.data['results']}
        self.assertEqual(product_names, {'P_Test Product', 'P_Expensive Product', 'P_Cheap Product'})

    def test_get_product_detail(self):
        url = reverse('product-detail', kwargs={'pk': self.product.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'P_Test Product')

    def test_create_product_as_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('product-list')
        data = {
            'name': 'New Product',
            'slug': slugify('New Product'),
            'description': 'New Description',
            'price': '149.99',
            'category_id': self.category.id,
            'stock': 50,
            'available': True
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Product.objects.filter(name='New Product').exists())

    def test_create_product_as_regular_user(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('product-list')
        data = {
            'name': 'New Product Reg',
            'description': 'New Description Reg',
            'price': '149.99',
            'category_id': self.category.id,
            'stock': 50,
            'available': True
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_product_as_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('product-detail', kwargs={'pk': self.product.pk})
        updated_name = 'Updated Product Name'
        data = {
            'name': updated_name,
            'slug': slugify(updated_name),
            'description': 'Updated Description',
            'price': '199.99',
            'category_id': self.category.id,
            'stock': 75,
            'available': True
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, updated_name)
        self.assertEqual(self.product.slug, slugify(updated_name))

    def test_delete_product_as_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        
        initial_count = Product.objects.count()
        if True: 
            print(f"\nDEBUG (test_delete_product_as_admin): Initial product count: {initial_count}")
            all_products_before = list(Product.objects.values_list('id','name', 'slug'))
            print(f"DEBUG (test_delete_product_as_admin): All products before delete: {all_products_before}")
            print(f"DEBUG (test_delete_product_as_admin): Attempting to delete product with slug: {self.product.slug} (ID: {self.product.id})")

        url = reverse('product-detail', kwargs={'pk': self.product.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        final_count = Product.objects.count()
        deleted_product_exists = Product.objects.filter(id=self.product.id).exists()
        if True:
            print(f"DEBUG (test_delete_product_as_admin): Final product count: {final_count}")
            print(f"DEBUG (test_delete_product_as_admin): Deleted product (ID: {self.product.id}, slug: '{self.product.slug}') exists in DB: {deleted_product_exists}")
            all_products_after = list(Product.objects.values_list('id','name', 'slug'))
            print(f"DEBUG (test_delete_product_as_admin): All products after delete: {all_products_after}")
            
        self.assertFalse(deleted_product_exists, "Удаленный продукт все еще существует в БД")
        self.assertEqual(final_count, initial_count - 1, "Количество продуктов не уменьшилось на 1")

    def test_filter_products_by_category(self):
        url = reverse('product-list')
        response = self.client.get(url, {'category': self.category.slug})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        product_names = {product['name'] for product in response.data['results']}
        self.assertIn(self.product.name, product_names)
        self.assertIn(self.product3.name, product_names)

    def test_filter_products_by_price_range(self):
        url = reverse('product-list')
        response = self.client.get(url, {
            'min_price': '75.00',
            'max_price': '150.00'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], self.product.name)

    def test_filter_products_by_category_and_price(self):
        url = reverse('product-list')
        response = self.client.get(url, {
            'category': self.category.slug,
            'min_price': '75.00',
            'max_price': '150.00'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], self.product.name)

    def test_filter_products_by_availability(self):
        self.product2.available = False
        self.product2.save()
        
        url = reverse('product-list')
        response = self.client.get(url, {'available': 'true'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        product_names = {product['name'] for product in response.data['results']}
        self.assertIn(self.product.name, product_names)
        self.assertIn(self.product3.name, product_names)

    def test_create_product_without_image(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('product-list')
        data = {
            'name': 'Product Without Image',
            'slug': slugify('Product Without Image'),
            'description': 'Description without image',
            'price': '149.99',
            'category_id': self.category.id,
            'stock': 50,
            'available': True
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        product = Product.objects.get(name='Product Without Image')
        self.assertEqual(str(product.image), '')

    def test_update_product_without_image(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('product-detail', kwargs={'pk': self.product.pk})
        data = {
            'name': 'Updated Product W/O Image',
            'slug': slugify('Updated Product W/O Image'),
            'description': 'Updated description without image',
            'price': '199.99',
            'category_id': self.category.id,
            'stock': 75,
            'available': True,
            'image': ''
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, 'Updated Product W/O Image')
        self.assertEqual(str(self.product.image), '')

    def test_partial_update_product_without_image(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('product-detail', kwargs={'pk': self.product.pk})
        data = {
            'name': 'Partially Updated Product',
            'description': 'Partially updated description'
        }
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, 'Partially Updated Product')
        self.assertEqual(self.product.price, Decimal('99.99'))
        self.assertEqual(str(self.product.image), '')

class PrintingServiceViewSetTest(TestCase):
    def setUp(self):
        clear_all_data() # Очистка перед каждым тестовым методом

        self.client = APIClient()
        self.user = User.objects.create_user(
            username='ps_testuser',
            email='ps_test@example.com',
            password='testpass123'
        )
        self.admin_user = User.objects.create_superuser(
            username='ps_admin',
            email='ps_admin@example.com',
            password='admin123'
        )

        self.printing_service = PrintingService.objects.create(
            name='PS_Test Service',
            description='Test Description',
            price_per_gram=Decimal('0.5'),
            min_weight=Decimal('10.00'),
            max_weight=Decimal('1000.00'),
            base_price=Decimal('10.00'),
            price_per_hour=Decimal('5.00'),
            available=True
        )
        
        self.printing_service2 = PrintingService.objects.create(
            name='PS_Another Service',
            description='Another Description',
            price_per_gram=Decimal('0.75'),
            min_weight=Decimal('5.00'),
            max_weight=Decimal('500.00'),
            base_price=Decimal('15.00'),
            price_per_hour=Decimal('7.00'),
            available=False 
        )

    def test_get_services_list(self):
        url = reverse('printingservice-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_get_service_detail(self):
        url = reverse('printingservice-detail', kwargs={'pk': self.printing_service.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'PS_Test Service')

    def test_create_service_as_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('printingservice-list')
        data = {
            'name': 'New Printing Service',
            'description': 'New service description',
            'price_per_gram': '0.6',
            'min_weight': '12.00',
            'max_weight': '1200.00',
            'base_price': '12.00',
            'price_per_hour': '6.00',
            'available': True
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(PrintingService.objects.filter(name='New Printing Service', available=True).exists())

    def test_create_service_as_regular_user(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('printingservice-list')
        data = { 'name': 'Unauthorized PS' }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_service_as_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('printingservice-detail', kwargs={'pk': self.printing_service.pk})
        updated_name = 'Updated PS Name'
        data = {
            'name': updated_name,
            'description': 'Updated service description',
            'price_per_gram': '0.55',
            'min_weight': '10.00',
            'max_weight': '1100.00',
            'base_price': '11.00',
            'price_per_hour': '5.50',
            'available': False
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.printing_service.refresh_from_db()
        self.assertEqual(self.printing_service.name, updated_name)
        self.assertEqual(self.printing_service.available, False)

    def test_update_service_as_regular_user(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('printingservice-detail', kwargs={'pk': self.printing_service.pk})
        data = {'name': 'Attempted Update PS'}
        response = self.client.patch(url, data) 
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_service_as_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('printingservice-detail', kwargs={'pk': self.printing_service.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(PrintingService.objects.filter(pk=self.printing_service.pk).exists())

    def test_delete_service_as_regular_user(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('printingservice-detail', kwargs={'pk': self.printing_service.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

class CategoryViewSetTest(TestCase):
    def setUp(self):
        clear_all_data() # Очистка перед каждым тестовым методом

        self.client = APIClient()
        self.user = User.objects.create_user(
            username='cat_testuser',
            email='cat_test@example.com',
            password='testpass123'
        )
        self.admin_user = User.objects.create_superuser(
            username='cat_admin',
            email='cat_admin@example.com',
            password='admin123'
        )
        
        self.category = Category.objects.create(
            name='CAT_Electronics',
            slug='cat_electronics',
            description='Gadgets and devices'
        )
        self.category2 = Category.objects.create(
            name='CAT_Books',
            slug='cat_books',
            description='Printed and digital books'
        )

    def test_get_categories_list(self):
        url = reverse('category-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_get_category_detail(self):
        url = reverse('category-detail', kwargs={'slug': self.category.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'CAT_Electronics')

    def test_create_category_as_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('category-list')
        data = {
            'name': 'New Test Category',
            'slug': slugify('New Test Category'),
            'description': 'A description for the new category.'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Category.objects.filter(name='New Test Category').exists())

    def test_create_category_as_regular_user(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('category-list')
        data = {'name': 'Unauthorized Category', 'slug': 'unauthorized-category'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_category_as_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('category-detail', kwargs={'slug': self.category.slug})
        updated_name = 'Updated CAT Electronics'
        data = {
            'name': updated_name,
            'slug': slugify(updated_name),
            'description': 'Updated description for electronics'
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.category.refresh_from_db()
        self.assertEqual(self.category.name, updated_name)
        self.assertEqual(self.category.slug, slugify(updated_name))

    def test_delete_category_as_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('category-detail', kwargs={'slug': self.category.slug})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Category.objects.filter(slug=self.category.slug).exists()) 