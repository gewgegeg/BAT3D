from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from products.models import Product, PrintingService, Category
from .models import Cart, CartItem
from decimal import Decimal
from django.utils.text import slugify
from django.conf import settings

User = get_user_model()

class CartTests(TestCase):
    def setUp(self):
        # Явная очистка в setUp для TestCase (хотя транзакции должны изолировать)
        CartItem.objects.all().delete()
        Cart.objects.all().delete()
        Product.objects.all().delete()
        PrintingService.objects.all().delete()
        Category.objects.all().delete()
        User.objects.all().delete()
        
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testcartuser',
            email='testcart@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        self.category = Category.objects.create(
            name='Test Category For Cart',
            slug=slugify('Test Category For Cart')
        )
        
        self.product = Product.objects.create(
            name='Test Product For Cart',
            slug=slugify('Test Product For Cart'),
            description='Test Description',
            price=Decimal('100.00'),
            stock=10,
            category=self.category,
            available=True
        )
        
        self.service = PrintingService.objects.create(
            name='Test Service For Cart',
            description='Test Service Description',
            base_price=Decimal('50.00'),
            price_per_gram=Decimal('2.00'),
            price_per_hour=Decimal('30.00'),
            min_weight=Decimal('10.00'),
            max_weight=Decimal('1000.00'),
            available=True
        )

    def test_create_cart_and_add_product(self):
        """Test adding a product, which should create cart and item."""
        add_item_url = reverse('cart-items-list')
        data = {
            'product': self.product.id,
            'quantity': 1
        }
        response = self.client.post(add_item_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Cart.objects.filter(user=self.user).exists())
        cart = Cart.objects.get(user=self.user)
        self.assertEqual(cart.items.count(), 1)
        self.assertEqual(cart.items.first().product, self.product)
        self.assertEqual(cart.items.first().quantity, 1)

    def test_add_product_to_existing_cart_item(self):
        """Test adding a product that is already in cart (updates quantity)."""
        # Сначала создаем корзину и добавляем в нее товар
        cart = Cart.objects.create(user=self.user)
        created_item = CartItem.objects.create(
            cart=cart, 
            product=self.product, 
            quantity=1
        )
        
        add_item_url = reverse('cart-items-list')
        data = {
            'product': self.product.id, # ID того же продукта
            'quantity': 2 # Добавляем еще 2
        }
        response = self.client.post(add_item_url, data)
        
        # Так как товар уже есть в корзине, ожидаем HTTP_200_OK (обновление)
        self.assertEqual(response.status_code, status.HTTP_200_OK, 
                         f"Expected 200 OK, got {response.status_code}. Response data: {getattr(response, 'data', 'N/A')}") 
        
        cart.refresh_from_db()
        self.assertEqual(cart.items.count(), 1)
        self.assertEqual(cart.items.first().quantity, 3)

    def test_add_service_to_cart(self):
        """Test adding a printing service to cart."""
        add_item_url = reverse('cart-items-list')
        data = {
            'printing_service': self.service.id,
            'quantity': 1,
            'weight': Decimal('100.00'),
            'printing_time': Decimal('2.00')
        }
        response = self.client.post(add_item_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        cart = Cart.objects.get(user=self.user)
        self.assertEqual(cart.items.count(), 1)
        item = cart.items.first()
        self.assertEqual(item.printing_service, self.service)
        self.assertEqual(item.weight, Decimal('100.00'))

    def test_remove_item_from_cart(self):
        """Test removing an item from cart."""
        cart = Cart.objects.create(user=self.user)
        cart_item = CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=1
        )
        remove_url = reverse('cart-items-detail', kwargs={'pk': cart_item.pk})
        response = self.client.delete(remove_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(cart.items.count(), 0)

    def test_update_item_quantity(self):
        """Test updating item quantity in cart."""
        cart = Cart.objects.create(user=self.user)
        cart_item = CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=1
        )
        update_url = reverse('cart-items-detail', kwargs={'pk': cart_item.pk})
        data = {'quantity': 3}
        response = self.client.patch(update_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        cart_item.refresh_from_db()
        self.assertEqual(cart_item.quantity, 3)

    def test_clear_cart(self):
        """Test clearing the cart."""
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=1)
        CartItem.objects.create(cart=cart, printing_service=self.service, quantity=1, weight=10, printing_time=1)
        
        clear_url = reverse('cart-clear')
        response = self.client.post(clear_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(cart.items.count(), 0)

    def test_unauthorized_access_to_cart_list(self):
        """Test that unauthorized users cannot list/get cart details."""
        self.client.force_authenticate(user=None)
        cart_list_url = reverse('cart-list')
        response = self.client.get(cart_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthorized_access_to_cart_items(self):
        """Test that unauthorized users cannot access cart items."""
        self.client.force_authenticate(user=None)
        cart_items_url = reverse('cart-items-list')
        response = self.client.get(cart_items_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self.client.post(cart_items_url, {'product': self.product.id, 'quantity': 1})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
