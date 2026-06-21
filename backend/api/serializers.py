from rest_framework import serializers

from recipes.constants import MIN_AMOUNT, MAX_AMOUNT
from recipes.models import (
    Recipe,
    Tag,
    Ingredient,
    RecipeIngredient,
    Favorite,
    ShoppingCart,
)
from users.models import User, Subscription
from .fields import Base64ImageField


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения ингредиентов в рецепте."""
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeIngredientWriteSerializer(serializers.Serializer):
    """Сериализатор для записи ингредиентов в рецепт."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
    )
    amount = serializers.IntegerField(
        min_value=MIN_AMOUNT,
        max_value=MAX_AMOUNT,
        error_messages={
            'min_value':
            f'Количество ингредиента должно быть не менее {MIN_AMOUNT}.',
            'max_value':
            f'Количество ингредиента не может превышать {MAX_AMOUNT}.',
            'invalid': 'Количество должно быть целым числом.',
        }
    )


class RecipeIngredientListSerializer(serializers.ListSerializer):
    """
    Сериализатор для списка ингредиентов.
    Проверяет дубликаты на уровне всего списка.
    """
    child = RecipeIngredientWriteSerializer()

    def validate(self, data):
        """Проверка на дубликаты ингредиентов."""
        if not data:
            raise serializers.ValidationError(
                'Ингредиенты обязательны.'
            )

        ingredient_ids = [item['id'] for item in data]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться.'
            )

        return data


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Короткий сериализатор для рецептов (для подписок)."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class CustomUserSerializer(serializers.ModelSerializer):
    """Сериализатор для пользователей."""
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name',
            'avatar', 'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if not user.is_authenticated:
            return False
        return Subscription.objects.filter(user=user, author=obj).exists()

    def get_avatar(self, obj):
        if obj.avatar and hasattr(obj.avatar, 'url'):
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return str(obj.avatar.url)
        return None


class CustomUserResponseSerializer(serializers.ModelSerializer):
    """Сериализатор для ответа при регистрации."""

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name')


class CustomUserCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name', 'password')
        extra_kwargs = {
            'password': {'write_only': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def create(self, validated_data):
        """Создание пользователя с правильным хешированием пароля."""
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=validated_data['password']
        )
        return user

    def to_representation(self, instance):
        return CustomUserResponseSerializer(
            instance, context=self.context).data


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения рецептов (GET)."""
    author = CustomUserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientReadSerializer(
        source='ingredients_amount',
        many=True,
        read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time'
        )

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if not user.is_authenticated:
            return False
        return Favorite.objects.filter(user=user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if not user.is_authenticated:
            return False
        return ShoppingCart.objects.filter(user=user, recipe=obj).exists()


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для записи рецептов (POST, PATCH)."""
    ingredients = RecipeIngredientListSerializer()
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'name', 'image', 'text', 'cooking_time', 'ingredients', 'tags'
        )

    def validate(self, data):
        """Общая валидация для POST и PATCH."""
        request = self.context.get('request')

        if request.method == 'PATCH':
            if 'ingredients' not in request.data:
                raise serializers.ValidationError(
                    {'ingredients': 'Это поле обязательно.'}
                )
            if 'tags' not in request.data:
                raise serializers.ValidationError(
                    {'tags': 'Это поле обязательно.'}
                )

        return data

    def validate_tags(self, value):
        """Проверка на дубликаты тегов."""
        if not value:
            raise serializers.ValidationError('Теги обязательны.')
        if len(value) != len(set(value)):
            raise serializers.ValidationError('Теги не должны повторяться.')
        return value

    def validate_cooking_time(self, value):
        """Проверка времени приготовления."""
        if value < 1:
            raise serializers.ValidationError(
                'Время приготовления должно быть не менее 1 минуты.'
            )
        return value

    def _create_ingredients(self, recipe, ingredients_data):
        """Вспомогательный метод для создания ингредиентов."""
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient=ing['id'],
                amount=ing['amount']
            )
            for ing in ingredients_data
        ])

    def create(self, validated_data):
        """Создание рецепта с ингредиентами и тегами."""
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')

        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)
        self._create_ingredients(recipe, ingredients_data)

        return recipe

    def update(self, instance, validated_data):
        """Обновление рецепта с ингредиентами и тегами."""
        tags_data = validated_data.pop('tags', None)
        ingredients_data = validated_data.pop('ingredients', None)

        instance = super().update(instance, validated_data)

        # Обновляем теги
        if tags_data is not None:
            instance.tags.set(tags_data)

        # Обновляем ингредиенты
        if ingredients_data is not None:
            instance.ingredients_amount.all().delete()
            self._create_ingredients(instance, ingredients_data)

        return instance

    def to_representation(self, instance):
        """Возвращаем данные в формате читающего сериализатора."""
        return RecipeReadSerializer(
            instance,
            context=self.context
        ).data


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для подписок."""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name',
            'avatar', 'recipes', 'recipes_count', 'is_subscribed'
        )

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit', 3)

        try:
            recipes_limit = int(recipes_limit)
        except ValueError:
            recipes_limit = 3

        recipes = obj.recipes.all()[:recipes_limit]
        return ShortRecipeSerializer(
            recipes, many=True, context=self.context
        ).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_is_subscribed(self, obj):
        return True
