import logging
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)

class SerwisPowiadomien:
    """Klasa usługi odpowiadająca za wysyłkę powiadomień e-mail (SMTP / konsola)."""

    @classmethod
    def wyslij(cls, odbiorca_email: str, temat: str, tresc: str) -> bool:
        """Wysyła wiadomość e-mail do podanego odbiorcy."""
        if not odbiorca_email:
            return False
        try:
            send_mail(
                subject=f"[Giełda Samochodowa] {temat}",
                message=tresc,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[odbiorca_email],
                fail_silently=False,
            )
            return True
        except Exception as e:
            logger.error(f"Błąd wysyłania powiadomienia e-mail do {odbiorca_email}: {e}")
            return False

    @classmethod
    def powiadom_o_nowej_wiadomosci(cls, wiadomosc):
        """Wysyła powiadomienie do odbiorcy o nowej wiadomości w wątku ogłoszenia."""
        temat = f"Nowa wiadomość w sprawie: {wiadomosc.ogloszenie.tytul}"
        tresc = (
            f"Witaj {wiadomosc.odbiorca.nazwa_wyswietlana()},\n\n"
            f"Otrzymałeś nową wiadomość od użytkownika {wiadomosc.nadawca.nazwa_wyswietlana()} "
            f"w sprawie ogłoszenia: „{wiadomosc.ogloszenie.tytul}”.\n\n"
            f"Treść wiadomości:\n{wiadomosc.tresc}\n\n"
            f"Zaloguj się do serwisu, aby odpowiedzieć."
        )
        return cls.wyslij(wiadomosc.odbiorca.email, temat, tresc)

    @classmethod
    def powiadom_o_nowym_zamowieniu(cls, zamowienie):
        """Wysyła powiadomienie do sprzedawcy o złożeniu nowej rezerwacji."""
        sprzedawca = zamowienie.ogloszenie.sprzedawca
        temat = f"Nowe zamówienie na pojazd: {zamowienie.ogloszenie.tytul}"
        tresc = (
            f"Witaj {sprzedawca.nazwa_wyswietlana()},\n\n"
            f"Kupujący {zamowienie.kupujacy.nazwa_wyswietlana()} złożył zamówienie (rezerwację) "
            f"na Twój samochód: „{zamowienie.ogloszenie.tytul}” za kwotę {zamowienie.cena} zł.\n\n"
            f"Uwagi kupującego:\n{zamowienie.uwagi_kupujacego or '(brak)'}\n\n"
            f"Wejdź w zakładkę „Otrzymane zamówienia” w serwisie, aby zaakceptować lub odrzucić rezerwację."
        )
        return cls.wyslij(sprzedawca.email, temat, tresc)

    @classmethod
    def powiadom_o_akceptacji(cls, zamowienie):
        """Wysyła powiadomienie do kupującego o zaakceptowaniu rezerwacji."""
        kupujacy = zamowienie.kupujacy
        temat = f"Twoje zamówienie zostało zaakceptowane: {zamowienie.ogloszenie.tytul}"
        tresc = (
            f"Witaj {kupujacy.nazwa_wyswietlana()},\n\n"
            f"Sprzedawca zaakceptował Twoje zamówienie na pojazd „{zamowienie.ogloszenie.tytul}”.\n"
            f"Pojazd został oznaczony jako sprzedany.\n"
            f"Możesz teraz skontaktować się ze sprzedawcą, sfinalizować odbiór auta, "
            f"a po zakończeniu transakcji potwierdzić odbiór i wystawić ocenę."
        )
        return cls.wyslij(kupujacy.email, temat, tresc)

    @classmethod
    def powiadom_o_odrzuceniu(cls, zamowienie, uzasadnienie=""):
        """Wysyła powiadomienie do kupującego o odrzuceniu rezerwacji."""
        kupujacy = zamowienie.kupujacy
        temat = f"Twoje zamówienie zostało odrzucone: {zamowienie.ogloszenie.tytul}"
        tresc = (
            f"Witaj {kupujacy.nazwa_wyswietlana()},\n\n"
            f"Sprzedawca odrzucił Twoje zamówienie na pojazd „{zamowienie.ogloszenie.tytul}”.\n"
            f"Powód odrzucenia:\n{uzasadnienie or '(brak uzasadnienia)'}\n\n"
            f"Ogłoszenie powróciło do stanu aktywnych ofert na giełdzie."
        )
        return cls.wyslij(kupujacy.email, temat, tresc)
