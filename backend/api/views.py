from django.contrib.auth import authenticate
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from recipes.models import (
    Recipe,
    Tag,
    Ingredient,
    Favorite,
    ShoppingCart,
    RecipeIngredient,
)
from users.models import User, Subscription
from .serializers import (
    RecipeReadSerializer,
    RecipeWriteSerializer,
    TagSerializer,
    IngredientSerializer,
    ShortRecipeSerializer,
    CustomUserSerializer,
    SubscriptionSerializer,
    CustomUserCreateSerializer,
)
from .permissions import IsAuthorOrReadOnly
from .filters import RecipeFilter, IngredientFilter
from .fields import Base64ImageField


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

    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated()]
        return super().get_permissions()

    def perform_create(self, serializer):
        """Сохраняет рецепт с автором — текущим пользователем."""
        serializer.save(author=self.request.user)

    def _add_to_user_recipe(self, request, pk, model, error_message):
        """Метод для добавления рецепта в избранное/корзину."""
        recipe = get_object_or_404(Recipe, pk=pk)
        if model.objects.filter(user=request.user, recipe=recipe).exists():
            return Response(
                {'error': error_message},
                status=status.HTTP_400_BAD_REQUEST
            )
        model.objects.create(user=request.user, recipe=recipe)
        serializer = ShortRecipeSerializer(
            recipe, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _remove_from_user_recipe(self, request, pk, model, error_message):
        """Метод для удаления рецепта из избранного/корзины."""
        recipe = get_object_or_404(Recipe, pk=pk)
        deleted, _ = model.objects.filter(
            user=request.user, recipe=recipe
        ).delete()
        if not deleted:
            return Response(
                {'error': error_message},
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
            'Рецепт уже в избранном'
        )

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        """Удалить рецепт из избранного."""
        return self._remove_from_user_recipe(
            request, pk,
            Favorite,
            'Рецепта нет в избранном'
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
            'Рецепт уже в списке покупок'
        )

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        """Удалить рецепт из списка покупок."""
        return self._remove_from_user_recipe(
            request, pk,
            ShoppingCart,
            'Рецепта нет в списке покупок'
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


class UserViewSet(viewsets.ModelViewSet):
    """Вьюсет для пользователей."""
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.AllowAny]
    http_method_names = [
        'get', 'post', 'put', 'delete', 'head', 'options', 'patch'
    ]

    def get_serializer_class(self):
        if self.action == 'create':
            return CustomUserCreateSerializer
        return CustomUserSerializer

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def me(self, request):
        """Текущий пользователь."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def subscribe(self, request, pk=None):
        """Подписка/отписка."""
        author = get_object_or_404(User, pk=pk)

        if request.method == 'POST':
            if request.user == author:
                return Response(
                    {'error': 'Нельзя подписаться на себя'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if Subscription.objects.filter(
                user=request.user, author=author
            ).exists():
                return Response(
                    {'error': 'Вы уже подписаны на этого пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            Subscription.objects.create(user=request.user, author=author)
            serializer = SubscriptionSerializer(
                author, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        deleted, _ = Subscription.objects.filter(
            user=request.user, author=author
        ).delete()
        if not deleted:
            return Response(
                {'error': 'Подписка не существует.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def subscriptions(self, request):
        """Список подписок."""
        authors = User.objects.filter(following__user=request.user)
        page = self.paginate_queryset(authors)
        serializer = SubscriptionSerializer(
            page,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False,
        methods=['post'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def set_password(self, request):
        """Смена пароля."""
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')

        if not current_password or not new_password:
            return Response(
                {'detail':
                 'Требуются оба поля: current_password и new_password'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not request.user.check_password(current_password):
            return Response(
                {'current_password': ['Неверный пароль.']},
                status=status.HTTP_400_BAD_REQUEST
            )

        request.user.set_password(new_password)
        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['put', 'delete'],
        permission_classes=[permissions.IsAuthenticated],
        url_path='me/avatar'
    )
    def manage_avatar(self, request):
        """Управление аватаром."""
        if request.method == 'PUT':
            avatar_data = request.data.get('avatar')
            image_field = Base64ImageField()
            try:
                request.user.avatar = image_field.to_internal_value(
                    avatar_data)
                request.user.save()
                return Response(
                    {'avatar': request.build_absolute_uri(
                        request.user.avatar.url
                    )},
                    status=status.HTTP_200_OK
                )
            except Exception:
                return Response(
                    {'avatar': 'Некорректное изображение.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # DELETE
        if request.user.avatar:
            request.user.avatar.delete()
        request.user.avatar = None
        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CustomTokenLoginView(APIView):
    """Кастомный вход по токену."""
    permission_classes = []
    authentication_classes = []

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        user = authenticate(request, username=email, password=password)

        if user is not None:
            token, created = Token.objects.get_or_create(user=user)
            return Response(
                {'auth_token': token.key},
                status=status.HTTP_200_OK
            )
        return Response(
            {'non_field_errors':
             ['Unable to log in with provided credentials.']},
            status=status.HTTP_400_BAD_REQUEST
        )


class CustomTokenLogoutView(APIView):
    """Кастомный выход по токену."""
    permission_classes = []
    authentication_classes = []

    def post(self, request):
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Token '):
            token_key = auth_header.split(' ')[1]
            try:
                token = Token.objects.get(key=token_key)
                token.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except Token.DoesNotExist:
                pass

        return Response(
            {'detail': 'Invalid token.'},
            status=status.HTTP_401_UNAUTHORIZED
        )


def short_link_redirect(request, recipe_id):
    """Редирект по короткой ссылке на страницу рецепта."""
    recipe = get_object_or_404(Recipe, id=recipe_id)
    return redirect(f'/recipes/{recipe.id}/')
