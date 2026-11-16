from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Avg

class RolaUzytkownika(models.TextChoices):
    KUPUJACY = 'KUPUJACY', 'Kupujący'
    SPRZEDAWCA = 'SPRZEDAWCA', 'Sprzedawca prywatny'
    KOMIS = 'KOMIS', 'Komis samochodowy'

class Uzytkownik(AbstractUser):
    email = models.EmailField('Adres e-mail', unique=True)
    rola = models.CharField(
        'Rola w systemie',
        max_length=12,
        choices=RolaUzytkownika.choices,
        default=RolaUzytkownika.KUPUJACY
    )
    nazwa_firmy = models.CharField(
        'Nazwa komisu / firmy',
        max_length=120,
        blank=True,
        null=True,
        help_text='Wymagane dla roli Komis'
    )
    telefon = models.CharField('Telefon kontaktowy', max_length=20, blank=True)
    miasto = models.CharField('Miejscowość', max_length=80, blank=True)
    zablokowany = models.BooleanField('Konto zablokowane przez administratora', default=False)
    data_rejestracji = models.DateTimeField('Data rejestracji', auto_now_add=True)

    class Meta:
        db_table = 'konta_uzytkownik'
        verbose_name = 'Użytkownik'
        verbose_name_plural = 'Użytkownicy'

    def __str__(self):
        return self.nazwa_wyswietlana()

    def czy_sprzedawca(self) -> bool:
        """Zwraca True, jeśli użytkownik może wystawiać ogłoszenia (sprzedawca prywatny lub komis)."""
        return self.rola in (RolaUzytkownika.SPRZEDAWCA, RolaUzytkownika.KOMIS)

    def srednia_ocen(self):
        """Oblicza średnią ocen otrzymanych przez sprzedawcę."""
        wynik = self.otrzymane_oceny.aggregate(srednia=Avg('liczba_gwiazdek'))['srednia']
        return round(wynik, 2) if wynik is not None else None

    def liczba_ocen(self) -> int:
        """Liczba wszystkich ocen otrzymanych przez użytkownika."""
        return self.otrzymane_oceny.count()

    def nazwa_wyswietlana(self) -> str:
        """Zwraca nazwę firmy (dla komisu) lub imię i nazwisko / login."""
        if self.rola == RolaUzytkownika.KOMIS and self.nazwa_firmy:
            return self.nazwa_firmy
        pelne = self.get_full_name()
        return pelne if pelne else self.username
