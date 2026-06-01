from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user with a role that drives access across the app."""

    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        LAWYER = 'LAWYER', 'Lawyer'
        CLIENT = 'CLIENT', 'Client'

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.CLIENT)
    phone = models.CharField(max_length=30, blank=True)

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    @property
    def is_lawyer(self):
        return self.role == self.Role.LAWYER

    @property
    def is_client(self):
        return self.role == self.Role.CLIENT

    def get_full_name(self):
        return super().get_full_name() or self.username

    def __str__(self):
        return f'{self.get_full_name()} ({self.get_role_display()})'


class LawyerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='lawyer_profile')
    specialization = models.CharField(max_length=120, blank=True)
    bar_number = models.CharField(max_length=60, blank=True)
    bio = models.TextField(blank=True)

    class Meta:
        ordering = ['user__first_name', 'user__last_name']

    def __str__(self):
        return self.user.get_full_name()


class ClientProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='client_profile')
    address = models.CharField(max_length=255, blank=True)
    company = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ['user__first_name', 'user__last_name']

    def __str__(self):
        return self.user.get_full_name()
