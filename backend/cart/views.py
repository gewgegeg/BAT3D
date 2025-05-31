from django.shortcuts import render
from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer
from products.models import Product, PrintingService
import logging
from django.conf import settings
from rest_framework.views import APIView
# from django.contrib.auth import get_user_model # Убрал, было для диагностики

logger = logging.getLogger(__name__)

# Методы для получения/создания корзины и получения queryset для CartViewSet (можно сделать их helper-функциями или оставить в CartViewSet)
# Для простоты, пока оставим их в CartViewSet, а MinimalCartView будет их использовать.
# Либо, если CartViewSet больше не нужен, эту логику можно перенести в MinimalCartView или в отдельные функции.

class _CartLogicMixin:
    def _get_user_cart_queryset(self, user):
        # logger.info(f"[_CartLogicMixin._get_user_cart_queryset] Called for user: {user.email if user and hasattr(user, 'email') else 'Anonymous'}") # DEBUG
        if user and user.is_authenticated:
            cart_qs = Cart.objects.filter(user=user)
            # logger.info(f"[_CartLogicMixin._get_user_cart_queryset] User is authenticated. Cart query: {cart_qs}. Count: {cart_qs.count()}") # DEBUG
            return cart_qs
        
        cart_id = self.request.session.get('cart_id')
        # logger.info(f"[_CartLogicMixin._get_user_cart_queryset] User is Anonymous. Session cart_id: {cart_id}") # DEBUG
        if cart_id:
            cart_qs = Cart.objects.filter(id=cart_id)
            # logger.info(f"[_CartLogicMixin._get_user_cart_queryset] Anonymous user with cart_id. Cart query: {cart_qs}. Count: {cart_qs.count()}") # DEBUG
            return cart_qs
        return Cart.objects.none()

    def _get_or_create_cart_for_user(self, user, save_session=True):
        # logger.info(f"[_CartLogicMixin._get_or_create_cart_for_user] Called for user: {user.email if user and hasattr(user, 'email') else 'Anonymous'}, save_session: {save_session}") # DEBUG
        cart = None
        created = False
        session_cart_id = self.request.session.get('cart_id')

        if user and user.is_authenticated:
            cart_qs = self._get_user_cart_queryset(user)
            if cart_qs.exists():
                cart = cart_qs.first()
                # logger.info(f"[_CartLogicMixin._get_or_create_cart_for_user] Existing cart found: ID {cart.id}") # DEBUG
            else:
                cart = Cart.objects.create(user=user)
                created = True
                logger.info(f"[_CartLogicMixin._get_or_create_cart_for_user] Created new cart ID {cart.id} for authenticated user {user.id}") # INFO - Ключевое событие
            
            # Связываем сессионную корзину с пользователем, если она есть и еще не связана
            if session_cart_id and Cart.objects.filter(id=session_cart_id, user__isnull=True).exists():
                session_cart_to_link = Cart.objects.get(id=session_cart_id)
                if cart.id != session_cart_to_link.id: # Предотвращаем слияние корзины самой с собой
                    logger.info(f"[_CartLogicMixin._get_or_create_cart_for_user] Linking session cart ID {session_cart_id} items to user cart ID {cart.id}") # INFO - Ключевое событие
                    for item in session_cart_to_link.items.all():
                        existing_item, item_created = cart.items.get_or_create(
                            product=item.product,
                            printing_service=item.printing_service,
                            defaults={
                                'quantity': item.quantity,
                                'weight': item.weight, 
                                'printing_time': item.printing_time
                            }
                        )
                        if not item_created:
                            existing_item.quantity += item.quantity
                            if item.weight is not None: existing_item.weight = item.weight
                            if item.printing_time is not None: existing_item.printing_time = item.printing_time
                            existing_item.save()
                    session_cart_to_link.delete()
                    logger.info(f"[_CartLogicMixin._get_or_create_cart_for_user] Session cart ID {session_cart_id} deleted after merging.") # INFO
                elif cart.id == session_cart_to_link.id and session_cart_to_link.user is None: # Сессионная корзина стала корзиной пользователя
                    session_cart_to_link.user = user
                    session_cart_to_link.session_key = None # Очищаем session_key
                    session_cart_to_link.save()
                    logger.info(f"[_CartLogicMixin._get_or_create_cart_for_user] Session cart ID {session_cart_id} assigned to user {user.id} and session_key cleared.") # INFO

            if save_session and self.request.session.get('cart_id') != cart.id:
                self.request.session['cart_id'] = cart.id
                # logger.info(f"[_CartLogicMixin._get_or_create_cart_for_user] Cart ID {cart.id} saved to session for authenticated user.") # DEBUG
        
        # Анонимный пользователь или пользователь без корзины, но есть cart_id в сессии
        elif session_cart_id:
            try:
                cart = Cart.objects.get(id=session_cart_id, user__isnull=True)
                # logger.info(f"[_CartLogicMixin._get_or_create_cart_for_user] Found anonymous session cart ID {cart.id}") # DEBUG
            except Cart.DoesNotExist:
                # logger.info(f"[_CartLogicMixin._get_or_create_cart_for_user] Anonymous session cart ID {session_cart_id} not found or already assigned. Creating new.") # DEBUG
                pass # Будет создана новая ниже, если cart все еще None

        # Если корзина все еще не определена (например, новый анонимный пользователь или невалидный session_cart_id)
        if cart is None:
            cart = Cart.objects.create() # user остается null для анонимов
            created = True
            logger.info(f"[_CartLogicMixin._get_or_create_cart_for_user] Created new cart ID {cart.id} for anonymous user/session.") # INFO - Ключевое событие
            if save_session:
                self.request.session['cart_id'] = cart.id
                # logger.info(f"[_CartLogicMixin._get_or_create_cart_for_user] Cart ID {cart.id} saved to session for anonymous user.") # DEBUG
        
        # logger.info(f"[_CartLogicMixin._get_or_create_cart_for_user] Returning cart ID: {cart.id}, Created: {created}") # DEBUG
        return cart, created

