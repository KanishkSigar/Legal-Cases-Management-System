from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import ClientProfile, LawyerProfile, User


class _PersonForm(UserCreationForm):
    """Shared base for creating a staff/client User account."""

    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=False)
    phone = forms.CharField(max_length=30, required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'phone')

    role = User.Role.CLIENT

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = self.role
        if commit:
            user.save()
        return user


class SignUpForm(UserCreationForm):
    """Public self-registration. Always creates a CLIENT account — the role is
    fixed server-side so it can never be escalated from form input."""

    first_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'placeholder': 'First name'}))
    last_name = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={'placeholder': 'Last name'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'you@example.com'}))

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('first_name', 'last_name', 'email', 'username')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.CLIENT  # never trust a role from the request
        if commit:
            user.save()
            ClientProfile.objects.get_or_create(user=user)
        return user


class LawyerForm(_PersonForm):
    role = User.Role.LAWYER
    specialization = forms.CharField(max_length=120, required=False)
    bar_number = forms.CharField(max_length=60, required=False)
    bio = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)

    def save(self, commit=True):
        user = super().save(commit=commit)
        LawyerProfile.objects.update_or_create(
            user=user,
            defaults={
                'specialization': self.cleaned_data.get('specialization', ''),
                'bar_number': self.cleaned_data.get('bar_number', ''),
                'bio': self.cleaned_data.get('bio', ''),
            },
        )
        return user


class ClientForm(_PersonForm):
    role = User.Role.CLIENT
    address = forms.CharField(max_length=255, required=False)
    company = forms.CharField(max_length=120, required=False)

    def save(self, commit=True):
        user = super().save(commit=commit)
        ClientProfile.objects.update_or_create(
            user=user,
            defaults={
                'address': self.cleaned_data.get('address', ''),
                'company': self.cleaned_data.get('company', ''),
            },
        )
        return user


class LawyerProfileEditForm(forms.ModelForm):
    """Edit an existing lawyer's name/contact + profile (no password)."""

    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=False)
    phone = forms.CharField(max_length=30, required=False)

    class Meta:
        model = LawyerProfile
        fields = ('specialization', 'bar_number', 'bio')
        widgets = {'bio': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user = self.instance.user
        self.fields['first_name'].initial = user.first_name
        self.fields['last_name'].initial = user.last_name
        self.fields['email'].initial = user.email
        self.fields['phone'].initial = user.phone

    def save(self, commit=True):
        profile = super().save(commit=commit)
        user = profile.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        user.phone = self.cleaned_data['phone']
        if commit:
            user.save()
        return profile


class ClientProfileEditForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=False)
    phone = forms.CharField(max_length=30, required=False)

    class Meta:
        model = ClientProfile
        fields = ('address', 'company')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user = self.instance.user
        self.fields['first_name'].initial = user.first_name
        self.fields['last_name'].initial = user.last_name
        self.fields['email'].initial = user.email
        self.fields['phone'].initial = user.phone

    def save(self, commit=True):
        profile = super().save(commit=commit)
        user = profile.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        user.phone = self.cleaned_data['phone']
        if commit:
            user.save()
        return profile
