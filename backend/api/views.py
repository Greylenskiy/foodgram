from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from recipes.models import Recipe, Tag, Ingredient, Favorite, ShoppingCart
from .serializers import RecipeSerializer, TagSerializer, IngredientSerializer
from .permissions import IsAuthorOrReadOnly


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    #
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None

    def get_queryset(self):
        name = self.request.query_params.get('name')
        if name:
            return self.queryset.filter(name__istartswith=name)
        return self.queryset


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthorOrReadOnly]

    def get_queryset(self):
        queryset = Recipe.objects.all()
        tags = self.request.query_params.getlist('tags')
        author = self.request.query_params.get('author')
        is_favorited = self.request.query_params.get('is_favorited')
        is_in_shopping_cart = self.request.query_params.get(
            'is_in_shopping_cart')

        if tags:
            queryset = queryset.filter(tags__slug__in=tags).distinct()
        if author:
            queryset = queryset.filter(author_id=author)
        if is_favorited == '1' and self.request.user.is_authenticated:
            queryset = queryset.filter(favorited_by__user=self.request.user)
        if is_in_shopping_cart == '1' and self.request.user.is_authenticated:
            queryset = queryset.filter(
                in_shopping_cart__user=self.request.user)

        return queryset

    @action(detail=True, methods=['post', 'delete'])
    def favorite(self, request, pk=None):
        """добавить/удалить рецепт из избранного"""

        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Учетные данные не были предоставлены.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        recipe = get_object_or_404(Recipe, pk=pk)

        if request.method == 'POST':
            if Favorite.objects.filter(
                    user=request.user, recipe=recipe).exists():
                return Response(
                    {'error': 'Рецепт уже в избранном'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Favorite.objects.create(user=request.user, recipe=recipe)

            from recipes.serializers import ShortRecipeSerializer
            serializer = ShortRecipeSerializer(
                recipe, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        # DELETE: проверяем, существует ли рецепт в избранном
        favorite_item = Favorite.objects.filter(
            user=request.user, recipe=recipe)
        if not favorite_item.exists():
            return Response(
                {'error': 'Рецепта нет в избранном.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        favorite_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'])
    def shopping_cart(self, request, pk=None):
        """добавить/удалить рецепт из списка покупок"""

        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Учетные данные не были предоставлены.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        recipe = get_object_or_404(Recipe, pk=pk)

        if request.method == 'POST':
            if ShoppingCart.objects.filter(
                    user=request.user, recipe=recipe).exists():
                return Response(
                    {'error': 'Рецепт уже в списке покупок'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            ShoppingCart.objects.create(user=request.user, recipe=recipe)

            from recipes.serializers import ShortRecipeSerializer
            serializer = ShortRecipeSerializer(
                recipe, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        # DELETE: проверяем, существует ли рецепт в корзине
        cart_item = ShoppingCart.objects.filter(
            user=request.user, recipe=recipe)
        if not cart_item.exists():
            return Response(
                {'error': 'Рецепта нет в списке покупок.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        cart_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def download_shopping_cart(self, request):
        """скачать список покупок в txt формате"""
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Учетные данные не были предоставлены.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Получаем рецепты из корзины пользователя
        cart_items = ShoppingCart.objects.filter(
            user=request.user).select_related('recipe')
        recipes = [item.recipe for item in cart_items]

        ingredients_dict = {}

        for recipe in recipes:
            # Используем правильный related_name
            for ing in recipe.ingredients_amount.all():
                name = ing.ingredient.name
                unit = ing.ingredient.measurement_unit
                key = f"{name} ({unit})"
                ingredients_dict[key] = ingredients_dict.get(
                    key, 0) + ing.amount

        # Формируем файл
        content = "Список покупок:\n\n"
        for item, amount in ingredients_dict.items():
            content += f"{item} — {amount}\n"

        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = 'attachment;' \
            'filename="shopping_list.txt"'
        return response

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_short_link(self, request, pk=None):
        """Получить короткую ссылку на рецепт"""
        recipe = self.get_object()
        short_link = request.build_absolute_uri(f'/s/{recipe.id}/')

        return Response(
            {'short-link': short_link},
            status=status.HTTP_200_OK
        )
