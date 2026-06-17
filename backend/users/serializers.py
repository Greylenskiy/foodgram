from rest_framework import serializers
from djoser.serializers import UserCreateSerializer, UserSerializer
from .models import User, Subscription


class CustomUserCreateSerializer(UserCreateSerializer):
    first_name = serializers.CharField(required=True, max_length=150)
    last_name = serializers.CharField(required=True, max_length=150)

    class Meta:
        model = User
        fields = ('id', 'email', 'username',
                  'first_name', 'last_name', 'password')
        extra_kwargs = {
            'password': {'write_only': True}
        }


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'avatar', 'is_subscribed')

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
        return ""


class SubscriptionSerializer(serializers.ModelSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name',
                  'last_name', 'avatar',
                  'recipes', 'recipes_count', 'is_subscribed')

    def get_recipes(self, obj):
        from recipes.serializers import ShortRecipeSerializer

        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit', 3)

        try:
            recipes_limit = int(recipes_limit)
        except ValueError:
            recipes_limit = 3

        recipes = obj.recipes.all()[:recipes_limit]
        return ShortRecipeSerializer(
            recipes, many=True, context=self.context).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_is_subscribed(self, obj):
        """Всегда True для подписок"""
        return True
