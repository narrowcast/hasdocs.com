from django import forms
from django.contrib import messages
from django.contrib.auth.models import User
from django.forms.fields import CharField, EmailField
from django.forms.widgets import PasswordInput

from hasdocs.accounts.models import Plan, UserProfile, UserType


class SignupForm(forms.ModelForm):
    """Form for signing up."""
    class Meta:
        model = User
        fields = ('username', 'email', 'password')
        widgets = {'password': PasswordInput}
    
    def save(self, commit=True):
        """Creates a new user."""
        user = super(SignupForm, self).save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user
        
class ProfileUpdateForm(forms.ModelForm):
    """Form for updating user settings."""
    name = CharField(required=False)
    email = EmailField(required=False)
    
    class Meta:
        model = UserProfile
        fields = ('name', 'email', 'url', 'company', 'location')
        
    def __init__(self, *args, **kwargs):
        """Initializes the fields from values in the User model."""
        super(ProfileUpdateForm, self).__init__(*args, **kwargs)
        self.fields['name'].initial = self.instance.user.first_name
        self.fields['email'].initial = self.instance.user.email
        
    def save(self, commit=True):
        """Saves the name and email fields into the user model."""
        profile = super(ProfileUpdateForm, self).save(commit=False)
        name = self.cleaned_data['name']
        email = self.cleaned_data['email']
        profile.user.first_name = name
        profile.user.email = email
        if commit:
            profile.user.save()
        return profile

class BillingUpdateForm(forms.ModelForm):
    """Form for updating billing information."""
    class Meta:
        model = UserProfile
        fields = ('plan', )
    
    def __init__(self, *args, **kwargs):
        super(BillingUpdateForm, self).__init__(*args, **kwargs)
        user_type = kwargs['instance'].user_type
        organization = UserType.objects.get(name='Organization')
        self.fields['plan'].queryset = Plan.objects.filter(
            business=(user_type==organization))
    
class ConnectionsUpdateForm(forms.ModelForm):
    """Form for setting Heroku api key."""
    class Meta:
        model = UserProfile
        fields = ('github_access_token', 'heroku_api_key')
        
class OrganizationsUpdateForm(forms.ModelForm):
    """Form for updating a user's organizations."""
    class Meta:
        model = UserProfile
        fields = ('organizations', )
        
    def __init__(self, *args, **kwargs):
        super(OrganizationsUpdateForm, self).__init__(*args, **kwargs)
        organization = UserType.objects.get(name='Organization')
        self.fields['organizations'].queryset = User.objects.filter(
            userprofile__user_type=organization)