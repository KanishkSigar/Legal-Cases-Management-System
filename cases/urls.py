from django.urls import path

from . import views

urlpatterns = [
    path('', views.CaseListView.as_view(), name='case_list'),
    path('add/', views.CaseCreateView.as_view(), name='case_add'),
    path('<int:pk>/', views.CaseDetailView.as_view(), name='case_detail'),
    path('<int:pk>/edit/', views.CaseUpdateView.as_view(), name='case_edit'),
    path('<int:pk>/delete/', views.CaseDeleteView.as_view(), name='case_delete'),
]
