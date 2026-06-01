from django.urls import path

from . import views

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),

    # Lawyers
    path('lawyers/', views.LawyerListView.as_view(), name='lawyer_list'),
    path('lawyers/add/', views.LawyerCreateView.as_view(), name='lawyer_add'),
    path('lawyers/<int:pk>/', views.LawyerDetailView.as_view(), name='lawyer_detail'),
    path('lawyers/<int:pk>/edit/', views.LawyerUpdateView.as_view(), name='lawyer_edit'),
    path('lawyers/<int:pk>/delete/', views.LawyerDeleteView.as_view(), name='lawyer_delete'),

    # Clients
    path('clients/', views.ClientListView.as_view(), name='client_list'),
    path('clients/add/', views.ClientCreateView.as_view(), name='client_add'),
    path('clients/<int:pk>/', views.ClientDetailView.as_view(), name='client_detail'),
    path('clients/<int:pk>/edit/', views.ClientUpdateView.as_view(), name='client_edit'),
    path('clients/<int:pk>/delete/', views.ClientDeleteView.as_view(), name='client_delete'),
]
