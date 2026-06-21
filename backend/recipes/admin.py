from django.contrib import admin
from django.utils.html import format_html
from django.contrib.auth import get_user_model

from .models import (
    Recipe, Tag, Ingredient, Favorite,
    ShoppingCart, RecipeIngredient
)

User = get_user_model()


class RecipeIngredientInline(admin.TabularInline):
    """Встроенная форма для ингредиентов в рецепте."""
    model = RecipeIngredient
    extra = 1
    min_num = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Админка для рецептов."""
    list_display = (
        'name',
        'author',
        'cooking_time_display',
        'get_tags',
        'favorites_count',
        'image_preview'
    )
    list_filter = ('author', 'tags')
    search_fields = ('name', 'author__username', 'author__email')
    filter_horizontal = ('tags',)
    inlines = [RecipeIngredientInline]

    @admin.display(description='Теги')
    def get_tags(self, obj):
        return ', '.join(tag.name for tag in obj.tags.all())

    @admin.display(description='Время приготовления')
    def cooking_time_display(self, obj):
        return f'{obj.cooking_time} мин'

    @admin.display(description='В избранном')
    def favorites_count(self, obj):
        return Favorite.objects.filter(recipe=obj).count()

    @admin.display(description='Изображение')
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="50" height="50" />',
                obj.image.url
            )
        return 'Нет изображения'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Админка для тегов."""
    list_display = ('name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Админка для ингредиентов."""
    list_display = ('name', 'measurement_unit', 'recipes_count')
    list_filter = ('measurement_unit',)
    search_fields = ('name', 'measurement_unit')

    @admin.display(description='В рецептах')
    def recipes_count(self, obj):
        return obj.recipes.count()


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Админка для избранного."""
    list_display = ('user', 'recipe')
    list_filter = ('user',)
    search_fields = ('user__username', 'recipe__name')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Админка для списка покупок."""
    list_display = ('user', 'recipe')
    list_filter = ('user',)
    search_fields = ('user__username', 'recipe__name')
