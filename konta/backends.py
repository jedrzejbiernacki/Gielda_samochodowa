from django.contrib.auth.backends import ModelBackend

class KontaAuthBackend(ModelBackend):
    """
    Backend uwierzytelniania uniemożliwiający logowanie użytkownikom zablokowanym przez administratora.
    """
    def user_can_authenticate(self, user):
        is_active = super().user_can_authenticate(user)
        return is_active and not getattr(user, 'zablokowany', False)
