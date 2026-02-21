"""Users app URL configuration."""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import SignUpView, SignInView, UserProfileView

app_name = 'users'

urlpatterns = [
    # Authentication endpoints
    path('signup/', SignUpView.as_view(), name='signup'),
    path('signin/', SignInView.as_view(), name='signin'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # User profile endpoints
    path('me/', UserProfileView.as_view(), name='profile'),
]