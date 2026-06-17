from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import User, Subscription
from .serializers import (CustomUserSerializer,
                          SubscriptionSerializer, CustomUserCreateSerializer)
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from django.contrib.auth import authenticate
import base64
from django.core.files.base import ContentFile


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.AllowAny]
    http_method_names = ['get', 'post', 'put', 'delete',
                         'head', 'options', 'patch']

    def create(self, request, *args, **kwargs):
        """Регистрация пользователя - POST /api/users/"""
        serializer = CustomUserCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
            },
            status=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Текущий пользователь - требует авторизации"""
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Учетные данные не были предоставлены.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=True, methods=['post', 'delete'])
    def subscribe(self, request, pk=None):
        """Подписка/отписка - требует авторизации"""
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Учетные данные не были предоставлены.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        author = get_object_or_404(User, pk=pk)

        if request.method == 'POST':
            if request.user == author:
                return Response(
                    {'error': 'Нельзя подписаться на себя'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if Subscription.objects.filter(
                    user=request.user, author=author).exists():
                return Response(
                    {'error': 'Вы уже подписаны на этого пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            Subscription.objects.create(user=request.user, author=author)
            serializer = SubscriptionSerializer(
                author, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        # DELETE
        subscription = Subscription.objects.filter(
            user=request.user, author=author)
        if not subscription.exists():
            return Response(
                {'error': 'Подписка не существует.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def subscriptions(self, request):
        """Список подписок - требует авторизации"""
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Учетные данные не были предоставлены.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        authors = User.objects.filter(following__user=request.user)
        page = self.paginate_queryset(authors)
        serializer = SubscriptionSerializer(
            page,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=['post'], url_path='set_password')
    def set_password(self, request):
        """Смена пароля - POST /api/users/set_password/"""
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Учетные данные не были предоставлены.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')

        if not current_password or not new_password:
            return Response(
                {'detail': 'Требуются оба поля:'
                    'current_password и new_password'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Проверяем текущий пароль
        if not request.user.check_password(current_password):
            return Response(
                {'current_password': ['Неверный пароль.']},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Устанавливаем новый пароль
        request.user.set_password(new_password)
        request.user.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['put', 'delete'], url_path='me/avatar')
    def manage_avatar(self, request):
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        if request.method == 'PUT':
            avatar_data = request.data.get('avatar')
            if avatar_data and avatar_data.startswith('data:image'):
                format, imgstr = avatar_data.split(';base64,')
                ext = format.split('/')[-1]
                request.user.avatar = ContentFile(
                    base64.b64decode(imgstr), name=f'avatar.{ext}')
                request.user.save()
                return Response(
                    {'avatar': request.build_absolute_uri(
                        request.user.avatar.url)},
                    status=status.HTTP_200_OK
                )
            return Response(status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'DELETE':
            if request.user.avatar:
                request.user.avatar.delete()
            request.user.avatar = None
            request.user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)


class CustomTokenLoginView(APIView):
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
        else:
            return Response(
                {'non_field_errors': [
                    'Unable to log in with provided credentials.']},
                status=status.HTTP_400_BAD_REQUEST
            )


class CustomTokenLogoutView(APIView):
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
