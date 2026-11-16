from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator
from .exceptions import NiedozwolonaZmianaStatusu

def sciezka_zdjecia(instance, filename):
    return f"ogloszenia/{instance.ogloszenie_id or 'nowe'}/{filename}"

class Paliwo(models.TextChoices):
    BENZYNA = 'BENZYNA', 'Benzyna'
    DIESEL = 'DIESEL', 'Diesel'
    LPG = 'LPG', 'LPG'
    HYBRYDA = 'HYBRYDA', 'Hybryda'
    ELEKTRYCZNY = 'ELEKTRYCZNY', 'Elektryczny'

class SkrzyniaBiegow(models.TextChoices):
    MANUALNA = 'MANUALNA', 'Manualna'
    AUTOMATYCZNA = 'AUTOMATYCZNA', 'Automatyczna'

class TypNadwozia(models.TextChoices):
    SEDAN = 'SEDAN', 'Sedan'
    HATCHBACK = 'HATCHBACK', 'Hatchback'
    KOMBI = 'KOMBI', 'Kombi'
    SUV = 'SUV', 'SUV'
    COUPE = 'COUPE', 'Coupe'
    KABRIOLET = 'KABRIOLET', 'Kabriolet'
    VAN = 'VAN', 'Van'
    PICKUP = 'PICKUP', 'Pickup'

class StatusOgloszenia(models.TextChoices):
    SZKIC = 'SZKIC', 'Szkic'
    AKTYWNE = 'AKTYWNE', 'Aktywne'
    ZAREZERWOWANE = 'ZAREZERWOWANE', 'Zarezerwowane'
    SPRZEDANE = 'SPRZEDANE', 'Sprzedane'
    WYGASLE = 'WYGASLE', 'Wygasłe'
    ZABLOKOWANE = 'ZABLOKOWANE', 'Zablokowane'

class TypSprzedazy(models.TextChoices):
    KUP_TERAZ = 'KUP_TERAZ', 'Kup teraz'
    LICYTACJA = 'LICYTACJA', 'Licytacja'


class Marka(models.Model):
    nazwa = models.CharField('Nazwa marki', max_length=60, unique=True)

    class Meta:
        db_table = 'ogloszenia_marka'
        verbose_name = 'Marka'
        verbose_name_plural = 'Marki'
        ordering = ['nazwa']

    def __str__(self):
        return self.nazwa

class ModelPojazdu(models.Model):
    marka = models.ForeignKey(
        Marka,
        on_delete=models.CASCADE,
        related_name='modele',
        verbose_name='Marka'
    )
    nazwa = models.CharField('Nazwa modelu', max_length=60)

    class Meta:
        db_table = 'ogloszenia_modelpojazdu'
        verbose_name = 'Model pojazdu'
        verbose_name_plural = 'Modele pojazdów'
        unique_together = ('marka', 'nazwa')
        ordering = ['marka__nazwa', 'nazwa']

    def __str__(self):
        return f"{self.marka.nazwa} {self.nazwa}"

def domyslna_data_wygasniecia():
    return timezone.now() + timedelta(days=30)

