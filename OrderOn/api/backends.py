from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.tokens import default_token_generator
from django.db.models import Q
from django.utils.http import base36_to_int
from django.contrib.auth import get_user_model

User = get_user_model()


class CaseInsensitiveBackend(ModelBackend):
    def authenticate(self, **kwargs):
        if kwargs:
            if kwargs.get('username', None):
                kwargs['username'] = kwargs.get('username', None).lower()
            if kwargs.get('email', None):
                kwargs['email'] = kwargs.get('email', None).lower()

            username = kwargs.pop('username', None)
            if username:
                username_or_email = Q(username=username) | Q(email=username)
                password = kwargs.pop('password', None)
                try:
                    user = User.objects.get(username_or_email)
                except User.DoesNotExist:
                    pass
                else:
                    if user.check_password(password):
                        return user
            else:
                if 'uidb36' not in kwargs:
                    return
                kwargs['id'] = base36_to_int(kwargs.pop('uidb36'))
                token = kwargs.pop('token')
                try:
                    user = User.objects.get(**kwargs)
                except User.DoesNotExist:
                    pass
                else:
                    if default_token_generator.check_token(user, token):
                        return user
