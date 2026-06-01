"""URL configuration for the Legal Cases Management System."""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),

    # Authentication (built-in views; templates under templates/registration/)
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # App routes
    path('', include('accounts.urls')),
    path('cases/', include('cases.urls')),
    path('appointments/', include('appointments.urls')),
]