class MinimalCartView(APIView, _CartLogicMixin):
    permission_classes = [AllowAny] # AllowAny, так как нам нужно обрабатывать и анонимные, и аутентифицированные корзины

    def get(self, request, *args, **kwargs):
        # logger.info(f"[MinimalCartView.get] --------- Request START for GET /api/cart/ ---------") # DEBUG
        # logger.info(f"[MinimalCartView.get] User: {request.user}, Authentication: {'authenticated' if request.user.is_authenticated else 'anonymous'}") # DEBUG
        # logger.info(f"[MinimalCartView.get] Session cart_id BEFORE getting/creating cart: {request.session.get('cart_id')}") # DEBUG
        
        cart, _ = self._get_or_create_cart_for_user(request.user)
        
        # logger.info(f"[MinimalCartView.get] Session cart_id AFTER getting/creating cart: {request.session.get('cart_id')}") # DEBUG
        # logger.info(f"[MinimalCartView.get] Cart object retrieved/created: ID {cart.id}, User on cart: {cart.user}") # DEBUG

        cart_items = cart.items.all().select_related('product__category', 'printing_service')
        # logger.info(f"[MinimalCartView.get] Cart ID {cart.id} has {cart_items.count()} items.") # DEBUG
        
        # for i, item in enumerate(cart_items):
        #     logger.info(f"[MinimalCartView.get] Item {i+1}: ID {item.id}, Product: {item.product.name if item.product else 'N/A'}, Service: {item.printing_service.name if item.printing_service else 'N/A'}, Qty: {item.quantity}") # DEBUG
            
        serializer = CartItemSerializer(cart_items, many=True, context={'request': request})
        # logger.info(f"[MinimalCartView.get] Serialized {cart_items.count()} cart items. Data: {serializer.data}") # DEBUG
        return Response(serializer.data)

