from django.conf import settings
from django.db import models
from django.urls import reverse


class CaseQuerySet(models.QuerySet):
    def for_user(self, user):
        """Scope cases to what ``user`` is allowed to see."""
        if user.is_admin:
            return self
        if user.is_lawyer:
            return self.filter(lawyer__user=user)
        if user.is_client:
            return self.filter(client__user=user)
        return self.none()


class Case(models.Model):
    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Open'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        PENDING = 'PENDING', 'Pending'
        CLOSED = 'CLOSED', 'Closed'
        WON = 'WON', 'Won'
        LOST = 'LOST', 'Lost'

    class Type(models.TextChoices):
        CIVIL = 'CIVIL', 'Civil'
        CRIMINAL = 'CRIMINAL', 'Criminal'
        FAMILY = 'FAMILY', 'Family'
        CORPORATE = 'CORPORATE', 'Corporate'
        PROPERTY = 'PROPERTY', 'Property'
        OTHER = 'OTHER', 'Other'

    case_number = models.CharField(max_length=40, unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    case_type = models.CharField(max_length=20, choices=Type.choices, default=Type.CIVIL)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)

    client = models.ForeignKey(
        'accounts.ClientProfile', on_delete=models.PROTECT, related_name='cases',
    )
    lawyer = models.ForeignKey(
        'accounts.LawyerProfile', on_delete=models.PROTECT, related_name='cases',
    )

    opened_date = models.DateField()
    closed_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CaseQuerySet.as_manager()

    class Meta:
        ordering = ['-opened_date', '-created_at']

    def __str__(self):
        return f'{self.case_number} — {self.title}'

    def get_absolute_url(self):
        return reverse('case_detail', args=[self.pk])

    @property
    def is_closed(self):
        return self.status in {self.Status.CLOSED, self.Status.WON, self.Status.LOST}

    def status_badge(self):
        """Bootstrap contextual class for the status badge."""
        return {
            self.Status.OPEN: 'primary',
            self.Status.IN_PROGRESS: 'info',
            self.Status.PENDING: 'warning',
            self.Status.CLOSED: 'secondary',
            self.Status.WON: 'success',
            self.Status.LOST: 'danger',
        }.get(self.status, 'secondary')


class CaseNote(models.Model):
    """A timeline entry / update on a case."""

    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='notes')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Note on {self.case.case_number} @ {self.created_at:%Y-%m-%d}'
