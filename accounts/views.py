from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView,
)

from appointments.models import Appointment
from cases.models import Case

from .forms import (
    ClientForm, ClientProfileEditForm, LawyerForm, LawyerProfileEditForm,
)
from .mixins import AdminRequiredMixin
from .models import ClientProfile, LawyerProfile


class DashboardView(LoginRequiredMixin, TemplateView):
    """Role-aware landing page with counts and recent activity."""

    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        cases = Case.objects.for_user(user)
        appts = Appointment.objects.for_user(user)
        upcoming = appts.filter(
            scheduled_for__gte=timezone.now(),
            status=Appointment.Status.SCHEDULED,
        )
        ctx.update({
            'case_count': cases.count(),
            'open_case_count': cases.exclude(status=Case.Status.CLOSED).count(),
            'recent_cases': cases[:5],
            'upcoming_appointments': upcoming[:5],
            'appointment_count': appts.count(),
        })
        if user.is_admin:
            ctx['lawyer_count'] = LawyerProfile.objects.count()
            ctx['client_count'] = ClientProfile.objects.count()
        return ctx


# --- Lawyers ---------------------------------------------------------------
class LawyerListView(AdminRequiredMixin, ListView):
    model = LawyerProfile
    template_name = 'accounts/lawyer_list.html'
    context_object_name = 'lawyers'

    def get_queryset(self):
        return LawyerProfile.objects.select_related('user')


class LawyerDetailView(AdminRequiredMixin, DetailView):
    model = LawyerProfile
    template_name = 'accounts/lawyer_detail.html'
    context_object_name = 'lawyer'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['cases'] = Case.objects.filter(lawyer=self.object).select_related('client__user')
        return ctx


class LawyerCreateView(AdminRequiredMixin, CreateView):
    form_class = LawyerForm
    template_name = 'accounts/person_form.html'
    extra_context = {'title': 'Add Lawyer'}
    success_url = reverse_lazy('lawyer_list')

    def form_valid(self, form):
        messages.success(self.request, 'Lawyer created.')
        return super().form_valid(form)


class LawyerUpdateView(AdminRequiredMixin, UpdateView):
    model = LawyerProfile
    form_class = LawyerProfileEditForm
    template_name = 'accounts/person_form.html'
    extra_context = {'title': 'Edit Lawyer'}
    success_url = reverse_lazy('lawyer_list')

    def form_valid(self, form):
        messages.success(self.request, 'Lawyer updated.')
        return super().form_valid(form)


class LawyerDeleteView(AdminRequiredMixin, DeleteView):
    model = LawyerProfile
    template_name = 'accounts/confirm_delete.html'
    success_url = reverse_lazy('lawyer_list')

    def form_valid(self, form):
        user = self.object.user
        response = super().form_valid(form)
        user.delete()  # remove the underlying account too
        messages.success(self.request, 'Lawyer removed.')
        return response


# --- Clients ---------------------------------------------------------------
class ClientListView(AdminRequiredMixin, ListView):
    model = ClientProfile
    template_name = 'accounts/client_list.html'
    context_object_name = 'clients'

    def get_queryset(self):
        return ClientProfile.objects.select_related('user')


class ClientDetailView(AdminRequiredMixin, DetailView):
    model = ClientProfile
    template_name = 'accounts/client_detail.html'
    context_object_name = 'client'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['cases'] = Case.objects.filter(client=self.object).select_related('lawyer__user')
        return ctx


class ClientCreateView(AdminRequiredMixin, CreateView):
    form_class = ClientForm
    template_name = 'accounts/person_form.html'
    extra_context = {'title': 'Add Client'}
    success_url = reverse_lazy('client_list')

    def form_valid(self, form):
        messages.success(self.request, 'Client created.')
        return super().form_valid(form)


class ClientUpdateView(AdminRequiredMixin, UpdateView):
    model = ClientProfile
    form_class = ClientProfileEditForm
    template_name = 'accounts/person_form.html'
    extra_context = {'title': 'Edit Client'}
    success_url = reverse_lazy('client_list')

    def form_valid(self, form):
        messages.success(self.request, 'Client updated.')
        return super().form_valid(form)


class ClientDeleteView(AdminRequiredMixin, DeleteView):
    model = ClientProfile
    template_name = 'accounts/confirm_delete.html'
    success_url = reverse_lazy('client_list')

    def form_valid(self, form):
        user = self.object.user
        response = super().form_valid(form)
        user.delete()
        messages.success(self.request, 'Client removed.')
        return response
