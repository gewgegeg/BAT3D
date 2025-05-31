from django.contrib.auth.models import AbstractUser, BaseUserManager # <--- Добавить BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _

class CustomUserManager(BaseUserManager): # <--- Новый менеджер
    """
    Custom user model manager where email is the unique identifiers
    for authentication instead of usernames.
    """
    def create_user(self, email, password, **extra_fields): # <--- Изменить сигнатуру
        """
        Create and save a User with the given email and password.
        """
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        # Если username не передается в extra_fields, но нужен для AbstractUser,
        # можно его установить равным email или генерировать.
        # Но Djoser должен передать 'username' из validated_data, если он там есть.
        # Проверим, есть ли 'username' в extra_fields, если нет, то используем email
        if 'username' not in extra_fields:
             extra_fields.setdefault('username', email) # <--- Устанавливаем username, если его нет

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        # Аналогично, убедимся что username установлен
        if 'username' not in extra_fields:
            extra_fields.setdefault('username', email)


        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    email = models.EmailField(_('email address'), unique=True)
    phone = models.CharField(_('phone number'), max_length=15, blank=True)
    address = models.TextField(_('address'), blank=True)
    first_name = models.CharField(_('first name'), max_length=150, blank=False) 
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name'] 
    
    objects = CustomUserManager() # <--- Назначить кастомный менеджер

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['email']
        
    def __str__(self):
        return self.email
