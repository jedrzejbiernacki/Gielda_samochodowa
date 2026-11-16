from django.utils import timezone
from konta.models import RolaUzytkownika
from ogloszenia.models import Ogloszenie, StatusOgloszenia
from .models import Cennik, OplataZaOgloszenie, TypOplaty

class SprawdzaczLimitu:
    """Klasa usługi weryfikująca limity liczby aktywnych ogłoszeń dla danego użytkownika."""

    def __init__(self, uzytkownik):
        self.uzytkownik = uzytkownik

    def sprawdz(self) -> tuple[bool, int, int]:
        """
        Zwraca (czy_w_limicie, aktualna_liczba, limit).
        Limit to suma bazowego limitu z cennika oraz opłaconych dodatkowych slotów.
        """
        cennik = Cennik.load()

        if self.uzytkownik.rola == RolaUzytkownika.KOMIS:
            limit_bazowy = cennik.limit_ogloszen_komis
        else:
            limit_bazowy = cennik.limit_ogloszen_prywatny

        dodatkowe_oplaty = OplataZaOgloszenie.objects.filter(
            uzytkownik=self.uzytkownik,
            oplacone=True,
            typ_oplaty=TypOplaty.DODATKOWE_OGLOSZENIE
        ).count()

        limit = limit_bazowy + dodatkowe_oplaty

        aktualna_liczba = Ogloszenie.objects.filter(
            sprzedawca=self.uzytkownik,
            status__in=[StatusOgloszenia.AKTYWNE, StatusOgloszenia.ZAREZERWOWANE]
        ).count()

        czy_w_limicie = aktualna_liczba < limit
        return (czy_w_limicie, aktualna_liczba, limit)


class SymulacjaOplaty:
    """Klasa symulująca proces realizacji płatności elektronicznej."""

    def przetworz_oplate(self, oplata_id: int):
        """Oznacza wskazaną opłatę jako opłaconą z bieżącą datą."""
        oplata = OplataZaOgloszenie.objects.get(pk=oplata_id)
        oplata.oplacone = True
        oplata.data_oplacenia = timezone.now()
        oplata.save(update_fields=['oplacone', 'data_oplacenia'])
        return oplata
