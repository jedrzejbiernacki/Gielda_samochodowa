from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal

class TypOplaty(models.TextChoices):
    DODATKOWE_OGLOSZENIE = 'DODATKOWE_OGLOSZENIE', 'Dodatkowe ogłoszenie'
    WYROZNIENIE = 'WYROZNIENIE', 'Wyróżnienie'

class Cennik(models.Model):
    limit_ogloszen_prywatny = models.IntegerField('Limit ogłoszeń dla konta prywatnego', default=2)
    limit_ogloszen_komis = models.IntegerField('Limit ogłoszeń dla komisu', default=10)
    cena_dodatkowe_ogloszenie = models.DecimalField(
        'Cena za dodatkowe ogłoszenie (zł)',
        max_digits=10,
        decimal_places=2,
        default=Decimal('29.99')
    )
    cena_wyroznienie_7dni = models.DecimalField(
        'Cena za wyróżnienie 7 dni (zł)',
        max_digits=10,
        decimal_places=2,
        default=Decimal('19.99')
    )
    cena_wyroznienie_30dni = models.DecimalField(
        'Cena za wyróżnienie 30 dni (zł)',
        max_digits=10,
        decimal_places=2,
        default=Decimal('49.99')
    )

    class Meta:
        db_table = 'platnosci_cennik'
        verbose_name = 'Cennik'
        verbose_name_plural = 'Cennik'

    def __str__(self):
        return 'Cennik opłat i limitów'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

class OplataZaOgloszenie(models.Model):
    uzytkownik = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='oplaty',
        verbose_name='Użytkownik'
    )
    ogloszenie = models.ForeignKey(
        'ogloszenia.Ogloszenie',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='oplaty',
        verbose_name='Ogłoszenie'
    )
    kwota = models.DecimalField('Kwota (zł)', max_digits=10, decimal_places=2)
    typ_oplaty = models.CharField(
        'Typ opłaty',
        max_length=30,
        choices=TypOplaty.choices
    )
    oplacone = models.BooleanField('Opłacone', default=False)
    data_oplacenia = models.DateTimeField('Data opłacenia', null=True, blank=True)
    data_waznosci = models.DateTimeField('Data ważności', null=True, blank=True)
    data_utworzenia = models.DateTimeField('Data utworzenia', auto_now_add=True)

    class Meta:
        db_table = 'platnosci_oplata'
        ordering = ['-data_utworzenia']
        verbose_name = 'Opłata za ogłoszenie'
        verbose_name_plural = 'Opłaty za ogłoszenia'

    def __str__(self):
        return f"Opłata #{self.pk} - {self.get_typ_oplaty_display()} ({self.kwota} zł) - {self.uzytkownik}"

class Wyroznienie(models.Model):
    ogloszenie = models.OneToOneField(
        'ogloszenia.Ogloszenie',
        on_delete=models.CASCADE,
        related_name='wyroznienie_obj',
        verbose_name='Ogłoszenie'
    )
    oplata = models.ForeignKey(
        OplataZaOgloszenie,
        on_delete=models.CASCADE,
        related_name='wyroznienia',
        verbose_name='Opłata'
    )
    data_rozpoczecia = models.DateTimeField('Data rozpoczęcia')
    data_zakonczenia = models.DateTimeField('Data zakończenia')

    class Meta:
        db_table = 'platnosci_wyroznienie'
        verbose_name = 'Wyróżnienie ogłoszenia'
        verbose_name_plural = 'Wyróżnienia ogłoszeń'

    def __str__(self):
        return f"Wyróżnienie #{self.pk} dla {self.ogloszenie} (do {self.data_zakonczenia})"

    @property
    def aktywne(self) -> bool:
        teraz = timezone.now()
        return self.data_rozpoczecia <= teraz < self.data_zakonczenia
