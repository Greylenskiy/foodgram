from rest_framework import serializers
from djoser.serializers import UserCreateSerializer, UserSerializer
from .models import User, Subscription


class CustomUserCreateSerializer(UserCreateSerializer):

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name',
                  'last_name', 'password')


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'avatar', 'is_subscribed')

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if not user.is_authenticated:
            return False
        return Subscription.objects.filter(user=user, author=obj).exists()


class SubscriptionSerializer(serializers.ModelSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name',
                  'last_name', 'avatar',
                  'recipes', 'recipes_count')

    def get_recipes(self, obj):
        from recipes.serializers import ShortRecipeSerializer
        recipes = obj.recipes.all()[:3]
        return ShortRecipeSerializer(
            recipes, many=True, context=self.context).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()