class Ogloszenie(models.Model):
    sprzedawca = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ogloszenia',
        verbose_name='Sprzedawca'
    )
    model_pojazdu = models.ForeignKey(
        ModelPojazdu,
        on_delete=models.PROTECT,
        related_name='ogloszenia',
        verbose_name='Model pojazdu'
    )
    tytul = models.CharField('Tytuł ogłoszenia', max_length=120)
    opis = models.TextField('Opis samochodu')
    rok_produkcji = models.PositiveSmallIntegerField(
        'Rok produkcji',
        db_index=True,
        validators=[
            MinValueValidator(1950, message='Rok produkcji nie może być wcześniejszy niż 1950.')
        ]
    )
    przebieg_km = models.PositiveIntegerField('Przebieg w km', db_index=True)
    pojemnosc_cm3 = models.PositiveIntegerField('Pojemność silnika (cm³)', null=True, blank=True)
    moc_km = models.PositiveIntegerField('Moc (KM)', null=True, blank=True)
    paliwo = models.CharField('Rodzaj paliwa', max_length=12, choices=Paliwo.choices, db_index=True)
    skrzynia = models.CharField('Skrzynia biegów', max_length=12, choices=SkrzyniaBiegow.choices)
    nadwozie = models.CharField('Typ nadwozia', max_length=10, choices=TypNadwozia.choices)
    kolor = models.CharField('Kolor nadwozia', max_length=30)
    vin = models.CharField('Numer VIN', max_length=17, blank=True, null=True)
    lokalizacja = models.CharField('Miejscowość', max_length=80, db_index=True)
    cena = models.DecimalField(
        'Cena (zł)',
        max_digits=10,
        decimal_places=2,
        db_index=True,
        validators=[MinValueValidator(Decimal('1.00'), message='Cena musi wynosić co najmniej 1 zł.')]
    )
    status = models.CharField(
        'Status ogłoszenia',
        max_length=14,
        choices=StatusOgloszenia.choices,
        default=StatusOgloszenia.AKTYWNE,
        db_index=True
    )
    data_dodania = models.DateTimeField('Data dodania', auto_now_add=True)
    data_aktualizacji = models.DateTimeField('Data aktualizacji', auto_now=True)
    data_wygasniecia = models.DateTimeField('Data wygaśnięcia', default=domyslna_data_wygasniecia)
    liczba_wyswietlen = models.PositiveIntegerField('Liczba wyświetleń', default=0)
    typ_sprzedazy = models.CharField(
        'Typ sprzedaży',
        max_length=10,
        choices=TypSprzedazy.choices,
        default=TypSprzedazy.KUP_TERAZ,
        db_index=True
    )
    cena_wywolawcza = models.DecimalField(
        'Cena wywoławcza (zł)',
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    data_zakonczenia_licytacji = models.DateTimeField(
        'Data zakończenia licytacji',
        null=True,
        blank=True
    )
    wyroznione = models.BooleanField(
        'Wyróżnione',
        default=False,
        db_index=True
    )


    class Meta:
        db_table = 'ogloszenia_ogloszenie'
        verbose_name = 'Ogłoszenie'
        verbose_name_plural = 'Ogłoszenia'
        ordering = ['-data_dodania']

    def __str__(self):
        return f"{self.tytul} ({self.cena} zł)"

    def clean(self):
        super().clean()
        maks_rok = timezone.now().year + 1
        if self.rok_produkcji and self.rok_produkcji > maks_rok:
            from django.core.exceptions import ValidationError
            raise ValidationError({'rok_produkcji': f'Rok produkcji nie może przekraczać {maks_rok}.'})
        if self.vin and len(self.vin.strip()) != 17:
            from django.core.exceptions import ValidationError
            raise ValidationError({'vin': 'Numer VIN musi składać się dokładnie z 17 znaków.'})

    def opublikuj(self):
        """Przejście do stanu AKTYWNE ze stanu SZKIC lub WYGASLE."""
        if self.status not in (StatusOgloszenia.SZKIC, StatusOgloszenia.WYGASLE):
            raise NiedozwolonaZmianaStatusu(
                f"Nie można opublikować ogłoszenia ze statusem '{self.get_status_display()}'."
            )
        self.status = StatusOgloszenia.AKTYWNE
        self.data_wygasniecia = timezone.now() + timedelta(days=30)
        self.save(update_fields=['status', 'data_wygasniecia', 'data_aktualizacji'])

    def zarezerwuj(self):
        """Przejście ze stanu AKTYWNE do ZAREZERWOWANE."""
        if self.status != StatusOgloszenia.AKTYWNE:
            raise NiedozwolonaZmianaStatusu(
                f"Nie można zarezerwować ogłoszenia ze statusem '{self.get_status_display()}'."
            )
        self.status = StatusOgloszenia.ZAREZERWOWANE
        self.save(update_fields=['status', 'data_aktualizacji'])

    def zwolnij_rezerwacje(self):
        """Powrót ze stanu ZAREZERWOWANE do AKTYWNE."""
        if self.status != StatusOgloszenia.ZAREZERWOWANE:
            raise NiedozwolonaZmianaStatusu(
                f"Nie można zwolnić rezerwacji ogłoszenia ze statusem '{self.get_status_display()}'."
            )
        self.status = StatusOgloszenia.AKTYWNE
        self.save(update_fields=['status', 'data_aktualizacji'])

    def oznacz_jako_sprzedane(self):
        """Przejście do stanu SPRZEDANE."""
        if self.status not in (StatusOgloszenia.ZAREZERWOWANE, StatusOgloszenia.AKTYWNE):
            raise NiedozwolonaZmianaStatusu(
                f"Nie można oznaczyć jako sprzedane ogłoszenia ze statusem '{self.get_status_display()}'."
            )
        self.status = StatusOgloszenia.SPRZEDANE
        self.save(update_fields=['status', 'data_aktualizacji'])

    def zablokuj(self):
        """Blokada przez administratora."""
        self.status = StatusOgloszenia.ZABLOKOWANE
        self.save(update_fields=['status', 'data_aktualizacji'])

    def odblokuj(self):
        """Odblokowanie przez administratora."""
        if self.status != StatusOgloszenia.ZABLOKOWANE:
            raise NiedozwolonaZmianaStatusu("Tylko zablokowane ogłoszenie może zostać odblokowane.")
        self.status = StatusOgloszenia.AKTYWNE
        self.save(update_fields=['status', 'data_aktualizacji'])

    def przedluz(self, dni=30):
        """Przedłużenie terminu ważności ogłoszenia o 30 dni."""
        baza = self.data_wygasniecia if self.data_wygasniecia > timezone.now() else timezone.now()
        self.data_wygasniecia = baza + timedelta(days=dni)
        if self.status == StatusOgloszenia.WYGASLE:
            self.status = StatusOgloszenia.AKTYWNE
        self.save(update_fields=['data_wygasniecia', 'status', 'data_aktualizacji'])

    def czy_dostepne(self) -> bool:
        """Sprawdza, czy ogłoszenie jest aktywne, niewygasłe i sprzedawca nie jest zablokowany."""
        if self.status != StatusOgloszenia.AKTYWNE:
            return False
        if self.data_wygasniecia <= timezone.now():
            return False
        if self.sprzedawca.zablokowany:
            return False
        return True

    def glowne_zdjecie(self):
        """Zwraca pierwsze zdjęcie ogłoszenia lub None."""
        return self.zdjecia.order_by('kolejnosc', 'id').first()

    def najwyzsza_oferta(self):
        """Zwraca najwyższą złożoną ofertę licytacji lub None."""
        return self.oferty.order_by('-kwota', 'data_zlozenia').first()

    def czy_licytacja_aktywna(self) -> bool:
        """Sprawdza, czy licytacja jest aktywna (typ LICYTACJA, data zakończenia w przyszłości i status AKTYWNE)."""
        if self.typ_sprzedazy != TypSprzedazy.LICYTACJA:
            return False
        if not self.data_zakonczenia_licytacji or self.data_zakonczenia_licytacji <= timezone.now():
            return False
        if self.status != StatusOgloszenia.AKTYWNE:
            return False
        return True

class Oferta(models.Model):
    ogloszenie = models.ForeignKey(
        Ogloszenie,
        on_delete=models.CASCADE,
        related_name='oferty',
        verbose_name='Ogłoszenie'
    )
    licytujacy = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='oferty_licytacji',
        verbose_name='Licytujący'
    )
    kwota = models.DecimalField(
        'Kwota (zł)',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('1.00'), message='Kwota oferty musi wynosić co najmniej 1 zł.')]
    )
    data_zlozenia = models.DateTimeField('Data złożenia', auto_now_add=True)

    class Meta:
        db_table = 'ogloszenia_oferta'
        ordering = ['-kwota']
        verbose_name = 'Oferta licytacji'
        verbose_name_plural = 'Oferty licytacji'

    def __str__(self):
        return f"{self.licytujacy} - {self.kwota} zł ({self.ogloszenie.tytul})"

    @classmethod
    def najwyzsza_oferta(cls, ogloszenie):
        """Zwraca najwyższą ofertę dla danego ogłoszenia."""
        return cls.objects.filter(ogloszenie=ogloszenie).order_by('-kwota', 'data_zlozenia').first()

