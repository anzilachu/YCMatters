from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class User(AbstractUser):
    email = models.EmailField(unique=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

class Otp(models.Model):
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    expiry_time = models.DateTimeField()

    def is_expired(self):
        return timezone.now() > self.expiry_time

    def __str__(self):
        return f"{self.email} - {self.otp}"

    class Meta:
        verbose_name = "Otp"
        verbose_name_plural = "Otps"

class Community(models.Model):
    email = models.EmailField(unique=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email
    
class Feedback(models.Model):
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message