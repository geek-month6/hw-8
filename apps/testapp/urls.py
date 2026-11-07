from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .serializers import CustomTokenObtainPairSerializer
from .views import GoogleAuthView, LogoutView, ProfileStatsView, PostsView, RegisterView
from rest_framework_simplejwt.views import TokenObtainPairView


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("v1/posts/", PostsView.as_view(), name="posts_list"),
    path("google/", GoogleAuthView.as_view(), name="google_auth"),
    path("token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("profile/stats/", ProfileStatsView.as_view(), name="profile_stats"),
]
