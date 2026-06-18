from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from recipes.models import (
    Recipe,
    Tag,
    Ingredient,
    Favorite,
    ShoppingCart,
    RecipeIngredient,
)
from .serializers import (
    RecipeReadSerializer,
    RecipeWriteSerializer,
    TagSerializer,
    IngredientSerializer,
    ShortRecipeSerializer,
)
from .permissions import IsAuthorOrReadOnly
from .filters import RecipeFilter, IngredientFilter


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для тегов."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для ингредиентов."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для рецептов."""
    queryset = Recipe.objects.select_related('author').prefetch_related(
        'tags', 'ingredients_amount__ingredient'
    )
    permission_classes = [IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от метода."""
        if self.request.method in ['POST', 'PUT', 'PATCH']:
            return RecipeWriteSerializer
        return RecipeReadSerializer

    def perform_create(self, serializer):
        """Сохраняет рецепт с автором — текущим пользователем."""
        serializer.save(author=self.request.user)

    def _add_to_user_recipe(self, request, pk, model,
                            error_exists, error_not_found):
        """метод для добавления рецепта в избранное/корзину."""
        recipe = get_object_or_404(Recipe, pk=pk)

        if request.method == 'POST':
            if model.objects.filter(user=request.user, recipe=recipe).exists():
                return Response(
                    {'error': error_exists},
                    status=status.HTTP_400_BAD_REQUEST
                )
            model.objects.create(user=request.user, recipe=recipe)
            serializer = ShortRecipeSerializer(
                recipe, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        # DELETE
        deleted, _ = model.objects.filter(
            user=request.user, recipe=recipe
        ).delete()
        if not deleted:
            return Response(
                {'error': error_not_found},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        """Добавить рецепт в избранное."""
        return self._add_to_user_recipe(
            request, pk,
            Favorite,
            'Рецепт уже в избранном',
            'Рецепта нет в избранном.'
        )

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        """Удалить рецепт из избранного."""
        return self._add_to_user_recipe(
            request, pk,
            Favorite,
            'Рецепт уже в избранном',
            'Рецепта нет в избранном.'
        )

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        """Добавить рецепт в список покупок."""
        return self._add_to_user_recipe(
            request, pk,
            ShoppingCart,
            'Рецепт уже в списке покупок',
            'Рецепта нет в списке покупок.'
        )

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        """Удалить рецепт из списка покупок."""
        return self._add_to_user_recipe(
            request, pk,
            ShoppingCart,
            'Рецепт уже в списке покупок',
            'Рецепта нет в списке покупок.'
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        """Скачать список покупок в txt формате."""
        user = request.user

        ingredients = RecipeIngredient.objects.filter(
            recipe__shoppingcart__user=user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(
            total_amount=Sum('amount')
        ).order_by('ingredient__name')

        content = self._format_shopping_list(ingredients)

        response = HttpResponse(content, content_type='text/plain')
        response[
            'Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
        return response

    def _format_shopping_list(self, ingredients):
        """Формирование текста списка покупок."""
        content = "Список покупок:\n\n"
        for item in ingredients:
            content += (
                f"{item['ingredient__name']} "
                f"({item['ingredient__measurement_unit']}) — "
                f"{item['total_amount']}\n"
            )
        return content

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_short_link(self, request, pk=None):
        """Получить короткую ссылку на рецепт."""
        recipe = self.get_object()
        short_link = request.build_absolute_uri(f'/s/{recipe.id}/')
        return Response(
            {'short-link': short_link},
            status=status.HTTP_200_OK
        )