class Zdjecie(models.Model):
    ogloszenie = models.ForeignKey(
        Ogloszenie,
        on_delete=models.CASCADE,
        related_name='zdjecia',
        verbose_name='Ogłoszenie'
    )
    plik = models.ImageField('Plik zdjęcia', upload_to=sciezka_zdjecia)
    kolejnosc = models.PositiveSmallIntegerField('Kolejność w galerii', default=0)
    data_dodania = models.DateTimeField('Data przesłania', auto_now_add=True)

    class Meta:
        db_table = 'ogloszenia_zdjecie'
        verbose_name = 'Zdjęcie'
        verbose_name_plural = 'Zdjęcia'
        ordering = ['kolejnosc', 'id']

    def __str__(self):
        return f"Zdjęcie #{self.id} dla ogłoszenia #{self.ogloszenie_id}"

class Ulubione(models.Model):
    uzytkownik = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ulubione',
        verbose_name='Użytkownik'
    )
    ogloszenie = models.ForeignKey(
        Ogloszenie,
        on_delete=models.CASCADE,
        related_name='polubione_przez',
        verbose_name='Ogłoszenie'
    )
    data_dodania = models.DateTimeField('Data zapisania', auto_now_add=True)

    class Meta:
        db_table = 'ogloszenia_ulubione'
        verbose_name = 'Ulubione ogłoszenie'
        verbose_name_plural = 'Ulubione ogłoszenia'
        unique_together = ('uzytkownik', 'ogloszenie')
        ordering = ['-data_dodania']

    def __str__(self):
        return f"{self.uzytkownik} -> {self.ogloszenie}"
