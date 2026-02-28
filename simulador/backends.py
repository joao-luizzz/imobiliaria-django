from django.contrib.auth.models import User

class EmailBackend:
    def authenticate(self, request, username=None, password=None, **kwargs):
        # username field may contain an email
        if username and '@' in username:
            try:
                user = User.objects.get(email__iexact=username)
            except User.DoesNotExist:
                return None
            except User.MultipleObjectsReturned:
                return None
        else:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return None
        if user.check_password(password) and user.is_active:
            return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
