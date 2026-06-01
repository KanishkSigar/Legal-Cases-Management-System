from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied

from accounts.models import User


class RoleRequiredMixin(LoginRequiredMixin):
    """Require login plus one of ``allowed_roles`` (admins always pass)."""

    allowed_roles = ()

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        user = request.user
        if user.is_admin or user.role in self.allowed_roles:
            return super().dispatch(request, *args, **kwargs)
        raise PermissionDenied('You do not have permission to access this page.')


class AdminRequiredMixin(RoleRequiredMixin):
    """Only admins / superusers pass."""

    allowed_roles = ()


class StaffRequiredMixin(RoleRequiredMixin):
    """Admins and lawyers (the firm's staff)."""

    allowed_roles = (User.Role.LAWYER,)
