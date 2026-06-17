from django.contrib import admin
from .models import (Recipe, Tag, Ingredient, Favorite,
                     ShoppingCart, RecipeIngredient)


class RecipeIngredientInline(admin.TabularInline):
    """Позволяет добавлять ингредиенты прямо на странице рецепта"""
    model = RecipeIngredient
    extra = 1
    min_num = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'favorites_count')
    list_filter = ('tags',)
    search_fields = ('name', 'author__username', 'author__email')
    inlines = [RecipeIngredientInline]

    @admin.display(description='В избранном')
    def favorites_count(self, obj):
        return obj.favorited_by.count()


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    list_filter = ('user',)
    search_fields = ('user__username', 'recipe__name')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    list_filter = ('user',)
    search_fields = ('user__username', 'recipe__name')
