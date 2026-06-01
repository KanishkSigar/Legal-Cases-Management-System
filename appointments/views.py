from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView, View,
)

from accounts.mixins import StaffRequiredMixin

from .forms import AppointmentForm
from .models import Appointment


class AppointmentListView(LoginRequiredMixin, ListView):
    model = Appointment
    template_name = 'appointments/appointment_list.html'
    context_object_name = 'appointments'
    paginate_by = 20

    def get_queryset(self):
        qs = Appointment.objects.for_user(self.request.user).select_related(
            'lawyer__user', 'client__user', 'case',
        )
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['statuses'] = Appointment.Status.choices
        ctx['current_status'] = self.request.GET.get('status', '')
        return ctx


class AppointmentDetailView(LoginRequiredMixin, DetailView):
    model = Appointment
    template_name = 'appointments/appointment_detail.html'
    context_object_name = 'appointment'

    def get_queryset(self):
        return Appointment.objects.for_user(self.request.user).select_related(
            'lawyer__user', 'client__user', 'case',
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        ctx['can_edit'] = user.is_admin or (
            user.is_lawyer and self.object.lawyer.user_id == user.id
        )
        return ctx


class AppointmentCreateView(StaffRequiredMixin, CreateView):
    model = Appointment
    form_class = AppointmentForm
    template_name = 'appointments/appointment_form.html'
    extra_context = {'title': 'New Appointment'}

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Appointment scheduled.')
        return super().form_valid(form)


class AppointmentUpdateView(StaffRequiredMixin, UpdateView):
    model = Appointment
    form_class = AppointmentForm
    template_name = 'appointments/appointment_form.html'
    extra_context = {'title': 'Edit Appointment'}

    def get_queryset(self):
        return Appointment.objects.for_user(self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Appointment updated.')
        return super().form_valid(form)


class AppointmentDeleteView(StaffRequiredMixin, DeleteView):
    model = Appointment
    template_name = 'appointments/appointment_confirm_delete.html'
    success_url = reverse_lazy('appointment_list')

    def get_queryset(self):
        return Appointment.objects.for_user(self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Appointment deleted.')
        return super().form_valid(form)


class AppointmentStatusView(StaffRequiredMixin, View):
    """Quick action to mark an appointment completed / cancelled."""

    def post(self, request, pk):
        appt = get_object_or_404(Appointment.objects.for_user(request.user), pk=pk)
        new_status = request.POST.get('status')
        valid = dict(Appointment.Status.choices)
        if new_status in valid:
            appt.status = new_status
            appt.save(update_fields=['status'])
            messages.success(request, f'Appointment marked {valid[new_status].lower()}.')
        return redirect('appointment_detail', pk=pk)
