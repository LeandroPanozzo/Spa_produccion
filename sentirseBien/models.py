from django.db import models #models.py
from django.utils import timezone
from django.urls import reverse
from PIL import Image
from datetime import timedelta

from django.db import models
from django.contrib.auth.models import AbstractUser

"""class EmployeeType(models.Model):
    name = models.CharField(max_length=100)
    
    def __str__(self) -> str:
        return self.name    """

class User(AbstractUser):
    """
    Users within the Django authentication system are represented by this
    model.

    Username and password are required. Other fields are optional.
    """   
    email = models.EmailField(unique=True)
    is_owner = models.BooleanField(default=False)
    is_professional = models.BooleanField(default=False)
    is_secretary = models.BooleanField(default=False)
    cuit = models.CharField(max_length=11, null=True, blank=True)  # CUIT del cliente
    ##employeeType = models.ForeignKey(EmployeeType, on_delete=models.RESTRICT, null=True, blank=True)
    class Meta(AbstractUser.Meta):
        swappable = "AUTH_USER_MODEL"

class Service(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return self.name
    
class Announcement(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    date_description = models.CharField(max_length=100)
    user = models.ForeignKey(User, null=True ,on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return 'Anuncio: ' + self.title
    
class PaymentType(models.Model):
    name = models.CharField(max_length=50, null=False)
    
    def __str__(self):
        return 'Tipo de Pago: ' + self.name
    
class Payment(models.Model):
    
    total_payment = models.DecimalField(max_digits=20, decimal_places=2)
    discount = models.DecimalField(max_digits=2, decimal_places=2, default=0.0)
    payment_type = models.ForeignKey(PaymentType, null=False, on_delete=models.CASCADE)
    payment_date = models.DateTimeField(null=False, auto_now_add=True)
    credit_card = models.CharField(max_length=16, null=True, blank=True)
    pin = models.CharField(max_length=4, null=True, blank=True)
    appointment = models.OneToOneField('Appointment', null=True, blank=False, on_delete=models.CASCADE, related_name='payment_appointment')
    
    def save(self, *args, **kwargs):
        # Validación de tarjeta de crédito antes de guardar
        if self.credit_card and not self.is_valid_credit_card():
            raise ValueError("Número de tarjeta de crédito no válido.")
        super().save(*args, **kwargs)

    def is_valid_credit_card(self):
        
        return len(self.credit_card) == 16 and self.credit_card.isdigit()  # Comprueba longitud y que sean solo dígitos


class Appointment(models.Model):
    client = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=False, related_name='client_appointment')
    professional = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=False, related_name='professional_appointment')
    services = models.ManyToManyField(Service)
    appointment_date = models.DateTimeField(null = False, auto_now=False, auto_now_add=False)
    payment = models.OneToOneField(Payment, null=True,blank=True, on_delete=models.CASCADE, related_name='appointment_payment')
    payment_deadline = models.DateTimeField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        # Guardar la cita primero para tener acceso a la fecha
        super().save(*args, **kwargs)  

        # Calcular el payment_deadline solo si la cita se creó dentro de las 48 horas
        if self.appointment_date <= timezone.now() + timedelta(hours=48):
            self.payment_deadline = timezone.now() + timedelta(minutes=30)
        else:
            self.payment_deadline = None  # O manejar según tus necesidades

        # Guardar de nuevo para que el payment_deadline se almacene
        super().save(update_fields=['payment_deadline'])  # Actualiza solo el payment_deadline

    
    def __str__(self):
        service_names = ', '.join([service.name for service in self.services.all()])
        return f"{self.client.username} - Servicios: {service_names}"
    
from django.dispatch import receiver
from django.db.models.signals import post_save

def check_appointments_without_payment(sender, instance, **kwargs):
    now = timezone.now()
    
    # Verificar citas que están a menos de 48 horas y no tienen un pago asociado
    appointments = Appointment.objects.filter(
        payment__isnull=True,
        appointment_date__lt=now + timedelta(hours=48)
    )

    # Eliminar citas que no tengan pago asociado y que excedan el límite de tiempo
    for appointment in appointments:
        if appointment.payment_deadline and now > appointment.payment_deadline:
            appointment.delete()
    

class Query(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.user.username + ' Consulta: ' + self.title

class Respuesta(models.Model):
    query = models.ForeignKey(Query, on_delete=models.CASCADE, related_name='responses')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class Post(models.Model):
    titulo = models.CharField(max_length=100)
    contenido = models.TextField()
    fecha_posteo = models.DateTimeField(default=timezone.now)
    autor = models.ForeignKey(User, on_delete=models.CASCADE, null = True, blank = True)  # Clave foránea
    alias = models.CharField(max_length=25, null= True, blank= True)
    
    def __str__(self):
        return self.titulo
    
    def get_absolute_url(self):
        return reverse('post-detail', kwargs={'pk': self.pk})
    
    def set_titulo(self, nuevo_titulo):
        self.titulo = nuevo_titulo
        self.save()

    def set_contenido(self, nuevo_contenido):
        self.contenido = nuevo_contenido
        self.save()

    def set_autor(self, nuevo_autor):
        if isinstance(nuevo_autor, User):
            self.autor = nuevo_autor
            self.save()
        else:
            raise ValueError("El autor debe ser una instancia de User")



class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(default='default.jpg', upload_to='profile_pics')
    
    
    def __str__(self):
        return f'{self.user.username} profile'
    
    def get_user_id(self):
        return self.user.id
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        img = Image.open(self.image.path)
        
        if img.height > 300 or img.width > 300:
            output_size = (300, 300)
            img.thumbnail(output_size)
            img.save(self.image.path)
    
    def get_full_name(self):
        return f'{self.user.first_name} {self.user.last_name}'
    
    def get_profile_image_url(self):
        if self.image and hasattr(self.image, 'url'):
            return self.image.url
        return '/path/to/default/image.jpg'

    def set_image(self, nueva_imagen):
        self.image = nueva_imagen
        self.save()

    def set_user(self, nuevo_user):
        if isinstance(nuevo_user, User):
            self.user = nuevo_user
            self.save()
        else:
            raise ValueError("El usuario debe ser una instancia de User")