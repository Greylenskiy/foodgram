from rest_framework import serializers
from rest_framework.fields import SerializerMethodField
from recipes.models import (
    Recipe,
    Tag,
    Ingredient,
    RecipeIngredient,
    Favorite,
    ShoppingCart,
)
import base64
from django.core.files.base import ContentFile
from rest_framework.exceptions import AuthenticationFailed


class Base64ImageField(serializers.ImageField):

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    author = SerializerMethodField()
    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientSerializer(source='ingredients_amount',
                                             many=True, read_only=True)
    is_favorited = SerializerMethodField()
    is_in_shopping_cart = SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name',
                  'image', 'text', 'cooking_time')

    def get_author(self, obj):
        from users.serializers import CustomUserSerializer
        return CustomUserSerializer(obj.author, context=self.context).data

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        return user.is_authenticated and Favorite.objects.filter(
            user=user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        return user.is_authenticated and ShoppingCart.objects.filter(
            user=user, recipe=obj).exists()

    def create(self, validated_data):
        request = self.context.get('request')

        # Проверка авторизации
        if not request.user or not request.user.is_authenticated:
            raise AuthenticationFailed('Учетные данные не были предоставлены.')

        # Проверка cooking_time
        cooking_time = validated_data.get('cooking_time')
        if cooking_time is None or cooking_time < 1:
            raise serializers.ValidationError(
                {'cooking_time': 'Время приготовления должно быть'
                    'не менее 1 минуты.'}
            )

        ingredients_data = request.data.get('ingredients')
        tags_data = request.data.get('tags')

        # Проверка наличия
        if not ingredients_data:
            raise serializers.ValidationError(
                {'ingredients': 'Это поле обязательно.'}
            )
        if not tags_data:
            raise serializers.ValidationError(
                {'tags': 'Это поле обязательно.'}
            )

        # Проверка количества ингредиентов
        for ing in ingredients_data:
            if ing.get('amount', 0) < 1:
                raise serializers.ValidationError(
                    {'ingredients': 'Количество ингредиента должно'
                        'быть не менее 1.'}
                )

        # Проверка на дубликаты ингредиентов
        ing_ids = [ing['id'] for ing in ingredients_data]
        if len(ing_ids) != len(set(ing_ids)):
            raise serializers.ValidationError(
                {'ingredients': 'Ингредиенты не должны повторяться.'}
            )

        # Проверка на дубликаты тегов
        if len(tags_data) != len(set(tags_data)):
            raise serializers.ValidationError(
                {'tags': 'Теги не должны повторяться.'}
            )

        # Проверка существования ингредиентов
        for ing in ingredients_data:
            if not Ingredient.objects.filter(id=ing['id']).exists():
                raise serializers.ValidationError(
                    {'ingredients':
                     f'Ингредиент с id={ing["id"]} не существует.'}
                )

        # Проверка существования тегов
        for tag_id in tags_data:
            if not Tag.objects.filter(id=tag_id).exists():
                raise serializers.ValidationError(
                    {'tags': f'Тег с id={tag_id} не существует.'}
                )

        # Создаём рецепт
        validated_data['author'] = request.user
        recipe = Recipe.objects.create(
            author=validated_data['author'],
            name=validated_data['name'],
            text=validated_data['text'],
            cooking_time=validated_data['cooking_time'],
            image=validated_data.get('image')
        )

        # Добавляем теги
        recipe.tags.set(set(tags_data))

        # Добавляем ингредиенты
        for ing in ingredients_data:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient_id=ing['id'],
                amount=ing['amount']
            )

        return recipe

    def validate(self, data):
        request = self.context.get('request')

        if not request.user or not request.user.is_authenticated:
            raise AuthenticationFailed('Учетные данные не были предоставлены.')

        if request.method == 'PATCH':
            # Проверка для ingredients
            if 'ingredients' in request.data:
                ingredients = request.data.get('ingredients')

                if not ingredients or len(ingredients) == 0:
                    raise serializers.ValidationError(
                        {'ingredients': 'Это поле не может быть пустым.'})

                for ing in ingredients:
                    if not Ingredient.objects.filter(id=ing['id']).exists():
                        raise serializers.ValidationError(
                            {'ingredients':
                             f'Ингредиент с id={ing["id"]} не существует.'}
                        )
                    if ing.get('amount', 0) < 1:
                        raise serializers.ValidationError(
                            {'ingredients': 'Количество ингредиента должно'
                                'быть не менее 1.'}
                        )

                ing_ids = [ing['id'] for ing in ingredients]
                if len(ing_ids) != len(set(ing_ids)):
                    raise serializers.ValidationError(
                        {'ingredients': 'Ингредиенты не должны повторяться.'}
                    )

            # Проверка для tags
            if 'tags' in request.data:
                tags = request.data.get('tags')

                if not tags or len(tags) == 0:
                    raise serializers.ValidationError(
                        {'tags': 'Это поле не может быть пустым.'})

                # Проверка на дубликаты
                if len(tags) != len(set(tags)):
                    raise serializers.ValidationError(
                        {'tags': 'Теги не должны повторяться.'}
                    )

                # Проверка существования тегов
                for tag_id in tags:
                    if not Tag.objects.filter(id=tag_id).exists():
                        raise serializers.ValidationError(
                            {'tags': f'Тег с id={tag_id} не существует.'}
                        )
            else:
                # Если поле tags отсутствует в запросе - ошибка
                raise serializers.ValidationError(
                    {'tags': 'Это поле обязательно.'}
                )

        return data

    def update(self, instance, validated_data):
        request = self.context.get('request')

        # Проверка обязательных полей
        if request.method == 'PATCH':
            if 'ingredients' not in request.data:
                raise serializers.ValidationError(
                    {'ingredients': 'Это поле обязательно.'})
            if 'tags' not in request.data:
                raise serializers.ValidationError(
                    {'tags': 'Это поле обязательно.'})

            # Проверка cooking_time
            if 'cooking_time' in request.data:
                cooking_time = request.data.get('cooking_time')
                if cooking_time is not None and cooking_time < 1:
                    raise serializers.ValidationError(
                        {'cooking_time': 'Время приготовления должно быть'
                            'не менее 1 минуты.'}
                    )

        return super().update(instance, validated_data)
