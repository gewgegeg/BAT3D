"""
URL configuration for bat3d project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

# Удаляем заглушку для продуктов, так как будет использоваться ViewSet
# @api_view(['GET', 'POST', 'PUT', 'DELETE'])
# @permission_classes([IsAdminUser])
# def management_products_view(request, id=None):
#     ...

# Удаляем заглушку для категорий, так как будет использоваться CategoryManagementViewSet
# @api_view(['GET', 'POST', 'PUT', 'DELETE'])
# @permission_classes([IsAdminUser])
# def management_categories_view(request, id=None):
#     model_name = "Категория"
#     if request.method == 'GET':
#         if id:
#             return Response({"id": id, "name": f"Тестовая {model_name.lower()} {id}", "description": "Описание"})
#         return Response({"count": 2, "next": None, "previous": None, "results": [
#             {"id": "1", "name": f"{model_name} 1"},
#             {"id": "2", "name": f"{model_name} 2"}
#         ]})
#     elif request.method == 'POST':
#         return Response({"id": "new", "name": request.data.get("name", f"Новая {model_name.lower()}"), **request.data}, status=201)
#     elif request.method == 'PUT':
#         return Response({"id": id, "name": request.data.get("name", f"Обновленная {model_name.lower()} {id}"), **request.data})
#     elif request.method == 'DELETE':
#         return Response(status=204)

# Удаляем заглушку для услуг, так как будет использоваться PrintingServiceManagementViewSet
# @api_view(['GET', 'POST', 'PUT', 'DELETE'])
# @permission_classes([IsAdminUser])
# def management_services_view(request, id=None):
#     model_name = "Услуга"
#     if request.method == 'GET':
#         if id:
#             return Response({"id": id, "name": f"Тестовая {model_name.lower()} {id}", "description": "Описание", "base_price": 1000})
#         return Response({"count": 2, "next": None, "previous": None, "results": [
#             {"id": "1", "name": f"{model_name} 1", "base_price": 1000},
#             {"id": "2", "name": f"{model_name} 2", "base_price": 2000}
#         ]})
#     elif request.method == 'POST':
#         return Response({"id": "new", "name": request.data.get("name", f"Новая {model_name.lower()}"), **request.data}, status=201)
#     elif request.method == 'PUT':
#         return Response({"id": id, "name": request.data.get("name", f"Обновленная {model_name.lower()} {id}"), **request.data})
#     elif request.method == 'DELETE':
#         return Response(status=204)

# Удаляем заглушку для заказов, так как будет использоваться OrderManagementViewSet
# @api_view(['GET', 'PUT'])
# @permission_classes([IsAdminUser])
# def management_orders_view(request, id=None):
#     model_name = "Заказ"
#     if request.method == 'GET':
#         if id:
#             return Response({"id": id, "user": {"email": "test@example.com"}, "status": "В обработке", "total": 500})
#         return Response({"count": 1, "next": None, "previous": None, "results": [
#             {"id": "1", "user": {"email": "test@example.com"}, "status": "В обработке", "total": 500}
#         ]})
#     elif request.method == 'PUT':
#         return Response({"id": id, "status": request.data.get("status", "Обновлен"), **request.data})

# Удаляем заглушку для пользователей, так как будем использовать эндпоинты Djoser
# @api_view(['GET'])
# @permission_classes([IsAdminUser]) # Только админ может видеть список пользователей
# def management_users_view(request, id=None):
#     # Заглушка для получения списка пользователей или одного пользователя (если id указан)
#     # В реальном приложении здесь будет логика работы с моделью CustomUser
#     if id:
#         # Djoser обычно использует /auth/users/{id}/ для получения конкретного пользователя,
#         # но для единообразия с другими management_view, сделаем так.
#         # Однако, GET /auth/users/me/ уже есть для текущего пользователя.
#         # А GET /auth/users/{user_id}/ доступен администраторам по умолчанию в Djoser.
#         return Response({
#             "id": id, 
#             "email": f"user{id}@example.com", 
#             "username": f"user{id}", 
#             "is_staff": False, # или is_admin в зависимости от модели
#             "is_superuser": False,
#             "first_name": "Тест",
#             "last_name": f"Пользователь{id}"
#         })
#     
#     # Список пользователей
#     return Response({"count": 2, "next": None, "previous": None, "results": [
#         {"id": "1", "email": "admin@example.com", "username": "admin", "is_staff": True, "first_name": "Главный", "last_name": "Админ"},
#         {"id": "2", "email": "user@example.com", "username": "user", "is_staff": False, "first_name": "Простой", "last_name": "Пользователь"}
#     ]})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('djoser.urls')),
    path('api/auth/', include('djoser.urls.jwt')),
    path('api/auth/', include('djoser.urls.authtoken')),
    path('api/products/', include('products.urls')),
    path('api/orders/', include('orders.urls')),
    path('api/users/', include('users.urls')),
    path('api/cart/', include('cart.urls')),
    path('api/payments/', include('payments.urls')),
    path('api/inquiries/', include('inquiries.urls')),
    path('api/site-settings/', include('site_settings.urls')),
    path('api/reviews/', include('reviews.urls')),
    
    # Маршруты для React Admin Panel (заглушки)
    # Удаляем URL-маршруты для management_products_view
    # path('api/management/products/', management_products_view, name='management-products-list'),
    # path('api/management/products/<str:id>/', management_products_view, name='management-products-detail'),
    # Удаляем URL-маршруты для management_categories_view, так как они теперь в products.urls
    # path('api/management/categories/', management_categories_view, name='management-categories-list'),
    # path('api/management/categories/<str:id>/', management_categories_view, name='management-categories-detail'),
    # Удаляем URL-маршруты для management_services_view, так как они теперь в products.urls
    # path('api/management/services/', management_services_view, name='management-services-list'),
    # path('api/management/services/<str:id>/', management_services_view, name='management-services-detail'),
    # Удаляем URL-маршруты для management_orders_view, так как они теперь в orders.urls
    # path('api/management/orders/', management_orders_view, name='management-orders-list'),
    # path('api/management/orders/<str:id>/', management_orders_view, name='management-orders-detail'),
    # Удаляем URL-маршруты для management_users_view, так как будем использовать Djoser
    # path('api/management/users/', management_users_view, name='management-users-list'),
    # path('api/management/users/<str:id>/', management_users_view, name='management-users-detail'),
    
    # Главная страница
    path('api/', lambda request: JsonResponse({"message": "BAT3D API"})),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) # Если вы обслуживаете статику Django в DEBUG
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
