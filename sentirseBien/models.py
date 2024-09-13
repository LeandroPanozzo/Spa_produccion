from django.db import models #models.py
from django.utils import timezone
from django.contrib.auth.models import User
from django.urls import reverse
from PIL import Image

from django.db import models
from django.contrib.auth.models import User

class Service(models.Model):
    name = models.CharField(max_length=100)
    
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

class Appointment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    appointment_date = models.DateTimeField(null = False, auto_now=False, auto_now_add=False)
    
    def __str__(self):
        return self.user.username + " " + self.service.name
    

class Query(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.user.username + ' Consulta: ' + self.title

class Response(models.Model):
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
    isEmployee = models.BooleanField(default=False)
    
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