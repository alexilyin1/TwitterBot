from django import forms


class StreamForm(forms.Form):
    topic = forms.CharField(max_length=20, label='', required=True,
                            widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Coronavirus'}),
                            error_messages={'required': 'Please enter a topic'})

    stream_time = forms.IntegerField(max_value=15, label='', required=True,
                                     widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '5 (max 15 minutes)'}),
                                     error_messages={'required': 'Please enter a streaming time'})

    email = forms.CharField(max_length=50, label='', required=True,
                            widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'xyz@example.com'}),
                            error_messages={'required': 'Please enter an email'})


class LoginForm(forms.Form):
    email = forms.CharField(max_length=50, label='', required=True,
                            widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'}),
                            error_messages={'required': 'Please enter an email'})
    uuid = forms.UUIDField(label='', required=True,
                           widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your unique ID'}),
                           error_messages={'required': 'Please enter a uuid'})


class PurgeForm(forms.Form):
    email = forms.CharField(max_length=50, label='', required=True,
                            widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'}),
                            error_messages={'required': 'Please enter an email'})

