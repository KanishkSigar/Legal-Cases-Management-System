from django.contrib import admin

from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'scheduled_for', 'lawyer', 'client', 'status')
    list_filter = ('status', 'lawyer')
    search_fields = ('title', 'location', 'notes')
    date_hierarchy = 'scheduled_for'
    autocomplete_fields = ('lawyer', 'client', 'case')
