from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import User, Subscription
from api.serializers import (
    CustomUserSerializer,
    SubscriptionSerializer,
    CustomUserCreateSerializer,
    CustomUserResponseSerializer
)
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from django.contrib.auth import authenticate
import base64
from django.core.files.base import ContentFile


class UserViewSet(viewsets.ModelViewSet):
    """Вьюсет для пользователей."""
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.AllowAny]
    http_method_names = [
        'get', 'post', 'put', 'delete', 'head', 'options', 'patch']

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

        # DELETE
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
            error_message = (
                'Требуются оба поля: current_password и new_password')
            return Response(
                {'detail': error_message},
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
            if avatar_data and avatar_data.startswith('data:image'):
                format, imgstr = avatar_data.split(';base64,')
                ext = format.split('/')[-1]
                request.user.avatar = ContentFile(
                    base64.b64decode(imgstr),
                    name=f'avatar.{ext}'
                )
                request.user.save()
                return Response(
                    {'avatar': request.build_absolute_uri(
                        request.user.avatar.url
                    )},
                    status=status.HTTP_200_OK
                )
            return Response(status=status.HTTP_400_BAD_REQUEST)

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
            {'non_field_errors': [
                'Unable to log in with provided credentials.']},
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
