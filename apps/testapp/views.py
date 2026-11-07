from uuid import uuid4

from django.core.cache import cache

from django.contrib.auth import get_user_model
from django.utils.text import slugify
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import GoogleAuthSerializer, LogoutSerializer, PostSerializer, RegisterSerializer
from .models import Post
from .services import get_google_access_token, get_google_user_info
from .tasks import send_welcome_email_task


class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            token = RefreshToken(serializer.validated_data["refresh"])
            token.blacklist()
        except TokenError:
            return Response(
                {"detail": "Токен недействителен или уже находится в черном списке."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"detail": "Вы успешно вышли из системы."},
            status=status.HTTP_205_RESET_CONTENT,
        )


class ProfileStatsView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        return Response({
            "email": user.email,
            "role": user.role,
            "is_staff": user.is_staff,
            "date_joined": user.date_joined,
        })


class GoogleAuthView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = GoogleAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        google_access_token = get_google_access_token(serializer.validated_data["code"])
        google_user = get_google_user_info(google_access_token)
        User = get_user_model()
        email = User.objects.normalize_email(google_user["email"])

        user = User.objects.filter(email__iexact=email).first()
        is_new_user = user is None

        if is_new_user:
            base_username = slugify(email.split("@", 1)[0])[:120] or "google_user"
            username = base_username
            while User.objects.filter(username=username).exists():
                username = f"{base_username[:130]}_{uuid4().hex[:8]}"

            user = User(
                email=email,
                username=username,
                first_name=google_user["name"][:150],
            )
            user.set_unusable_password()
            user.save()

        if not user.is_active:
            raise AuthenticationFailed("Аккаунт пользователя отключен.")

        refresh = RefreshToken.for_user(user)
        refresh["email"] = user.email
        refresh["role"] = user.role
        access = refresh.access_token

        return Response({
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "name": google_user["name"],
                "role": user.role,
            },
            "is_new_user": is_new_user,
            "tokens": {
                "refresh": str(refresh),
                "access": str(access),
            },
        }, status=status.HTTP_200_OK)



class PostsView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        posts = cache.get("posts_list")
        if posts is None:
            posts = list(Post.objects.values("id", "title", "content"))
            cache.set("posts_list", posts, 60)
        return Response(posts)

    def post(self, request):
        serializer = PostSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        cache.delete("posts_list")
        return Response(serializer.data, status=status.HTTP_201_CREATED)



class RegisterView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        send_welcome_email_task.delay(user.email)
        return Response(
            {
                "id": user.id,
                "email": user.email,
                "username": user.username,
            },
            status=status.HTTP_201_CREATED,
        )
