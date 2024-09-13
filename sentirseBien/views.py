from rest_framework import viewsets, permissions, status, generics
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Profile, Post
from django.contrib.auth.models import User
from rest_framework.permissions import AllowAny
from .serializer import ProfileSerializer, PostSerializer, RegisterSerializer, UserDetailSerializer, CustomTokenObtainPairSerializer, QuerySerializer, ResponseSerializer, AppointmentSerializer, ServiceSerializer, AnnouncementSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import serializers
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .permissions import IsStaffAndReadOrEditOnly, IsStaff
from rest_framework.permissions import IsAuthenticated
from .models import Query, Response, Appointment, Service, Announcement

class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
        

class AnnouncementView(viewsets.ModelViewSet):
    queryset = Announcement.objects.all()
    serializer_class = AnnouncementSerializer
    permission_classes = [IsStaff]
    
    def get_queryset(self):
        return Announcement.objects.order_by('-created_at')  # Orden descendente por created_at
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [IsStaffAndReadOrEditOnly, IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        
    def get_queryset(self):
        
        if self.request.user.is_staff:
            # Empleados ven todos los appointments
            return Appointment.objects.all()
        else:
            # Usuarios normales ven solo sus appointments
            return Appointment.objects.filter(user=self.request.user)

class QueryViewSet(viewsets.ModelViewSet):
    queryset = Query.objects.all()
    serializer_class = QuerySerializer
    permission_classes = [IsAuthenticated, IsStaffAndReadOrEditOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        
    def get_queryset(self):
        
        if self.request.user.is_staff:
            # Empleados ven todos los appointments
            return Query.objects.all()
        else:
            # Usuarios normales ven solo sus appointments
            return Query.objects.filter(user=self.request.user)

class ResponseViewSet(viewsets.ModelViewSet):
    queryset = Response.objects.all()
    serializer_class = ResponseSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        
    def get_queryset(self):
        
        if self.request.user.is_staff:
            # Empleados ven todos los appointments
            return Response.objects.all()
        else:
            # Usuarios normales ven solo sus appointments
            return Response.objects.filter(user=self.request.user)

class ProfileViewSet(viewsets.ModelViewSet):
    serializer_class = ProfileSerializer
    queryset = Profile.objects.all()

    @action(detail=True, methods=['delete'])
    def delete_profile(self, request, pk=None):
        profile = get_object_or_404(Profile, pk=pk)
        profile.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all().order_by('-fecha_posteo')
    serializer_class = PostSerializer
    
    def perform_create(self, serializer):
        user = self.request.user
        if user.is_authenticated:
            # Usuario autenticado, asignar `autor` y dejar `alias` como `null`
            serializer.save(autor=user, alias=None)
        else:
            # Usuario no autenticado, asignar `alias` y dejar `autor` como `null`
            alias = self.request.data.get('alias', None)
            serializer.save(autor=None, alias=alias)

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        refresh = RefreshToken.for_user(user)
        return Response({
            "user": RegisterSerializer(user, context=self.get_serializer_context()).data,
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        })
        
# En views.py
from rest_framework import generics
from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticated

class UserDetailView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserDetailSerializer
    permission_classes = [IsAuthenticated]
    
from rest_framework_simplejwt.views import TokenObtainPairView

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
