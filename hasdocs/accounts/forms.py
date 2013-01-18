from django import forms

from hasdocs.accounts.models import Plan, User


class ProfileUpdateForm(forms.ModelForm):
    """Form for updating user settings."""
    class Meta:
        model = User
        fields = ('name', 'email', 'blog', 'company', 'location')


class BillingUpdateForm(forms.ModelForm):
    """Form for updating billing information."""
    class Meta:
        model = User
        fields = ('plan', )

    def __init__(self, *args, **kwargs):
        super(BillingUpdateForm, self).__init__(*args, **kwargs)
        self.fields['plan'].queryset = Plan.objects.filter(
            business=(kwargs['instance'].is_organization()))


class ConnectionsUpdateForm(forms.ModelForm):
    """Form for setting Heroku api key."""
    class Meta:
        model = User
        fields = ('github_access_token', 'heroku_api_key')
