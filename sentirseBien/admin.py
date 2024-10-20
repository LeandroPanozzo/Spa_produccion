from django.contrib import admin #admin.py
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm
from .models import Profile, Post, Respuesta, Query, Service, Appointment, Announcement, User, PaymentType, Payment

class CustomUserAdmin(UserAdmin):
    model = User
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('is_owner', 'is_professional', 'is_secretary', 'cuit')}),
    )

admin.site.register(User, CustomUserAdmin)
admin.site.register(Profile)
##admin.site.register(EmployeeType)
admin.site.register(Post)
admin.site.register(Respuesta)
admin.site.register(Query)
admin.site.register(Service)
admin.site.register(Appointment)
admin.site.register(Announcement)
admin.site.register(Payment)
admin.site.register(PaymentType)

