from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView
from django.urls import path, reverse_lazy

from . import views


def _pw(view, template, **kw):
    return view.as_view(template_name=f'accounts/{template}', **kw)

urlpatterns = [
    # Public
    path('', views.LandingView.as_view(), name='landing'),

    # One-time DB setup from the browser (optional ?token= via SETUP_TOKEN env)
    path('setup/', views.setup_view, name='setup'),

    # Authentication
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('login/', views.PortalLoginView.as_view(), name='login'),
    path('staff/login/', views.AdminLoginView.as_view(), name='admin_login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    # Password change (logged in)
    path('password/change/', _pw(auth_views.PasswordChangeView, 'password_change.html',
         success_url=reverse_lazy('password_change_done')), name='password_change'),
    path('password/change/done/', _pw(auth_views.PasswordChangeDoneView, 'password_change_done.html'),
         name='password_change_done'),
    # Password reset (forgot password)
    path('password/reset/', _pw(auth_views.PasswordResetView, 'password_reset.html',
         email_template_name='accounts/password_reset_email.txt',
         subject_template_name='accounts/password_reset_subject.txt',
         success_url=reverse_lazy('password_reset_done')), name='password_reset'),
    path('password/reset/done/', _pw(auth_views.PasswordResetDoneView, 'password_reset_done.html'),
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/', _pw(auth_views.PasswordResetConfirmView, 'password_reset_confirm.html',
         success_url=reverse_lazy('password_reset_complete')), name='password_reset_confirm'),
    path('reset/done/', _pw(auth_views.PasswordResetCompleteView, 'password_reset_complete.html'),
         name='password_reset_complete'),

    # Authenticated app
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
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
