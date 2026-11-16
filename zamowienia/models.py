from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from ogloszenia.models import Ogloszenie
from .exceptions import NiedozwolonaOperacjaZamowienia

class StatusZamowienia(models.TextChoices):
    ZLOZONE = 'ZLOZONE', 'Złożone'
    ZAAKCEPTOWANE = 'ZAAKCEPTOWANE', 'Zaakceptowane'
    ODRZUCONE = 'ODRZUCONE', 'Odrzucone'
    ANULOWANE = 'ANULOWANE', 'Anulowane'
    ZAKONCZONE = 'ZAKONCZONE', 'Zakończone'

class Zamowienie(models.Model):
    ogloszenie = models.ForeignKey(
        Ogloszenie,
        on_delete=models.PROTECT,
        related_name='zamowienia',
        verbose_name='Zamawiany samochód'
    )
    kupujacy = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='zamowienia',
        verbose_name='Kupujący'
    )
    cena = models.DecimalField(
        'Cena w chwili zamówienia (zł)',
        max_digits=10,
        decimal_places=2
    )
    status = models.CharField(
        'Status zamówienia',
        max_length=14,
        choices=StatusZamowienia.choices,
        default=StatusZamowienia.ZLOZONE,
        db_index=True
    )
    uwagi_kupujacego = models.TextField('Uwagi kupującego', blank=True)
    uzasadnienie_odrzucenia = models.TextField('Powód odrzucenia', blank=True)
    data_zlozenia = models.DateTimeField('Data złożenia', auto_now_add=True)
    data_decyzji = models.DateTimeField('Data akceptacji/odrzucenia/anulowania', null=True, blank=True)
    data_zakonczenia = models.DateTimeField('Data potwierdzenia odbioru', null=True, blank=True)

    class Meta:
        db_table = 'zamowienia_zamowienie'
        verbose_name = 'Zamówienie (rezerwacja)'
        verbose_name_plural = 'Zamówienia (rezerwacje)'
        ordering = ['-data_zlozenia']

    def __str__(self):
        return f"Zamówienie #{self.id} na {self.ogloszenie.tytul} ({self.get_status_display()})"

    # Metody przejść stanów z diagramu stanów (Rysunek 7)
    def akceptuj(self):
        """Akceptacja rezerwacji przez sprzedawcę (ZLOZONE -> ZAAKCEPTOWANE)."""
        if self.status != StatusZamowienia.ZLOZONE:
            raise NiedozwolonaOperacjaZamowienia(
                f"Nie można zaakceptować zamówienia o statusie '{self.get_status_display()}'."
            )
        self.status = StatusZamowienia.ZAAKCEPTOWANE
        self.data_decyzji = timezone.now()
        self.save(update_fields=['status', 'data_decyzji'])

    def odrzuc(self, uzasadnienie: str = ""):
        """Odrzucenie rezerwacji przez sprzedawcę (ZLOZONE -> ODRZUCONE)."""
        if self.status != StatusZamowienia.ZLOZONE:
            raise NiedozwolonaOperacjaZamowienia(
                f"Nie można odrzucić zamówienia o statusie '{self.get_status_display()}'."
            )
        self.status = StatusZamowienia.ODRZUCONE
        self.uzasadnienie_odrzucenia = uzasadnienie or ""
        self.data_decyzji = timezone.now()
        self.save(update_fields=['status', 'uzasadnienie_odrzucenia', 'data_decyzji'])

    def anuluj(self):
        """Anulowanie rezerwacji przez kupującego przed decyzją (ZLOZONE -> ANULOWANE)."""
        if self.status != StatusZamowienia.ZLOZONE:
            raise NiedozwolonaOperacjaZamowienia(
                f"Można anulować jedynie zamówienie w stanie 'Złożone', bieżący status: '{self.get_status_display()}'."
            )
        self.status = StatusZamowienia.ANULOWANE
        self.data_decyzji = timezone.now()
        self.save(update_fields=['status', 'data_decyzji'])

    def zakoncz(self):
        """Potwierdzenie odbioru samochodu przez kupującego (ZAAKCEPTOWANE -> ZAKONCZONE)."""
        if self.status != StatusZamowienia.ZAAKCEPTOWANE:
            raise NiedozwolonaOperacjaZamowienia(
                f"Tylko zaakceptowane zamówienie może zostać zakończone, bieżący status: '{self.get_status_display()}'."
            )
        self.status = StatusZamowienia.ZAKONCZONE
        self.data_zakonczenia = timezone.now()
        self.save(update_fields=['status', 'data_zakonczenia'])

    def czy_mozna_ocenic(self) -> bool:
        """Ocena może być wystawiona po zakończeniu odbioru i tylko raz."""
        if self.status != StatusZamowienia.ZAKONCZONE:
            return False
        return not hasattr(self, 'ocena')


class Ocena(models.Model):
    zamowienie = models.OneToOneField(
        Zamowienie,
        on_delete=models.CASCADE,
        related_name='ocena',
        verbose_name='Oceniana transakcja'
    )
    oceniajacy = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wystawione_oceny',
        verbose_name='Kupujący'
    )
    oceniany = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='otrzymane_oceny',
        verbose_name='Sprzedawca'
    )
    liczba_gwiazdek = models.PositiveSmallIntegerField(
        'Liczba gwiazdek (1–5)',
        validators=[
            MinValueValidator(1, message='Ocena musi wynosić co najmniej 1.'),
            MaxValueValidator(5, message='Ocena nie może przekraczać 5.')
        ]
    )
    komentarz = models.TextField('Komentarz do oceny')
    data_wystawienia = models.DateTimeField('Data wystawienia', auto_now_add=True)

    class Meta:
        db_table = 'zamowienia_ocena'
        verbose_name = 'Ocena sprzedawcy'
        verbose_name_plural = 'Oceny sprzedawców'
        ordering = ['-data_wystawienia']

    def __str__(self):
        return f"Ocena {self.liczba_gwiazdek}★ od {self.oceniajacy} dla {self.oceniany}"
