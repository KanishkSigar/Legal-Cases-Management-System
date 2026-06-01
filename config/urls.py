"""URL configuration for the Legal Cases Management System."""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),

    # Public + auth + dashboard + people management
    path('', include('accounts.urls')),

    # Domain apps
    path('cases/', include('cases.urls')),
    path('appointments/', include('appointments.urls')),
]
