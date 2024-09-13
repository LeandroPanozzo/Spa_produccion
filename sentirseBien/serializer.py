# serializer.py
from datetime import timezone
from rest_framework import serializers
from .models import Profile
from django.contrib.auth.models import User  # Añade esta línea

from .models import Query, Response, Service, Appointment, Announcement

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['id', 'name']
        
class AnnouncementSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = Announcement
        fields = '__all__'

        
class AppointmentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    service_id = serializers.PrimaryKeyRelatedField(
        queryset=Service.objects.all(),
        source='service',
        write_only=True
    )
    service_name = serializers.CharField(source='service.name', read_only=True)

    class Meta:
        model = Appointment
        fields = ['id', 'user', 'service_id', 'service_name', 'appointment_date']
        read_only_fields = ['user']
        
class ResponseSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Response
        fields = ['id', 'user', 'content', 'created_at', 'query']
        read_only_fields = ['user']
        
class QuerySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    responses = ResponseSerializer(many=True, read_only=True)

    class Meta:
        model = Query
        fields = ['id', 'user', 'title', 'content', 'created_at', 'responses']
        read_only_fields = ['user']





class ProfileSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = ['id', 'user', 'image_url']

    def get_image_url(self, obj):
        return obj.get_profile_image_url()

# PostSerializer
from django.utils import timezone
from rest_framework import serializers
from .models import Post

class PostSerializer(serializers.ModelSerializer):
    autor = serializers.StringRelatedField()
    time_since_posted = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['id', 'titulo', 'contenido', 'fecha_posteo', 'autor', 'time_since_posted', 'alias']
        ##read_only_fields = ['autor']
    
    def get_time_since_posted(self, obj):
        # Calcula el tiempo transcurrido desde la publicación
        time_diff = timezone.now() - obj.fecha_posteo
        return f"{time_diff.days} days, {time_diff.seconds // 3600} hours ago"


# Serializador para el registro de usuario
# serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'confirm_password']

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Las contraseñas no coinciden")
        return data

    def create(self, validated_data):
        user = User(
            username=validated_data['username'],
            email=validated_data['email']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


    
# En serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User

class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'date_joined', 'is_staff']
        read_only_fields = ['id', 'date_joined', 'is_staff']
        
from rest_framework import generics
from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticated

class UserDetailView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserDetailSerializer
    permission_classes = [IsAuthenticated]
    
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer): #autenticación con JWT
    def validate(self, attrs):
        data = super().validate(attrs)
        data.update({'username': self.user.username})
        data.update({'email': self.user.email})
        return data
