from django.contrib.auth.signals import user_logged_out, user_logged_in
from django.dispatch import receiver
from .models import Cart
import logging

logger = logging.getLogger(__name__)

@receiver(user_logged_in)
def transfer_session_cart_to_user(sender, request, user, **kwargs):
    session_key = request.session.session_key
    if session_key:
        try:
            session_cart = Cart.objects.get(session_key=session_key, user__isnull=True)
            # logger.info(f"[Cart Signal] Found session cart ID {session_cart.id} for session_key {session_key} during login of user {user.id}.") # DEBUG
            
            user_cart, created = Cart.objects.get_or_create(user=user)
            if created:
                logger.info(f"[Cart Signal] Created new cart ID {user_cart.id} for user {user.id} upon login.") # INFO
            # else: # DEBUG
                # logger.info(f"[Cart Signal] Found existing cart ID {user_cart.id} for user {user.id} upon login.")

            if user_cart.id == session_cart.id: 
                # logger.warning(f"[Cart Signal] User cart ID {user_cart.id} is the same as session cart ID {session_cart.id}. No merge needed.") # DEBUG
                return

            if session_cart.items.exists():
                logger.info(f"[Cart Signal] Session cart {session_cart.id} has {session_cart.items.count()} items. Merging with user cart {user_cart.id}.") # INFO - Ключевое событие
                for item in session_cart.items.all():
                    existing_item, item_created = user_cart.items.get_or_create(
                        product=item.product, 
                        printing_service=item.printing_service,
                        # Важно также учитывать другие поля, если они влияют на уникальность (например, параметры конфигурации)
                        defaults={
                            'quantity': item.quantity,
                            'weight': item.weight, 
                            'printing_time': item.printing_time
                        }
                    )
                    if not item_created:
                        existing_item.quantity += item.quantity
                        # Обновляем вес и время, если они есть в сессионном товаре
                        # (можно добавить более сложную логику, например, суммировать или брать максимальное)
                        if item.weight is not None: # Проверяем, что вес есть, прежде чем обновлять
                            existing_item.weight = item.weight 
                        if item.printing_time is not None: # Проверяем, что время есть
                            existing_item.printing_time = item.printing_time
                        existing_item.save()
                        # logger.info(f"[Cart Signal] Updated quantity for item (Product: {item.product_id}, Service: {item.printing_service_id}) in user cart {user_cart.id}. New quantity: {existing_item.quantity}") # DEBUG
                    # else: # DEBUG
                        # logger.info(f"[Cart Signal] Transferred new item (Product: {item.product_id}, Service: {item.printing_service_id}, Qty: {item.quantity}) from session cart {session_cart.id} to user cart {user_cart.id}.")
                
                # logger.info(f"[Cart Signal] Deleting session cart ID {session_cart.id} after merging.") # DEBUG
                session_cart.delete()
            else: # Сессионная корзина пуста
                # logger.info(f"[Cart Signal] Session cart ID {session_cart.id} is empty. Deleting it.") # DEBUG
                session_cart.delete()
        
        except Cart.DoesNotExist:
            # logger.info(f"[Cart Signal] No session cart found for session_key {session_key} during login of user {user.id}.") # DEBUG
            Cart.objects.get_or_create(user=user) # Просто убедимся, что у пользователя есть корзина
            # logger.info(f"[Cart Signal] Ensured cart exists for user {user.id} (or created if new) as no session cart was found.") # DEBUG
        except Exception as e:
            logger.error(f"[Cart Signal] Error in transfer_session_cart_to_user for user {user.id}: {e}", exc_info=True) # ERROR - стоит оставить


@receiver(user_logged_out)
def clear_cart_on_logout(sender, request, user, **kwargs):
    if user: # Убедимся, что user существует
        try:
            user_cart = Cart.objects.filter(user=user).first()
            if user_cart:
                logger.info(f"[Cart Signal] User {user.id} logged out. Cart ID {user_cart.id} with {user_cart.items.count()} items WILL BE CLEARED.") # INFO - Ключевое событие
                user_cart.items.all().delete()
                # Опционально: можно удалить и саму корзину, если не предполагается, что она будет переиспользована
                # user_cart.delete()
                # logger.info(f"[Cart Signal] Cart ID {user_cart.id} for user {user.id} and its items deleted on logout.")
            else:
                # logger.info(f"[Cart Signal] User {user.id} logged out, but no associated cart found to clear.")
                pass
        except Exception as e:
            logger.error(f"[Cart Signal] Error in clear_cart_on_logout for user {user.id}: {e}", exc_info=True) # ERROR - стоит оставить
    else:
        # logger.warning("[Cart Signal] user_logged_out signal received, but user object was None.") 
        pass 