class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # logger.debug(f"[CartViewSet.get_queryset] Called for user: {self.request.user}, auth: {self.request.user.is_authenticated}")
        if self.request.user.is_authenticated:
            # logger.info(f"DEBUG_GET_QUERYSET: Authenticated user: {self.request.user} (ID: {self.request.user.id if self.request.user else 'N/A'}, Username: {self.request.user.username if self.request.user else 'N/A'})")
            try:
                user_cart = Cart.objects.get(user=self.request.user)
                # logger.info(f"DEBUG_GET_QUERYSET: Standard search found cart (ID: {user_cart.id}) for request.user {self.request.user.id}")
                
                session_key = self.request.session.session_key
                if session_key:
                    session_cart_for_merge = Cart.objects.filter(session_key=session_key, user__isnull=True).first()
                    if session_cart_for_merge and session_cart_for_merge.items.exists():
                        if not user_cart.items.exists(): 
                            for item in session_cart_for_merge.items.all():
                                item.cart = user_cart
                                item.save()
                            session_cart_for_merge.delete()
                        else: 
                            for s_item in session_cart_for_merge.items.all():
                                u_item, created = user_cart.items.get_or_create(
                                    product=s_item.product,
                                    printing_service=s_item.printing_service,
                                    defaults={'quantity': s_item.quantity, 'weight': s_item.weight, 'printing_time': s_item.printing_time}
                                )
                                if not created:
                                    u_item.quantity += s_item.quantity
                                    u_item.save()
                            session_cart_for_merge.delete()

                qs = Cart.objects.filter(user=self.request.user)
                return qs
            except Cart.DoesNotExist:
                session_key = self.request.session.session_key
                if session_key:
                    session_cart_qs = Cart.objects.filter(session_key=session_key, user__isnull=True)
                    if session_cart_qs.exists():
                        s_cart = session_cart_qs.first()
                        s_cart.user = self.request.user
                        s_cart.session_key = None
                        s_cart.save()
                        return Cart.objects.filter(user=self.request.user)
                return Cart.objects.none()
        else: 
            logger.debug(f"[CartViewSet.get_queryset] Anonymous user. Session key: {self.request.session.session_key}")
            session_key = self.request.session.session_key
            if not session_key:
                self.request.session.save()
                session_key = self.request.session.session_key
            return Cart.objects.filter(session_key=session_key, user__isnull=True)

    def get_or_create_cart(self): # Этот метод все еще используется CartItemViewSet
        logger.debug(f"[CartViewSet.get_or_create_cart] Called for user: {self.request.user}, auth: {self.request.user.is_authenticated}")
        if self.request.user.is_authenticated:
            user_carts_qs = self.get_queryset()
            logger.debug(f"[CartViewSet.get_or_create_cart] Queryset from get_queryset(): {list(user_carts_qs.values_list('id', flat=True)) if user_carts_qs else 'None'}")
            if user_carts_qs.exists():
                cart = user_carts_qs.first()
                logger.debug(f"[CartViewSet.get_or_create_cart] Using existing cart ID: {cart.id} for user {self.request.user.id}")
            else:
                logger.debug(f"[CartViewSet.get_or_create_cart] No existing cart found by get_queryset. Creating new cart for user {self.request.user.id}")
                cart = Cart.objects.create(user=self.request.user)
                logger.debug(f"[CartViewSet.get_or_create_cart] CREATED new cart ID: {cart.id} for user {self.request.user.id}")
        else:
            session_key = self.request.session.session_key
            if not session_key:
                self.request.session.save()
                session_key = self.request.session.session_key
            cart, created = Cart.objects.get_or_create(session_key=session_key, user__isnull=True)
            logger.debug(f"[CartViewSet.get_or_create_cart] Anonymous user. Cart ID: {cart.id}, Created: {created}")
        return cart

    # get_cart_items_list и get(self, ...) в CartViewSet больше не нужны, так как MinimalCartView их заменяет для GET /api/cart/
    # def get_cart_items_list(self, request, *args, **kwargs): ...
    # def get(self, request, *args, **kwargs): ...

    @action(detail=False, methods=['post', 'delete'])
    def clear(self, request):
        # Этот метод может остаться здесь, если /api/cart/clear/ все еще используется через CartViewSet.
        # Но если MinimalCartView полностью заменяет CartViewSet для всех GET/POST на /api/cart/, то clear тоже нужно перенести или сделать отдельный APIView.
        # Пока оставим, но помним, что его вызов теперь зависит от того, как CartViewSet зарегистрирован в urls.py (а он сейчас не зарегистрирован для /api/cart/).
        cart = self.get_or_create_cart()
        cart.items.all().delete()
        serializer = self.serializer_class(cart) # Используем self.serializer_class (CartSerializer)
        return Response(serializer.data)

