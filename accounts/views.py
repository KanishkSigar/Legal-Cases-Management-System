import io
import os
import secrets

from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.core.management import call_command
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView,
)

from appointments.models import Appointment
from cases.models import Case

from .forms import (
    AccountForm, ClientForm, ClientProfileEditForm, LawyerForm,
    LawyerProfileEditForm, PortalAuthForm, SignUpForm,
)
from .mixins import AdminRequiredMixin
from .models import ClientProfile, LawyerProfile


# --- One-time setup ---------------------------------------------------------
@csrf_exempt
def setup_view(request):
    """Initialise the database from the browser (one-time, no shell needed).

    Runs migrations (always — idempotent) and creates the first administrator
    if none exists yet. Because the serverless host has no shell, this is how
    the schema gets created after the first deploy. Usage:

        /setup/?username=admin&password=YourStrongPass

    If you omit the password a strong one is generated and shown once. After an
    admin exists the endpoint refuses to create more. If you set a SETUP_TOKEN
    env var, callers must also pass ?token=<that value>.
    """
    required = os.environ.get('SETUP_TOKEN')
    if required and request.GET.get('token') != required:
        return HttpResponseForbidden('Missing or invalid ?token=.')

    out = io.StringIO()

    # Safe diagnostics: /setup/?debug=1 shows the effective DB config (never the
    # password value — only its length). Disabled unless a SETUP_TOKEN is set
    # (and matched above), so it can't leak details on a live site.
    if request.GET.get('debug'):
        if not required:
            return HttpResponseForbidden('Diagnostics disabled. Set SETUP_TOKEN to enable.')
        from django.conf import settings as _s
        db = _s.DATABASES['default']
        out.write('== effective DB config (no secrets) ==\n')
        out.write(f"ENGINE        : {db.get('ENGINE')}\n")
        out.write(f"HOST          : {db.get('HOST')}\n")
        out.write(f"PORT          : {db.get('PORT')}\n")
        out.write(f"NAME          : {db.get('NAME')}\n")
        out.write(f"USER          : {db.get('USER')}\n")
        _pw = str(db.get('PASSWORD') or '')
        out.write(f"PASSWORD len  : {len(_pw)}\n")
        out.write(f"PASSWORD has surrounding whitespace : {_pw != _pw.strip()}\n")
        out.write(f"PASSWORD all-ASCII-printable        : {_pw.isascii() and _pw.isprintable()}\n")
        out.write(f"SSL enabled   : {'ssl' in db.get('OPTIONS', {})}\n")
        out.write(f"DATABASE_URL set in env : {bool(os.environ.get('DATABASE_URL'))}\n")
        out.write(f"DB_PASSWORD set in env  : {bool(os.environ.get('DB_PASSWORD'))}\n")
        return HttpResponse(_wrap(out.getvalue()), content_type='text/html')

    out.write('== migrate ==\n')
    try:
        call_command('migrate', '--noinput', stdout=out, stderr=out)
    except Exception as exc:  # surface DB / connection errors in the response
        out.write(f'\nMIGRATE ERROR: {exc}\n')
        return HttpResponse(_wrap(out.getvalue()), status=500, content_type='text/html')

    User = get_user_model()
    out.write('\n== administrator ==\n')
    if User.objects.filter(is_superuser=True).exists():
        out.write('An administrator already exists — skipping.\n')
    else:
        username = request.GET.get('username') or os.environ.get('ADMIN_USERNAME') or 'admin'
        password = request.GET.get('password') or os.environ.get('ADMIN_PASSWORD')
        generated = False
        if not password:
            password = secrets.token_urlsafe(9)
            generated = True
        admin = User(
            username=username, role=User.Role.ADMIN,
            is_staff=True, is_superuser=True,
            email=os.environ.get('ADMIN_EMAIL', ''),
        )
        admin.set_password(password)
        admin.save()
        out.write(f'Created administrator "{username}".\n')
        if generated:
            out.write(f'GENERATED PASSWORD (copy it now — shown only once):\n    {password}\n')

    out.write('\nDone. Sign in at /staff/login/.\n')
    return HttpResponse(_wrap(out.getvalue()), content_type='text/html')


def _wrap(text):
    return (
        '<html><body style="font-family:ui-monospace,monospace;background:#0b1525;'
        'color:#8fe3b0;padding:2rem;line-height:1.5"><pre>' + text + '</pre></body></html>'
    )


# --- Public ----------------------------------------------------------------
class LandingView(TemplateView):
    """Public marketing / landing page. No authentication required."""

    template_name = 'landing.html'

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Stay graceful if the database isn't initialised yet (no tables) — the
        # public page should never 500 just because /setup/ hasn't run.
        try:
            ctx['lawyer_count'] = LawyerProfile.objects.count()
            ctx['featured_lawyers'] = list(LawyerProfile.objects.select_related('user')[:3])
        except Exception:
            ctx['lawyer_count'] = 0
            ctx['featured_lawyers'] = []
        return ctx


# --- Authentication --------------------------------------------------------
class SignUpView(CreateView):
    """Public self-registration for clients; logs the new user straight in."""

    form_class = SignUpForm
    template_name = 'accounts/signup.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, f'Welcome to CaseHarbor, {user.first_name}!')
        return redirect('dashboard')


class PortalLoginView(LoginView):
    """Client / lawyer sign-in. Admins are redirected to the staff portal."""

    template_name = 'accounts/login_portal.html'
    authentication_form = PortalAuthForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        user = form.get_user()
        if user.is_admin:
            form.add_error(None, 'Administrators must sign in through the staff portal.')
            return self.form_invalid(form)
        return super().form_valid(form)


class AdminLoginView(LoginView):
    """Separate, unadvertised credential window for administrators."""

    template_name = 'accounts/login_admin.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        user = form.get_user()
        if not user.is_admin:
            form.add_error(None, 'This portal is for administrators only.')
            return self.form_invalid(form)
        return super().form_valid(form)


# --- Dashboard -------------------------------------------------------------
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


class ProfileView(LoginRequiredMixin, TemplateView):
    """Self-service 'My profile' — edit your own details. Clients and lawyers
    edit their profile (incl. role-specific fields); admins edit basic account
    details. Password changes happen via the separate change-password flow."""

    template_name = 'accounts/profile.html'

    def _form(self, data=None):
        user = self.request.user
        if user.is_lawyer and hasattr(user, 'lawyer_profile'):
            return LawyerProfileEditForm(data, instance=user.lawyer_profile)
        if user.is_client and hasattr(user, 'client_profile'):
            return ClientProfileEditForm(data, instance=user.client_profile)
        return AccountForm(data, instance=user)

    def get(self, request, *args, **kwargs):
        return self.render_to_response(self.get_context_data(form=self._form()))

    def post(self, request, *args, **kwargs):
        form = self._form(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('profile')
        return self.render_to_response(self.get_context_data(form=form))


class LawyerDirectoryView(LoginRequiredMixin, ListView):
    """Read-only 'our lawyers' directory visible to every signed-in user."""

    model = LawyerProfile
    template_name = 'accounts/lawyer_directory.html'
    context_object_name = 'lawyers'

    def get_queryset(self):
        return LawyerProfile.objects.select_related('user')


# --- Lawyers (admin management) --------------------------------------------
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


# --- Clients (admin management) --------------------------------------------
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
