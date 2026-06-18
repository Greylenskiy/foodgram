from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from rest_framework.authtoken.models import TokenProxy

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Админка для пользователей."""
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'recipes_count',
        'followers_count'
    )
    search_fields = ('email', 'username')
    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительно', {'fields': ('avatar',)}),
    )

    def recipes_count(self, obj):
        return obj.recipes.count()
    recipes_count.short_description = 'Рецептов'

    def followers_count(self, obj):
        return obj.following.count()
    followers_count.short_description = 'Подписчиков'


# Скрываем ненужные модели в админке
admin.site.unregister(Group)
try:
    admin.site.unregister(TokenProxy)
except admin.sites.NotRegistered:
    pass
