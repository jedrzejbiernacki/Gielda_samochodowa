from django.core.management.base import BaseCommand
from django.utils import timezone
from ogloszenia.models import Ogloszenie, StatusOgloszenia

class Command(BaseCommand):
    help = 'Automatyczne wygaszanie aktywnych ogłoszeń starszych niż 30 dni (WF-17)'

    def handle(self, *args, **options):
        teraz = timezone.now()
        przeterminowane = Ogloszenie.objects.filter(
            status=StatusOgloszenia.AKTYWNE,
            data_wygasniecia__lte=teraz
        )
        liczba = przeterminowane.count()
        przeterminowane.update(status=StatusOgloszenia.WYGASLE)

        self.stdout.write(
            self.style.SUCCESS(
                f'Pomyślnie wygaszono {liczba} ogłoszeń starszych niż termin ważności.'
            )
        )
