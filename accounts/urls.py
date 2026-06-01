from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

urlpatterns = [
    # Public
    path('', views.LandingView.as_view(), name='landing'),

    # Authentication
    path('login/', views.PortalLoginView.as_view(), name='login'),
    path('staff/login/', views.AdminLoginView.as_view(), name='admin_login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    # Authenticated app
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('our-lawyers/', views.LawyerDirectoryView.as_view(), name='lawyer_directory'),

    # Lawyers (admin management)
    path('manage/lawyers/', views.LawyerListView.as_view(), name='lawyer_list'),
    path('manage/lawyers/add/', views.LawyerCreateView.as_view(), name='lawyer_add'),
    path('manage/lawyers/<int:pk>/', views.LawyerDetailView.as_view(), name='lawyer_detail'),
    path('manage/lawyers/<int:pk>/edit/', views.LawyerUpdateView.as_view(), name='lawyer_edit'),
    path('manage/lawyers/<int:pk>/delete/', views.LawyerDeleteView.as_view(), name='lawyer_delete'),

    # Clients (admin management)
    path('manage/clients/', views.ClientListView.as_view(), name='client_list'),
    path('manage/clients/add/', views.ClientCreateView.as_view(), name='client_add'),
    path('manage/clients/<int:pk>/', views.ClientDetailView.as_view(), name='client_detail'),
    path('manage/clients/<int:pk>/edit/', views.ClientUpdateView.as_view(), name='client_edit'),
    path('manage/clients/<int:pk>/delete/', views.ClientDeleteView.as_view(), name='client_delete'),
]
