import re

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import UserProfile, DailyEntry


# ── Reusable username validator ──────────────────────────────────────

def validate_username_format(username):
    """Validate that username contains only letters, numbers, and underscores."""
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        raise forms.ValidationError(
            'Username can only contain letters, numbers, and underscores.'
        )
    if len(username) < 3:
        raise forms.ValidationError(
            'Username must be at least 3 characters long.'
        )
    if len(username) > 30:
        raise forms.ValidationError(
            'Username must be 30 characters or fewer.'
        )


# ── Login Form ───────────────────────────────────────────────────────

class LoginForm(AuthenticationForm):
    """Custom login form with styled fields."""
    """Login using email OR username."""
    username = forms.CharField(
        label='Email or Username',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter email or username',
            'id': 'login-username',
        })
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password',
            'id': 'login-password',
        })
    )


# ── Signup Form ──────────────────────────────────────────────────────

class SignupForm(UserCreationForm):
    """Custom signup form with username, first name, last name, email, and password."""
    username = forms.CharField(
        max_length=30,
        min_length=3,
        label='Username',
        help_text='Letters, numbers, and underscores only.',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Choose a unique username',
            'id': 'signup-username',
        })
    )
    first_name = forms.CharField(
        max_length=30,
        label='First Name',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your first name',
            'id': 'signup-first-name',
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=False,
        label='Last Name',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your last name',
            'id': 'signup-last-name',
        })
    )
    email = forms.EmailField(
        label='Email Address',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email',
            'id': 'signup-email',
        })
    )
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Create a password',
            'id': 'signup-password',
        })
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your password',
            'id': 'confirm-password',
        })
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def clean_username(self):
        """Validate username format and uniqueness."""
        username = self.cleaned_data.get('username', '').strip()
        validate_username_format(username)
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username

    def clean_email(self):
        """Ensure email is unique."""
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['username']
        user.first_name = self.cleaned_data['first_name'].strip()
        user.last_name = self.cleaned_data.get('last_name', '').strip()
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            # UserProfile is auto-created by the signal, no need to create here
        return user


# ── Daily Entry Form ─────────────────────────────────────────────────

class DailyEntryForm(forms.ModelForm):
    """Form for daily life tracking entries."""
    class Meta:
        model = DailyEntry
        fields = ['date', 'sleep_hours', 'work_hours', 'expense', 'mood', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'id': 'entry-date',
            }),
            'sleep_hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '24',
                'step': '0.5',
                'placeholder': 'e.g., 7.5',
                'id': 'sleep-hours',
            }),
            'work_hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '24',
                'step': '0.5',
                'placeholder': 'e.g., 8',
                'id': 'work-hours',
            }),
            'expense': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01',
                'placeholder': 'e.g., 35.50',
                'id': 'expense',
            }),
            'mood': forms.HiddenInput(attrs={
                'id': 'mood-value',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Any additional notes about your day...',
                'id': 'notes',
            }),
        }


# ── User Profile Form (Settings Page) ───────────────────────────────

class UserProfileForm(forms.ModelForm):
    """Form for updating user profile settings — includes username editing."""
    username = forms.CharField(
        max_length=30,
        min_length=3,
        label='Username',
        help_text='Letters, numbers, and underscores only.',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'settings-username',
        })
    )
    first_name = forms.CharField(
        max_length=30,
        label='First Name',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'settings-first-name',
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=False,
        label='Last Name',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'settings-last-name',
        })
    )
    email = forms.EmailField(
        label='Email Address',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'id': 'settings-email',
        })
    )

    class Meta:
        model = UserProfile
        fields = ['phone', 'date_of_birth', 'address', 'location', 'postal_code', 'gender']
        widgets = {
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'settings-phone',
                'placeholder': 'e.g., +91 9876543210',
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'id': 'settings-dob',
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'settings-address',
                'placeholder': 'Street address',
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'settings-location',
                'placeholder': 'City, State',
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'settings-postal-code',
                'placeholder': 'e.g., 560001',
            }),
            'gender': forms.Select(attrs={
                'class': 'form-control',
                'id': 'settings-gender',
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['username'].initial = self.user.username
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
            self.fields['email'].initial = self.user.email

    def clean_username(self):
        """Validate username format and uniqueness (excluding the current user)."""
        username = self.cleaned_data.get('username', '').strip()
        validate_username_format(username)
        qs = User.objects.filter(username__iexact=username)
        if self.user:
            qs = qs.exclude(pk=self.user.pk)
        if qs.exists():
            raise forms.ValidationError('This username is already taken.')
        return username

    def clean_email(self):
        """Ensure email uniqueness (excluding the current user)."""
        email = self.cleaned_data.get('email', '').strip().lower()
        qs = User.objects.filter(email__iexact=email)
        if self.user:
            qs = qs.exclude(pk=self.user.pk)
        if qs.exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email


# ── Profile Photo Form ───────────────────────────────────────────────

class ProfilePhotoForm(forms.ModelForm):
    """Form for uploading profile photo."""
    class Meta:
        model = UserProfile
        fields = ['profile_photo']
        widgets = {
            'profile_photo': forms.ClearableFileInput(attrs={
                'class': 'form-control photo-input',
                'id': 'profile-photo-input',
                'accept': 'image/*',
            }),
        }


# ── Password Change Form ────────────────────────────────────────────

class PasswordChangeForm(forms.Form):
    """Form for changing user password."""
    current_password = forms.CharField(
        label='Current Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter current password',
            'id': 'current-password',
        })
    )
    new_password = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new password',
            'id': 'new-password',
        })
    )
    confirm_password = forms.CharField(
        label='Confirm New Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password',
            'id': 'confirm-new-password',
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        new_pass = cleaned_data.get('new_password')
        confirm = cleaned_data.get('confirm_password')
        if new_pass and confirm and new_pass != confirm:
            raise forms.ValidationError('Passwords do not match.')
        return cleaned_data


# ── Theme Form ───────────────────────────────────────────────────────

class ThemeForm(forms.ModelForm):
    """Form for selecting app theme."""
    class Meta:
        model = UserProfile
        fields = ['theme']
        widgets = {
            'theme': forms.RadioSelect(attrs={
                'class': 'theme-radio-group',
            }),
        }
