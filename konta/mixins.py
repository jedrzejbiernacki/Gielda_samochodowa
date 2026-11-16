from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages

class SprzedawcaWymaganyMixin(AccessMixin):
    """
    Mixin weryfikujący, czy użytkownik jest zalogowany, ma rolę sprzedawcy (SPRZEDAWCA lub KOMIS)
    oraz czy jego konto nie zostało zablokowane przez administratora.
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        if request.user.zablokowany:
            messages.error(request, 'Twoje konto zostało zablokowane przez administratora.')
            raise PermissionDenied('Konto zablokowane.')

        if not request.user.czy_sprzedawca():
            messages.error(request, 'Ta operacja wymaga konta sprzedawcy lub komisu.')
            raise PermissionDenied('Brak uprawnień sprzedawcy.')

        return super().dispatch(request, *args, **kwargs)
