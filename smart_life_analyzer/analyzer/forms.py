from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import DailyEntry, UserProfile

class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Username or Email'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Password'
    }))

class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Email'
    }))
    first_name = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'First Name'
    }))
    last_name = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Last Name'
    }))
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirm Password'})
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email

class DailyEntryForm(forms.ModelForm):
    class Meta:
        model = DailyEntry
        fields = ['date', 'sleep_hours', 'work_hours', 'exercise_minutes', 'water_intake', 
                 'expense', 'income', 'mood', 'stress_level', 'energy_level', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'sleep_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5', 'min': '0', 'max': '24'}),
            'work_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5', 'min': '0', 'max': '24'}),
            'exercise_minutes': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '1440'}),
            'water_intake': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '20'}),
            'expense': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'income': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'mood': forms.Select(attrs={'class': 'form-control'}),
            'stress_level': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '10'}),
            'energy_level': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '10'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['exercise_minutes'].required = False
        self.fields['water_intake'].required = False
        self.fields['income'].required = False
        self.fields['stress_level'].required = False
        self.fields['energy_level'].required = False

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['phone', 'age', 'date_of_birth', 'profile_image']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'age': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '120'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'profile_image': forms.FileInput(attrs={'class': 'form-control'}),
        }

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

class PasswordChangeForm(forms.Form):
    current_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    new_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    
    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if new_password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        
        return cleaned_data