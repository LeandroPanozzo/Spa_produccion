from django.urls import path, include
from rest_framework import routers
from rest_framework.documentation import include_docs_urls
from sentirseBien import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import PaymentListViewSet, UserEditViewSet, ProfessionalAppointmentsViewSet, download_invoice, PaymentCreateView, PaymentTypeView, RegisterView, UserDetailView, CustomTokenObtainPairView,QueryViewSet, ProfessionalViewSet, ResponseViewSet, AppointmentViewSet, ServiceViewSet, AnnouncementView, ClientViewSet, ClientsByDayViewSet, ClientsByProfessionalViewSet

router = routers.DefaultRouter()
router.register(r'clients', ClientViewSet, basename='client')  # Listado de clientes
router.register(r'clients-by-day', ClientsByDayViewSet, basename='clients-by-day')  # Listado de clientes a atender hoy
router.register(r'clients-by-professional', ClientsByProfessionalViewSet, basename='clients-by-professional')  # Listado de clientes por profesional
router.register(r'posts', views.PostViewSet, basename='post')
router.register(r'profile', views.ProfileViewSet, basename='profile')
router.register(r'queries', QueryViewSet)
router.register(r'responses', ResponseViewSet)
router.register(r'appointments', AppointmentViewSet, basename='appointment')
router.register(r'services', views.ServiceViewSet, basename='service')
router.register(r'announcements', AnnouncementView, basename='announcement')
router.register(r'professionals', ProfessionalViewSet, basename='professional')
router.register(r'payments', PaymentCreateView, basename='payment')
router.register(r'payment-types', PaymentTypeView, basename='payment-types')
router.register(r'professional/appointments', ProfessionalAppointmentsViewSet, basename='professional-appointments')
router.register(r'payments-list', PaymentListViewSet, basename='payments-list')
router.register(r'user', UserEditViewSet, basename='user')

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
    path('api/v1/appointments/<int:appointment_id>/download_invoice/', download_invoice, name='download_invoice'),
    
]
