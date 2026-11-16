from django.db import transaction
from django.core.exceptions import PermissionDenied, ValidationError
from ogloszenia.models import Ogloszenie, StatusOgloszenia
from wiadomosci.services import SerwisPowiadomien
from .models import Zamowienie, Ocena, StatusZamowienia
from .exceptions import NiedozwolonaOperacjaZamowienia

class SerwisZamowien:
    """
    Warstwa logiki biznesowej realizująca operacje na zamówieniach i ogłoszeniach
    w ramach transakcji bazodanowych z blokadą wierszy (SELECT ... FOR UPDATE).
    """

    @classmethod
    def zloz_zamowienie(cls, kupujacy, ogloszenie_id: int, uwagi: str = "") -> Zamowienie:
        """
        Złożenie rezerwacji pojazdu przez kupującego (PU-07).
        Transakcja atomowa z blokadą wiersza ogłoszenia zapobiegająca race condition.
        """
        with transaction.atomic():
            ogloszenie = Ogloszenie.objects.select_for_update().select_related('sprzedawca').get(id=ogloszenie_id)

            if ogloszenie.sprzedawca_id == kupujacy.id:
                raise PermissionDenied("Nie możesz złożyć zamówienia na własne ogłoszenie.")

            if not ogloszenie.czy_dostepne():
                raise NiedozwolonaOperacjaZamowienia(
                    "To ogłoszenie nie jest obecnie dostępne do rezerwacji (zostało już zarezerwowane, sprzedane lub wygasło)."
                )

            zamowienie = Zamowienie.objects.create(
                ogloszenie=ogloszenie,
                kupujacy=kupujacy,
                cena=ogloszenie.cena,
                uwagi_kupujacego=uwagi or "",
                status=StatusZamowienia.ZLOZONE
            )
            ogloszenie.zarezerwuj()

            SerwisPowiadomien.powiadom_o_nowym_zamowieniu(zamowienie)

            return zamowienie

    @classmethod
    def akceptuj(cls, sprzedawca, zamowienie_id: int) -> Zamowienie:
        """
        Akceptacja rezerwacji przez sprzedawcę (PU-12).
        Ogłoszenie staje się SPRZEDANE, a zamówienie ZAAKCEPTOWANE.
        """
        with transaction.atomic():
            zamowienie = Zamowienie.objects.select_for_update().select_related('ogloszenie', 'kupujacy').get(id=zamowienie_id)
            ogloszenie = Ogloszenie.objects.select_for_update().get(id=zamowienie.ogloszenie_id)

            if ogloszenie.sprzedawca_id != sprzedawca.id and not sprzedawca.is_staff:
                raise PermissionDenied("Tylko właściciel ogłoszenia może zaakceptować zamówienie.")

            zamowienie.akceptuj()
            ogloszenie.oznacz_jako_sprzedane()

            SerwisPowiadomien.powiadom_o_akceptacji(zamowienie)
            return zamowienie

    @classmethod
    def odrzuc(cls, sprzedawca, zamowienie_id: int, uzasadnienie: str = "") -> Zamowienie:
        """
        Odrzucenie rezerwacji przez sprzedawcę (PU-12).
        Ogłoszenie powraca do stanu AKTYWNE, zamówienie staje się ODRZUCONE.
        """
        with transaction.atomic():
            zamowienie = Zamowienie.objects.select_for_update().select_related('ogloszenie', 'kupujacy').get(id=zamowienie_id)
            ogloszenie = Ogloszenie.objects.select_for_update().get(id=zamowienie.ogloszenie_id)

            if ogloszenie.sprzedawca_id != sprzedawca.id and not sprzedawca.is_staff:
                raise PermissionDenied("Tylko właściciel ogłoszenia może odrzucić zamówienie.")

            zamowienie.odrzuc(uzasadnienie)
            ogloszenie.zwolnij_rezerwacje()

            SerwisPowiadomien.powiadom_o_odrzuceniu(zamowienie, uzasadnienie)
            return zamowienie

    @classmethod
    def anuluj(cls, kupujacy, zamowienie_id: int) -> Zamowienie:
        """
        Anulowanie rezerwacji przez kupującego przed podjęciem decyzji przez sprzedawcę.
        Ogłoszenie powraca do stanu AKTYWNE.
        """
        with transaction.atomic():
            zamowienie = Zamowienie.objects.select_for_update().select_related('ogloszenie').get(id=zamowienie_id)
            ogloszenie = Ogloszenie.objects.select_for_update().get(id=zamowienie.ogloszenie_id)

            if zamowienie.kupujacy_id != kupujacy.id and not kupujacy.is_staff:
                raise PermissionDenied("Możesz anulować jedynie własne zamówienie.")

            zamowienie.anuluj()
            ogloszenie.zwolnij_rezerwacje()
            return zamowienie

    @classmethod
    def potwierdz_odbior(cls, kupujacy, zamowienie_id: int) -> Zamowienie:
        """
        Potwierdzenie fizycznego odbioru pojazdu i sfinalizowania zakupu przez kupującego (PU-08).
        Przejście zamówienia: ZAAKCEPTOWANE -> ZAKONCZONE.
        """
        with transaction.atomic():
            zamowienie = Zamowienie.objects.select_for_update().get(id=zamowienie_id)

            if zamowienie.kupujacy_id != kupujacy.id and not kupujacy.is_staff:
                raise PermissionDenied("Tylko kupujący może potwierdzić odbiór samochodu.")

            zamowienie.zakoncz()
            return zamowienie

    @classmethod
    def wystaw_ocene(cls, kupujacy, zamowienie_id: int, liczba_gwiazdek: int, komentarz: str) -> Ocena:
        """
        Wystawienie oceny sprzedawcy po zakończonej transakcji (PU-09).
        """
        with transaction.atomic():
            zamowienie = Zamowienie.objects.select_for_update().select_related('ogloszenie').get(id=zamowienie_id)

            if zamowienie.kupujacy_id != kupujacy.id and not kupujacy.is_staff:
                raise PermissionDenied("Tylko kupujący z tego zamówienia może wystawić ocenę.")

            if not zamowienie.czy_mozna_ocenic():
                raise NiedozwolonaOperacjaZamowienia(
                    "Ocena może być wystawiona wyłącznie dla zakończonego zamówienia i tylko raz."
                )

            ocena = Ocena.objects.create(
                zamowienie=zamowienie,
                oceniajacy=kupujacy,
                oceniany=zamowienie.ogloszenie.sprzedawca,
                liczba_gwiazdek=liczba_gwiazdek,
                komentarz=komentarz or ""
            )
            return ocena
