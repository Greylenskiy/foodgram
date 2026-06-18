from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator


class User(AbstractUser):
    """Кастомная модель пользователя."""
    email = models.EmailField(
        unique=True,
        max_length=254,
        verbose_name='Email'
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
        default='',
        verbose_name='Аватар'
    )
    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[RegexValidator(r'^[\w.@+-]+\Z')],
        verbose_name='Имя пользователя'
    )
    first_name = models.CharField(
        max_length=150,
        verbose_name='Имя'
    )
    last_name = models.CharField(
        max_length=150,
        verbose_name='Фамилия'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['id']

    def __str__(self):
        return self.email


class Subscription(models.Model):
    """Модель подписки."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscription'
            ),
            models.CheckConstraint(
                condition=~models.Q(user=models.F('author')),
                name='cannot_subscribe_to_self'
            )
        ]

    def __str__(self):
        return f"{self.user} -> {self.author}"
