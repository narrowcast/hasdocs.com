from django import forms
from django.contrib.auth.models import User
from django.forms.widgets import PasswordInput

from hasdocs.accounts.models import UserProfile


class SignupForm(forms.ModelForm):
    """Form for signing up."""
    class Meta:
        model = User
        fields = ('username', 'email', 'password')
        widgets = {'password': PasswordInput}
        
class UserUpdateForm(forms.ModelForm):
    """Form for updating user settings."""
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')

class HerokuConnectForm(forms.ModelForm):
    """Form for setting Heroku api key."""
    class Meta:
        model = UserProfile
        fields = ('heroku_api_key', )