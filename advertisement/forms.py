from django import forms
from django.forms import ModelForm

from advertisement.models import Signal, Signaler, Expert
from advertisement.validators import phone_validator, string_check
from django.contrib.auth.models import User


class SearchForm(forms.Form):
    title = forms.CharField(label='Signal Title', max_length=80,
                            widget=forms.TextInput(
                                attrs={'class': 'form-control', 'placeholder': 'Enter the signal\'s title'}))


class AddSignalForm(ModelForm):
    class Meta:
        model = Signal
        exclude = ['signaler']

    def __init__(self, *args, **kwargs):
        super(AddSignalForm, self).__init__(*args, **kwargs)
        self.fields['title'].widget.attrs['placeholder'] = 'title'
        self.fields['profit'].widget.attrs['placeholder'] = 'profit'
        self.fields['start_date'].widget.attrs['placeholder'] = 'start_date'
        self.fields['close_date'].widget.attrs['placeholder'] = 'close_date'
        self.fields['expected_return'].widget.attrs['placeholder'] = 'expected_return'
        self.fields['expected_risk'].widget.attrs['placeholder'] = 'expected_risk'
        self.fields['title'].widget.attrs['class'] = 'form-control '
        self.fields['profit'].widget.attrs['class'] = 'form-control '
        self.fields['start_date'].widget.attrs['class'] = 'form-control '
        self.fields['close_date'].widget.attrs['class'] = 'form-control '
        self.fields['expected_return'].widget.attrs['class'] = 'form-control '
        self.fields['expected_risk'].widget.attrs['class'] = 'form-control '

    def clean(self):
        data = self.cleaned_data
        # if phone_validator(data['phone'])[0] is False:
        #     self._errors['phone'] = phone_validator(data['phone'])[1]
        return data

    def save(self, commit=True):
        instance = super(AddSignalForm, self).save(commit=False)
        the_user = Signaler.objects.filter(user=self.user)
        if len(the_user) > 0:
            instance.advertiser = Signaler.objects.filter(user=self.user)[0]
        else:
            instance.advertiser = self.fields['expert']
        if commit:
            instance.save()
        return instance


class AddExpertForm(ModelForm):
    class Meta:
        model = Expert
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(AddExpertForm, self).__init__(*args, **kwargs)
        self.fields['display_name'].widget.attrs['placeholder'] = 'display_name'
        self.fields['first_name'].widget.attrs['placeholder'] = 'first_name'
        self.fields['last_name'].widget.attrs['placeholder'] = 'last_name'
        self.fields['website'].widget.attrs['placeholder'] = 'website'
        self.fields['display_name'].widget.attrs['class'] = 'form-control '
        self.fields['first_name'].widget.attrs['class'] = 'form-control '
        self.fields['last_name'].widget.attrs['class'] = 'form-control '
        self.fields['website'].widget.attrs['class'] = 'form-control '

    def clean(self):
        data = self.cleaned_data
        return data

    def save(self, commit=True):
        instance = super(AddExpertForm, self).save(commit=False)
        if commit:
            instance.save()
        return instance


class AddSignalerForm(ModelForm):
    username = forms.CharField(max_length=20)
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = Signaler
        exclude = ['user']

    def __init__(self, *args, **kwargs):
        super(AddSignalerForm, self).__init__(*args, **kwargs)
        self.fields['first_name'].widget.attrs['placeholder'] = 'first_name'
        self.fields['last_name'].widget.attrs['placeholder'] = 'last_name'
        self.fields['phone'].widget.attrs['placeholder'] = 'phone'
        self.fields['email'].widget.attrs['placeholder'] = 'email'
        self.fields['sex'].widget.attrs['placeholder'] = 'sex'
        self.fields['age'].widget.attrs['placeholder'] = 'age'
        self.fields['first_name'].widget.attrs['class'] = 'form-control '
        self.fields['last_name'].widget.attrs['class'] = 'form-control '
        self.fields['phone'].widget.attrs['class'] = 'form-control '
        self.fields['email'].widget.attrs['class'] = 'form-control '
        self.fields['sex'].widget.attrs['class'] = 'form-control '
        self.fields['age'].widget.attrs['class'] = 'form-control '

    def clean(self):
        data = self.cleaned_data
        if phone_validator(data['phone'])[0] is False:
            self._errors['phone'] = phone_validator(data['phone'])[1]
        return data

    def save(self, commit=True):
        instance = super(AddSignalerForm, self).save(commit=False)
        user_instance = User.objects.create_user(username=self.cleaned_data['username'],
                                                 password=self.cleaned_data['password'])
        user_instance.save()
        instance.user = user_instance
        if commit:
            instance.save()
        return instance


class LoginForm(forms.Form):
    username = forms.CharField(max_length=20)
    password = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['placeholder'] = 'username'
        self.fields['username'].widget.attrs['class'] = 'form-control '

        self.fields['password'].widget.attrs['placeholder'] = '*********'
        self.fields['password'].widget.attrs['class'] = 'form-control '

    def clean(self):
        data = self.cleaned_data
        return data


class ResetPassForm(forms.Form):
    email = forms.EmailField()

    def __init__(self, *args, **kwargs):
        super(ResetPassForm, self).__init__(*args, **kwargs)
        self.fields['email'].widget.attrs['placeholder'] = 'email'
        self.fields['email'].widget.attrs['class'] = 'form-control '


class SubmitPassword(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput())
    confirm_password = forms.CharField(widget=forms.PasswordInput())

    def __init__(self, *args, **kwargs):
        super(SubmitPassword, self).__init__(*args, **kwargs)
        self.fields['password'].widget.attrs['placeholder'] = 'password'
        self.fields['password'].widget.attrs['class'] = 'form-control '

        self.fields['confirm_password'].widget.attrs['placeholder'] = 'confirm_password'
        self.fields['confirm_password'].widget.attrs['class'] = 'form-control '

    def clean(self):
        cleaned_data = super(SubmitPassword, self).clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password != confirm_password:
            self._errors['password'] = 'passwords does not match.'

        return cleaned_data
