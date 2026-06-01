from django import forms

from .models import Appointment


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = (
            'title', 'scheduled_for', 'location',
            'lawyer', 'client', 'case', 'status', 'notes',
        )
        widgets = {
            'scheduled_for': forms.DateTimeInput(
                attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M',
            ),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        # HTML datetime-local inputs need this exact format to round-trip.
        self.fields['scheduled_for'].input_formats = ['%Y-%m-%dT%H:%M']
        # A lawyer can only schedule appointments for themselves.
        if user is not None and user.is_lawyer:
            self.fields['lawyer'].queryset = self.fields['lawyer'].queryset.filter(user=user)
            self.fields['lawyer'].initial = user.lawyer_profile
            self.fields['lawyer'].disabled = True
