from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView,
)

from accounts.mixins import StaffRequiredMixin

from .forms import CaseForm, CaseNoteForm, CaseStatusForm
from .models import Case


class CaseListView(LoginRequiredMixin, ListView):
    model = Case
    template_name = 'cases/case_list.html'
    context_object_name = 'cases'
    paginate_by = 15

    SORTS = {
        'newest': '-opened_date', 'oldest': 'opened_date',
        'number': 'case_number', 'title': 'title', 'status': 'status',
    }

    def get_queryset(self):
        qs = Case.objects.for_user(self.request.user).select_related(
            'client__user', 'lawyer__user',
        )
        status = self.request.GET.get('status')
        case_type = self.request.GET.get('type')
        q = self.request.GET.get('q', '').strip()
        if status:
            qs = qs.filter(status=status)
        if case_type:
            qs = qs.filter(case_type=case_type)
        if q:
            qs = qs.filter(
                Q(case_number__icontains=q) | Q(title__icontains=q)
                | Q(client__user__first_name__icontains=q)
                | Q(client__user__last_name__icontains=q)
            )
        return qs.order_by(self.SORTS.get(self.request.GET.get('sort'), '-opened_date'))

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['statuses'] = Case.Status.choices
        ctx['types'] = Case.Type.choices
        ctx['current_status'] = self.request.GET.get('status', '')
        ctx['current_type'] = self.request.GET.get('type', '')
        ctx['q'] = self.request.GET.get('q', '')
        ctx['current_sort'] = self.request.GET.get('sort', 'newest')
        return ctx


class CaseDetailView(LoginRequiredMixin, DetailView):
    model = Case
    template_name = 'cases/case_detail.html'
    context_object_name = 'case'

    def get_queryset(self):
        return Case.objects.for_user(self.request.user).select_related(
            'client__user', 'lawyer__user',
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['notes'] = self.object.notes.select_related('author')
        ctx['note_form'] = CaseNoteForm()
        ctx['status_form'] = CaseStatusForm(instance=self.object)
        ctx['can_edit'] = self._can_edit(self.request.user, self.object)
        return ctx

    @staticmethod
    def _can_edit(user, case):
        return user.is_admin or (user.is_lawyer and case.lawyer.user_id == user.id)

    def post(self, request, *args, **kwargs):
        """Handle adding a note or updating status from the detail page."""
        self.object = self.get_object()
        if not self._can_edit(request.user, self.object):
            raise PermissionDenied
        action = request.POST.get('action')
        if action == 'add_note':
            form = CaseNoteForm(request.POST)
            if form.is_valid():
                note = form.save(commit=False)
                note.case = self.object
                note.author = request.user
                note.save()
                messages.success(request, 'Note added.')
        elif action == 'update_status':
            form = CaseStatusForm(request.POST, instance=self.object)
            if form.is_valid():
                form.save()
                messages.success(request, 'Status updated.')
        return redirect('case_detail', pk=self.object.pk)


class CaseCreateView(StaffRequiredMixin, CreateView):
    model = Case
    form_class = CaseForm
    template_name = 'cases/case_form.html'
    extra_context = {'title': 'New Case'}

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Case created.')
        return super().form_valid(form)


class CaseUpdateView(StaffRequiredMixin, UpdateView):
    model = Case
    form_class = CaseForm
    template_name = 'cases/case_form.html'
    extra_context = {'title': 'Edit Case'}

    def get_queryset(self):
        # Lawyers may only edit their own cases.
        return Case.objects.for_user(self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Case updated.')
        return super().form_valid(form)


class CaseDeleteView(StaffRequiredMixin, DeleteView):
    model = Case
    template_name = 'cases/case_confirm_delete.html'
    success_url = reverse_lazy('case_list')

    def get_queryset(self):
        return Case.objects.for_user(self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Case deleted.')
        return super().form_valid(form)
