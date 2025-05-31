from django.urls import path, include # Добавляем include
from rest_framework.routers import DefaultRouter # Используем DefaultRouter, если rest_framework_nested не нужен явно здесь
# from rest_framework_nested import routers # Убрано
# from .views import CartViewSet, CartItemViewSet # CartViewSet больше не используется напрямую здесь
from .views import MinimalCartView, CartItemViewSet # Импортируем MinimalCartView и CartItemViewSet

# Если CartItemViewSet все еще нужен для /api/items/, его роутер можно оставить или переделать на path()
# Для чистоты эксперимента с GET /api/cart/, оставим только MinimalCartView

# Восстанавливаем роутер для CartItemViewSet, чтобы /api/cart/items/ работал
# Это важно, чтобы фронтенд мог добавлять товары и мы могли тестировать GET /api/cart/
router_items = DefaultRouter()
router_items.register(r'items', CartItemViewSet, basename='cart-item')

# router = routers.DefaultRouter()
# router.register(r'cart', CartViewSet, basename='cart') # Закомментировано

# cart_item_router = routers.DefaultRouter()
# cart_item_router.register(r'items', CartItemViewSet, basename='cart-items') # Пока закомментируем, если CartItemViewSet не нужен для этого теста

urlpatterns = [
    # path('', include(router.urls)), # Закомментировано
    # path('', include(cart_item_router.urls)), # Закомментировано
    path('', MinimalCartView.as_view(), name='minimal-cart'), # /api/cart/ будет обрабатываться MinimalCartView.get()
    path('', include(router_items.urls)), # Это добавит /api/cart/items/ (если основной urls.py path('api/cart/', include('cart.urls')) )
    # Если вам нужны URL-ы для CartItemViewSet (например, /api/cart/items/), их нужно будет добавить отдельно.
    # Например, если ваш основной urls.py такой: path('api/cart/', include('cart.urls'))
    # то для /api/cart/items/ можно сделать так:
    # path('items/', CartItemViewSet.as_view({'get': 'list', 'post': 'create'}), name='cartitem-list-create'),
    # path('items/<int:pk>/', CartItemViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name='cartitem-detail'),
] 