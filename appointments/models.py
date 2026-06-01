from django.db import models
from django.urls import reverse


class AppointmentQuerySet(models.QuerySet):
    def for_user(self, user):
        """Scope appointments to what ``user`` is allowed to see."""
        if user.is_admin:
            return self
        if user.is_lawyer:
            return self.filter(lawyer__user=user)
        if user.is_client:
            return self.filter(client__user=user)
        return self.none()


class Appointment(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = 'SCHEDULED', 'Scheduled'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    title = models.CharField(max_length=200)
    scheduled_for = models.DateTimeField()
    location = models.CharField(max_length=200, blank=True)

    lawyer = models.ForeignKey(
        'accounts.LawyerProfile', on_delete=models.CASCADE, related_name='appointments',
    )
    client = models.ForeignKey(
        'accounts.ClientProfile', on_delete=models.CASCADE, related_name='appointments',
    )
    case = models.ForeignKey(
        'cases.Case', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='appointments',
    )

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.SCHEDULED)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = AppointmentQuerySet.as_manager()

    class Meta:
        ordering = ['scheduled_for']

    def __str__(self):
        return f'{self.title} ({self.scheduled_for:%Y-%m-%d %H:%M})'

    def get_absolute_url(self):
        return reverse('appointment_detail', args=[self.pk])

    def status_badge(self):
        return {
            self.Status.SCHEDULED: 'primary',
            self.Status.COMPLETED: 'success',
            self.Status.CANCELLED: 'secondary',
        }.get(self.status, 'secondary')
