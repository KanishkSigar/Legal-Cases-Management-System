from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import ClientProfile, LawyerProfile, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'get_full_name', 'role', 'email', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Legal CMS', {'fields': ('role', 'phone')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Legal CMS', {'fields': ('role', 'phone')}),
    )


@admin.register(LawyerProfile)
class LawyerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialization', 'bar_number')
    search_fields = ('user__first_name', 'user__last_name', 'specialization', 'bar_number')


@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'company', 'address')
    search_fields = ('user__first_name', 'user__last_name', 'company')
