from django import forms


class ContactForm(forms.Form):
    """Form for contacting us."""
    # Name of the sender
    name = forms.CharField(max_length=50)
    # Email of the sender
    email = forms.EmailField()
    # Subject for the request
    subject = forms.CharField(max_length=100)
    # Body text for the request
    body = forms.CharField(widget=forms.Textarea)