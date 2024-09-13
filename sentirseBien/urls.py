from django.urls import path, include
from rest_framework import routers
from rest_framework.documentation import include_docs_urls
from sentirseBien import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import RegisterView, UserDetailView, CustomTokenObtainPairView,QueryViewSet, ResponseViewSet, AppointmentViewSet, ServiceViewSet, AnnouncementView

router = routers.DefaultRouter()
router.register(r'posts', views.PostViewSet, basename='post')
router.register(r'profile', views.ProfileViewSet, basename='profile')
router.register(r'queries', QueryViewSet)
router.register(r'responses', ResponseViewSet)
router.register(r'appointments', AppointmentViewSet, basename='appointment')
router.register(r'services', views.ServiceViewSet, basename='service')
router.register(r'announcements', AnnouncementView, basename='announcement')

urlpatterns = [
    path('api/v1/', include(router.urls)),
    ##path('', include(router.urls)),
    path('documentacion/', include_docs_urls(title= "sentirseBien API")),
    path('api/v1/register/', RegisterView.as_view(), name='register'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('api/v1/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/v1/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
]
