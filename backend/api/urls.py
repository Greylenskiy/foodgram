from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import TagViewSet, IngredientViewSet, RecipeViewSet
from users.views import UserViewSet

router = DefaultRouter()
router.register('users', UserViewSet)
router.register('tags', TagViewSet)
router.register('ingredients', IngredientViewSet)
router.register('recipes', RecipeViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