class CartItemViewSet(viewsets.ModelViewSet, _CartLogicMixin):
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        logger.info(f"[CartItemViewSet.get_queryset] START for user {self.request.user}")
        # cart_view = CartViewSet()
        # cart_view.request = self.request
        # cart_view.format_kwarg = None
        # cart = cart_view.get_or_create_cart()
        cart, _ = self._get_or_create_cart_for_user(self.request.user)
        logger.info(f"[CartItemViewSet.get_queryset] Got cart ID: {cart.id if cart else 'None'}. Returning items for this cart.")
        return CartItem.objects.filter(cart=cart)

    def perform_create(self, serializer):
        logger.info(f"[CartItemViewSet.perform_create] START for user {self.request.user}")
        # cart_view = CartViewSet()
        # cart_view.request = self.request
        # cart_view.format_kwarg = None
        # cart = cart_view.get_or_create_cart()
        cart, cart_created = self._get_or_create_cart_for_user(self.request.user)
        logger.info(f"[CartItemViewSet.perform_create] Got cart ID: {cart.id}. Current items: {list(cart.items.all().values('id', 'product__name', 'quantity'))}")

        product_id_from_request = self.request.data.get('product')
        service_id_from_request = self.request.data.get('printing_service')
        
        # Логируем validated_data особенно quantity
        logger.info(f"[CartItemViewSet.perform_create] Serializer validated_data: {serializer.validated_data}")
        quantity_in_validated_data = serializer.validated_data.get('quantity')
        logger.info(f"[CartItemViewSet.perform_create] Quantity from validated_data: {quantity_in_validated_data}")

        product = serializer.validated_data.get('product') # Может быть None, если ID не найден или это service
        service = serializer.validated_data.get('printing_service') # Может быть None

        # Если product/service в validated_data нет (из-за read_only), 
        # но ID были в request.data, то нам нужны объекты product/service для filter_kwargs
        # Код ниже был для получения product/service объектов, он нужен.
        # Мы их не передаем в serializer.save() если они в validated_data, но используем для existing_item

        product_obj_for_check = None
        service_obj_for_check = None

        if product_id_from_request:
            try:
                product_obj_for_check = Product.objects.get(id=product_id_from_request)
            except Product.DoesNotExist:
                # Это уже должно было быть обработано serializer.is_valid(), но для лога оставим
                logger.error(f"[CartItemViewSet.perform_create] Product with ID {product_id_from_request} not found, though serializer was valid.")
                raise serializers.ValidationError({'product': 'Product not found during perform_create logic.'})
        elif service_id_from_request:
            try:
                service_obj_for_check = PrintingService.objects.get(id=service_id_from_request)
            except PrintingService.DoesNotExist:
                logger.error(f"[CartItemViewSet.perform_create] Service with ID {service_id_from_request} not found, though serializer was valid.")
                raise serializers.ValidationError({'printing_service': 'Service not found during perform_create logic.'})

        filter_kwargs = {'cart': cart}
        if product_obj_for_check:
            filter_kwargs['product'] = product_obj_for_check
            filter_kwargs['printing_service__isnull'] = True
        elif service_obj_for_check:
            filter_kwargs['printing_service'] = service_obj_for_check
            filter_kwargs['product__isnull'] = True
        else:
            # Ни product_id, ни service_id не были предоставлены корректно - serializer должен был это поймать
            logger.error("[CartItemViewSet.perform_create] Neither product nor service ID was valid for filtering.")
            # Это состояние не должно достигаться, если is_valid прошел
            raise serializers.ValidationError("Either product or printing_service must be provided.")

        existing_item = CartItem.objects.filter(**filter_kwargs).first()
        logger.info(f"[CartItemViewSet.perform_create] Filter kwargs for existing_item: {filter_kwargs}")
        logger.info(f"[CartItemViewSet.perform_create] Found existing_item: {existing_item.id if existing_item else 'None'}")

        if existing_item:
            # Если товар уже есть, УВЕЛИЧИВАЕМ его количество
            requested_quantity_to_add = serializer.validated_data.get('quantity', 1)
            existing_item.quantity += requested_quantity_to_add
            existing_item.save(update_fields=['quantity'])
            logger.info(f"[CartItemViewSet.perform_create] Item ID {existing_item.id} already in cart. Quantity INCREASED by {requested_quantity_to_add} to {existing_item.quantity}.")
            serializer.instance = existing_item # Важно для корректного ответа
            # Не вызываем serializer.save() здесь, так как мы напрямую обновили existing_item
            # Возвращаемся, чтобы метод create мог сформировать ответ
            return 
        else:
            # Создание нового элемента (этот блок кода у вас уже должен быть корректным)
            logger.info(f"[CartItemViewSet.perform_create] Creating new item. Quantity to be set: {quantity_in_validated_data}")
            save_kwargs = {'cart': cart}
            if product_obj_for_check:
                save_kwargs['product'] = product_obj_for_check
            if service_obj_for_check:
                save_kwargs['printing_service'] = service_obj_for_check
            
            logger.info(f"[CartItemViewSet.perform_create] Calling serializer.save() with explicit kwargs: { {k: (v.id if hasattr(v, 'id') else v) for k,v in save_kwargs.items()} } PLUS quantity from validated_data") 
            instance = serializer.save(**save_kwargs) # quantity уже в validated_data
            logger.info(f"[CartItemViewSet.perform_create] Created new item ID {instance.id}. Actual qty in DB: {instance.quantity}, Product: {instance.product}, Service: {instance.printing_service}")

    def create(self, request, *args, **kwargs):
        logger.info(f"[CartItemViewSet.create] START for user {request.user}. Request data: {request.data}")
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            logger.error(f"[CartItemViewSet.create] Serializer errors: {serializer.errors}")
            raise serializers.ValidationError(serializer.errors)
        
        # cart = self.get_or_create_cart() # get_or_create_cart будет вызван внутри perform_create
        # logger.info(f"[CartItemViewSet.create] Got cart ID: {cart.id if cart else 'None'}. Items before this operation: {list(cart.items.all().values('id', 'product__name', 'quantity'))}")

        # Логика определения item_already_existed может быть не нужна, если perform_create сам обрабатывает и мы доверяем статусу ответа
        # Но для отладки можно оставить похожую логику или посмотреть на serializer.instance._state.adding после perform_create
        # Однако, это состояние может быть не всегда надежным.
        # Вместо этого, мы можем положиться на то, что perform_create устанавливает serializer.instance
        # и если ID у instance есть ДО вызова perform_create (если бы мы его искали здесь), то это обновление.
        # Но проще всего, если perform_create возвращает флаг или мы проверяем был ли existing_item найден внутри perform_create.
        
        self.perform_create(serializer) # perform_create теперь устанавливает serializer.instance
        
        headers = self.get_success_headers(serializer.data)
        response_data = serializer.data
        
        # Определяем статус ответа: если ID элемента корзины был в ответе и он совпадает с тем, что в serializer.instance,
        # и если МЫ ЗНАЕМ, что это был update или create. 
        # Проверка `existing_item` внутри `perform_create` более надежна для определения, был ли это update.
        # Мы не можем легко получить результат `existing_item` из `perform_create` сюда.
        # Пусть пока будет стандартный ответ, или можно усложнить.
        # Для простоты, пока оставим как есть, но помним, что статус может быть не всегда точно 200 или 201, если логика сложная.
        # DRF обычно возвращает 201 для POST, если не переопределено.

        # Чтобы определить статус 200 или 201, нам нужно знать, был ли элемент новым.
        # `perform_create` не возвращает этот флаг.
        # Мы можем повторно проверить здесь, но это дублирование логики.
        # Можно попробовать проверить serializer.instance до и после.
        # Если до вызова self.perform_create у serializer.instance не было pk, а после появился, то это CREATED.
        # Но это не всегда надежно. 

        # Давайте упростим: если perform_create нашел existing_item, то это HTTP_200_OK, иначе HTTP_201_CREATED.
        # Это потребует от perform_create вернуть флаг.
        # Пока оставим как есть, DRF вернет 201.
        # Если очень нужно различать 200 и 201, perform_create должен вернуть признак. 

        logger.info(f"[CartItemViewSet.create] END. Response data: {response_data}")
        # Стандартный ModelViewSet.create возвращает 201.
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)

    # def create(self, request, *args, **kwargs): # Старая версия с неправильной логикой _state.adding
    #     serializer = self.get_serializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)
    #     self.perform_create(serializer)
    #     headers = self.get_success_headers(serializer.data)
    #     is_new_instance = serializer.instance._state.adding if serializer.instance else True 
    #     current_status = status.HTTP_201_CREATED if is_new_instance else status.HTTP_200_OK
    #     return Response(serializer.data, status=current_status, headers=headers)
