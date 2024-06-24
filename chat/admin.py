# admin.py
from django.contrib import admin
from .models import User, Otp, Community

admin.site.register(User)
admin.site.register(Otp)
admin.site.register(Community)