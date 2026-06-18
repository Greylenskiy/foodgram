from django_filters import rest_framework as filters
from recipes.models import Recipe


class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='istartswith')


class RecipeFilter(filters.FilterSet):
    tags = filters.CharFilter(method='filter_tags')
    author = filters.NumberFilter(field_name='author__id')
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ['tags', 'author', 'is_favorited', 'is_in_shopping_cart']

    def filter_tags(self, queryset, name, value):
        """Фильтр по тегам"""
        if value:
            tags_list = self.request.query_params.getlist('tags')
            if tags_list:
                return queryset.filter(tags__slug__in=tags_list).distinct()
        return queryset

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(favorite__user=user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(shoppingcart__user=user)
        return queryset
