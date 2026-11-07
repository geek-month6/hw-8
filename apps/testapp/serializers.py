from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["email"] = user.email
        token["username"] = user.username
        token["role"] = user.role
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["id"] = self.user.id
        data["email"] = self.user.email
        data["username"] = self.user.username
        data["role"] = self.user.role
        return data


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class GoogleAuthSerializer(serializers.Serializer):
    code = serializers.CharField(allow_blank=False, trim_whitespace=True)



from .models import Post


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ("id", "title", "content")



from django.contrib.auth import get_user_model


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = get_user_model()
        fields = ("id", "email", "username", "password")

    def create(self, validated_data):
        User = get_user_model()
        return User.objects.create_user(**validated_data)
