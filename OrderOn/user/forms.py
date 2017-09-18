from django.contrib.auth.forms import UserCreationForm, UserChangeForm, ReadOnlyPasswordHashField
from .models import AbstractUser
from django import forms


class AbstractUserCreationForm(forms.ModelForm):
    """
    A form that creates a user, with no privileges,
    from the given email and password.
    """
    password1 = forms.CharField(
        label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(
        label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = AbstractUser
        fields = ('username', 'sex')

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super(AbstractUserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class AbstractUserChangeForm(forms.ModelForm):
    """
    A form for updating users. Includes all the fields on
    the user, but replace the password field with admin's
    password hash display field.
    """
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = AbstractUser
        fields = '__all__'

    def clean_password(self, *args, **kargs):
        return self.initial['password']
