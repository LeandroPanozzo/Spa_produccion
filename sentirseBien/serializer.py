# serializer.py
from datetime import timezone
from rest_framework import serializers
from .models import Profile
#from django.contrib.auth.models import User  # Añade esta línea

from .models import Query, Respuesta, Service, Appointment, Announcement, User, Payment, PaymentType

class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['cuit', 'first_name', 'last_name', 'email', 'password','is_owner', 'is_professional', 'is_secretary']
        read_only_fields = ['is_owner', 'is_professional', 'is_secretary']
        extra_kwargs = {
            'password': {'write_only': True, 'required': False}  # No es obligatorio
        }

    def update(self, instance, validated_data):
        # Extraemos la contraseña del validated_data
        password = validated_data.pop('password', None)

        # Actualizamos otros campos
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Solo actualizamos la contraseña si se proporciona
        if password:
            instance.set_password(password)

        # Guardamos la instancia
        instance.save()
        return instance  # Retornamos la instancia actualizada

class UserSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = User
        fields = ['id', 'username', 'is_owner', 'is_professional', 'is_secretary', 'cuit', 'first_name', 'last_name']
        read_only_fields = ['is_owner', 'is_professional', 'is_secretary']

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['id', 'name', 'price']
        
class AnnouncementSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = Announcement
        fields = '__all__'
        
class PaymentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentType
        fields = ['id', 'name']  # Incluye el ID y el nombre del tipo de pago

from decimal import Decimal

class PaymentSerializer(serializers.ModelSerializer):
    appointment = serializers.PrimaryKeyRelatedField(queryset=Appointment.objects.all())  # Asegúrate de que esto está presente
    
    payment_type = serializers.PrimaryKeyRelatedField(queryset=PaymentType.objects.all())
    total_payment = serializers.DecimalField(max_digits=20, decimal_places=2, read_only=True)

    class Meta:
        model = Payment
        fields = ['id','appointment', 'total_payment', 'payment_type', 'credit_card', 'pin', 'payment_date', 'discount']
        extra_kwargs = {'credit_card': {'write_only': True}, 'pin': {'write_only': True}}

    def create(self, validated_data):
        # No se necesita hacer pop aquí, ya que ya se valida correctamente como un ID
        appointment_instance = validated_data.pop('appointment')
        discount = validated_data.pop('discount', Decimal('0'))  # Usa 0 como valor por defecto si no hay descuento
        # Calcular el total del pago basado en los servicios asociados
        total_payment = sum(service.price for service in appointment_instance.services.all()) * (Decimal('1') - Decimal(discount))
        validated_data['total_payment'] = total_payment
        validated_data['discount'] = discount
        payment = Payment.objects.create(appointment=appointment_instance, **validated_data)
        
        appointment_instance.payment = payment
        appointment_instance.save()  # Guardar la cita para actualizar la relación
        return payment
        
class AppointmentSerializer(serializers.ModelSerializer):
    client = UserSerializer(read_only=True)
    professional_id = serializers.PrimaryKeyRelatedField(
        queryset = User.objects.all(),
        source = 'professional',
        write_only=True
    )
    professional = UserSerializer(read_only = True)
    services_ids = serializers.PrimaryKeyRelatedField(
        queryset=Service.objects.all(),
        source='services',
        many=True,
        write_only=True
    )
    services_names = serializers.SlugRelatedField(many=True, source='services', slug_field='name', read_only=True)
    services_prices = serializers.SlugRelatedField(many=True, source='services', slug_field='price', read_only = True)
    payment = PaymentSerializer(read_only=True)  # Asegúrate de que PaymentSerializer esté definido

    class Meta:
        model = Appointment
        fields = ['id', 'client', 'professional', 'professional_id', 'services_ids', 'services_names', 'services_prices', 'appointment_date', 'payment']
        read_only_fields = ['client']
        
class ResponseSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Respuesta
        fields = ['id', 'user', 'content', 'created_at', 'query']
        read_only_fields = ['user']
        
class QuerySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    responses = ResponseSerializer(many=True, read_only=True)

    class Meta:
        model = Query
        fields = ['id', 'user', 'title', 'content', 'created_at', 'responses']
        read_only_fields = ['user']



"""class EmployeeTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeType
        fields = ['id', 'name'] """

class ProfileSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    image_url = serializers.SerializerMethodField()
    employeeType = serializers.StringRelatedField()

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
import re
#from django.contrib.auth.models import User

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'cuit', 'email', 'password', 'confirm_password']
        
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("El nombre de usuario ya está en uso.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("El correo electrónico ya está en uso.")
        return value
    
    def validate_cuit(self, value):
        if not re.match(r'^\d{11}$', value):
            raise serializers.ValidationError("El CUIT deben ser exactamente 11 dígitos numéricos.")
        return value

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Las contraseñas no coinciden")
        return data
    
    def create(self, validated_data):
        user = User(
            username=validated_data['username'],
            email=validated_data['email'],
            cuit=validated_data['cuit'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


    
# En serializers.py
from rest_framework import serializers
#from django.contrib.auth.models import User

class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'date_joined', 'is_staff','is_owner', 'is_professional', 'is_secretary', 'first_name', 'last_name']
        read_only_fields = ['id', 'date_joined', 'is_staff']
        
from rest_framework import generics
#from django.contrib.auth.models import User
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
