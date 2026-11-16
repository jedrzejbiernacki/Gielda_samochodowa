from django.db.models import Q
from django.utils import timezone
from .models import Ogloszenie, StatusOgloszenia

class WyszukiwarkaOgloszen:
    """Klasa usługi odpowiadająca za filtrowanie i sortowanie ogłoszeń."""

    SORT_OPCJE = {
        'data_desc': '-data_dodania',
        'data_asc': 'data_dodania',
        'cena_asc': 'cena',
        'cena_desc': '-cena',
        'rok_desc': '-rok_produkcji',
        'rok_asc': 'rok_produkcji',
        'przebieg_asc': 'przebieg_km',
        'przebieg_desc': '-przebieg_km',
    }

    def __init__(self, cleaned_data=None):
        self.dane = cleaned_data or {}
        self.bledy = {}

    def waliduj_zakresy(self) -> bool:
        """Sprawdza relacje 'od - do' dla ceny, rocznika i przebiegu."""
        poprawne = True

        cena_od = self.dane.get('cena_od')
        cena_do = self.dane.get('cena_do')
        if cena_od is not None and cena_do is not None and cena_od > cena_do:
            self.bledy['cena_od'] = 'Cena „od” nie może być wyższa niż cena „do”.'
            poprawne = False

        rok_od = self.dane.get('rok_od')
        rok_do = self.dane.get('rok_do')
        if rok_od is not None and rok_do is not None and rok_od > rok_do:
            self.bledy['rok_od'] = 'Rok produkcji „od” nie może być większy niż „do”.'
            poprawne = False

        przebieg_od = self.dane.get('przebieg_od')
        przebieg_do = self.dane.get('przebieg_do')
        if przebieg_od is not None and przebieg_do is not None and przebieg_od > przebieg_do:
            self.bledy['przebieg_od'] = 'Przebieg „od” nie może być większy niż „do”.'
            poprawne = False

        return poprawne

    def wyszukaj(self):
        """Buduje zapytanie ORM z uwzględnieniem filtrów, wykluczeń i sortowania."""
        qs = Ogloszenie.objects.filter(
            status__in=[StatusOgloszenia.AKTYWNE, StatusOgloszenia.ZAREZERWOWANE],
            data_wygasniecia__gt=timezone.now(),
            sprzedawca__zablokowany=False
        ).select_related('model_pojazdu', 'model_pojazdu__marka', 'sprzedawca').prefetch_related('zdjecia')

        if not self.waliduj_zakresy():
            return qs.none()

        fraza = self.dane.get('fraza')
        if fraza:
            fraza = fraza.strip()
            qs = qs.filter(
                Q(tytul__icontains=fraza) |
                Q(opis__icontains=fraza) |
                Q(model_pojazdu__nazwa__icontains=fraza) |
                Q(model_pojazdu__marka__nazwa__icontains=fraza)
            )

        marka = self.dane.get('marka')
        if marka:
            qs = qs.filter(model_pojazdu__marka=marka)

        model_pojazdu = self.dane.get('model_pojazdu')
        if model_pojazdu:
            qs = qs.filter(model_pojazdu=model_pojazdu)

        if self.dane.get('cena_od') is not None:
            qs = qs.filter(cena__gte=self.dane['cena_od'])
        if self.dane.get('cena_do') is not None:
            qs = qs.filter(cena__lte=self.dane['cena_do'])

        if self.dane.get('rok_od') is not None:
            qs = qs.filter(rok_produkcji__gte=self.dane['rok_od'])
        if self.dane.get('rok_do') is not None:
            qs = qs.filter(rok_produkcji__lte=self.dane['rok_do'])

        if self.dane.get('przebieg_od') is not None:
            qs = qs.filter(przebieg_km__gte=self.dane['przebieg_od'])
        if self.dane.get('przebieg_do') is not None:
            qs = qs.filter(przebieg_km__lte=self.dane['przebieg_do'])

        paliwo = self.dane.get('paliwo')
        if paliwo:
            qs = qs.filter(paliwo=paliwo)

        skrzynia = self.dane.get('skrzynia')
        if skrzynia:
            qs = qs.filter(skrzynia=skrzynia)

        nadwozie = self.dane.get('nadwozie')
        if nadwozie:
            qs = qs.filter(nadwozie=nadwozie)

        lokalizacja = self.dane.get('lokalizacja')
        if lokalizacja:
            qs = qs.filter(lokalizacja__icontains=lokalizacja.strip())

        sortowanie = self.dane.get('sortowanie', 'data_desc')
        pole_sortowania = self.SORT_OPCJE.get(sortowanie, '-data_dodania')
        qs = qs.order_by('-wyroznione', pole_sortowania)

        return qs


class Porownywarka:
    """Zarządza porównaniem do 3 samochodów w sesji użytkownika."""

    SESJA_KLUCZ = 'porownywarka'
    MAKS_POJAZDOW = 3

    def __init__(self, session):
        self.session = session
        if self.SESJA_KLUCZ not in self.session:
            self.session[self.SESJA_KLUCZ] = []
        self.lista_id = self.session[self.SESJA_KLUCZ]

    def _oznacz_zmiane(self):
        if hasattr(self.session, 'modified'):
            self.session.modified = True

    def dodaj(self, ogloszenie_id: int) -> bool:
        """Dodaje ogłoszenie do porównywarki, jeśli nie przekroczono limitu 3."""
        ogloszenie_id = int(ogloszenie_id)
        if ogloszenie_id in self.lista_id:
            return True
        if len(self.lista_id) >= self.MAKS_POJAZDOW:
            return False
        self.lista_id.append(ogloszenie_id)
        self._oznacz_zmiane()
        return True

    def usun(self, ogloszenie_id: int):
        """Usuwa ogłoszenie z listy porównania."""
        ogloszenie_id = int(ogloszenie_id)
        if ogloszenie_id in self.lista_id:
            self.lista_id.remove(ogloszenie_id)
            self._oznacz_zmiane()

    def wyczysc(self):
        """Czyści listę porównania."""
        self.lista_id.clear()
        self._oznacz_zmiane()

    def ogloszenia(self):
        """Zwraca obiekty ogłoszeń znajdujące się w porównywarce."""
        if not self.lista_id:
            return []
        ogloszenia_qs = Ogloszenie.objects.filter(
            id__in=self.lista_id
        ).select_related('model_pojazdu', 'model_pojazdu__marka', 'sprzedawca').prefetch_related('zdjecia')
        slownik = {o.id: o for o in ogloszenia_qs}
        return [slownik[oid] for oid in self.lista_id if oid in slownik]

    def zawiera(self, ogloszenie_id: int) -> bool:
        return int(ogloszenie_id) in self.lista_id
