from django.contrib import admin #admin.py
from .models import Profile, Post, Response, Query, Service, Appointment, Announcement

admin.site.register(Profile)
admin.site.register(Post)
admin.site.register(Response)
admin.site.register(Query)
admin.site.register(Service)
admin.site.register(Appointment)
admin.site.register(Announcement)
