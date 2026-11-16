from django.db import models
from django.conf import settings
from ogloszenia.models import Ogloszenie

class Wiadomosc(models.Model):
    ogloszenie = models.ForeignKey(
        Ogloszenie,
        on_delete=models.CASCADE,
        related_name='wiadomosci',
        verbose_name='Ogłoszenie'
    )
    kupujacy = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='watki_wiadomosci',
        verbose_name='Kupujący (wątek)'
    )
    nadawca = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wyslane_wiadomosci',
        verbose_name='Nadawca'
    )
    odbiorca = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='odebrane_wiadomosci',
        verbose_name='Odbiorca'
    )
    tresc = models.TextField('Treść wiadomości', max_length=2000)
    data_wyslania = models.DateTimeField('Data wysłania', auto_now_add=True)
    przeczytana = models.BooleanField('Czy przeczytana', default=False)

    class Meta:
        db_table = 'wiadomosci_wiadomosc'
        verbose_name = 'Wiadomość'
        verbose_name_plural = 'Wiadomości'
        indexes = [
            models.Index(fields=['ogloszenie', 'kupujacy'], name='idx_ogloszenie_kupujacy'),
        ]
        ordering = ['data_wyslania']

    def __str__(self):
        return f"Wiadomość od {self.nadawca} do {self.odbiorca} (Ogłoszenie #{self.ogloszenie_id})"

    def oznacz_jako_przeczytana(self):
        """Oznacza wiadomość jako przeczytaną przez odbiorcę."""
        if not self.przeczytana:
            self.przeczytana = True
            self.save(update_fields=['przeczytana'])
