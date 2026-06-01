from django import forms

from .models import Case, CaseNote


class CaseForm(forms.ModelForm):
    class Meta:
        model = Case
        fields = (
            'case_number', 'title', 'description', 'case_type', 'status',
            'client', 'lawyer', 'opened_date', 'closed_date',
        )
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'opened_date': forms.DateInput(attrs={'type': 'date'}),
            'closed_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        # A lawyer creating/editing a case can only assign it to themselves.
        if user is not None and user.is_lawyer:
            self.fields['lawyer'].queryset = self.fields['lawyer'].queryset.filter(user=user)
            self.fields['lawyer'].initial = user.lawyer_profile
            self.fields['lawyer'].disabled = True


class CaseStatusForm(forms.ModelForm):
    class Meta:
        model = Case
        fields = ('status', 'closed_date')
        widgets = {'closed_date': forms.DateInput(attrs={'type': 'date'})}


class CaseNoteForm(forms.ModelForm):
    class Meta:
        model = CaseNote
        fields = ('text',)
        widgets = {'text': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Add an update…'})}
