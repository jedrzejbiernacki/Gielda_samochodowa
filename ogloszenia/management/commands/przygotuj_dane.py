from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import os
from django.core.files.base import ContentFile

from konta.models import Uzytkownik, RolaUzytkownika
from ogloszenia.models import (
    Marka,
    ModelPojazdu,
    Ogloszenie,
    Zdjecie,
    StatusOgloszenia,
    Paliwo,
    SkrzyniaBiegow,
    TypNadwozia,
)
from wiadomosci.models import Wiadomosc
from zamowienia.models import Zamowienie, Ocena, StatusZamowienia

def generuj_obraz_svg(tytul: str, kolor_tla="#2c3e50") -> bytes:
    """Generuje proste zdjęcie SVG jako miniatury samochodu."""
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="800" height="500" viewBox="0 0 800 500">
      <defs>
        <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style="stop-color:{kolor_tla};stop-opacity:1" />
          <stop offset="100%" style="stop-color:#1a252f;stop-opacity:1" />
        </linearGradient>
      </defs>
      <rect width="100%" height="100%" fill="url(#grad)" />
      <g fill="#ecf0f1" text-anchor="middle" font-family="sans-serif">
        <text x="400" y="220" font-size="44" font-weight="bold">🚗 GIEŁDA SAMOCHODOWA</text>
        <text x="400" y="280" font-size="28" fill="#3498db">{tytul}</text>
        <text x="400" y="340" font-size="18" fill="#bdc3c7">Zdjęcie demonstracyjne pojazdu</text>
      </g>
    </svg>"""
    return svg.encode('utf-8')

class Command(BaseCommand):
    help = 'Zasila bazę danych przykładowymi słownikami marek, modeli, kontami i ogłoszeniami.'

    def handle(self, *args, **options):
        self.stdout.write('Generowanie danych początkowych...')

        # 1. Konta użytkowników
        admin_user, _ = Uzytkownik.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@gielda-samochodowa.pl',
                'first_name': 'Administrator',
                'last_name': 'Główny',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        admin_user.set_password('Admin1234!')
        admin_user.save()

        komis, _ = Uzytkownik.objects.get_or_create(
            username='komis_premium',
            defaults={
                'email': 'biuro@premium-auto.pl',
                'first_name': 'Michał',
                'last_name': 'Wiśniewski',
                'rola': RolaUzytkownika.KOMIS,
                'nazwa_firmy': 'Premium Auto Centrum Warszawa',
                'telefon': '+48 22 123 45 67',
                'miasto': 'Warszawa',
            }
        )
        komis.set_password('Komis1234!')
        komis.save()

        sprzedawca, _ = Uzytkownik.objects.get_or_create(
            username='sprzedawca_jan',
            defaults={
                'email': 'jan.kowalski@example.com',
                'first_name': 'Jan',
                'last_name': 'Kowalski',
                'rola': RolaUzytkownika.SPRZEDAWCA,
                'telefon': '+48 601 234 567',
                'miasto': 'Kraków',
            }
        )
        sprzedawca.set_password('Jan12345!')
        sprzedawca.save()

        kupujacy, _ = Uzytkownik.objects.get_or_create(
            username='kupujacy_adam',
            defaults={
                'email': 'adam.nowak@example.com',
                'first_name': 'Adam',
                'last_name': 'Nowak',
                'rola': RolaUzytkownika.KUPUJACY,
                'telefon': '+48 502 345 678',
                'miasto': 'Wrocław',
            }
        )
        kupujacy.set_password('Adam1234!')
        kupujacy.save()

        # 2. Słowniki marek i modeli
        katalog = {
            'BMW': ['Seria 3', 'Seria 5', 'X3', 'X5', 'Seria 1'],
            'Audi': ['A3', 'A4', 'A6', 'Q5', 'Q7'],
            'Mercedes-Benz': ['Klasa C', 'Klasa E', 'GLC', 'Klasa A'],
            'Toyota': ['Corolla', 'Yaris', 'RAV4', 'Camry', 'Prius'],
            'Volkswagen': ['Golf', 'Passat', 'Tiguan', 'Polo', 'Arteon'],
            'Ford': ['Focus', 'Mondeo', 'Kuga', 'Mustang', 'Fiesta'],
            'Volvo': ['XC60', 'XC90', 'V60', 'V40'],
            'Kia': ['Ceed', 'Sportage', 'Stinger'],
        }

        modele_obiekty = {}
        for marka_nazwa, modele_lista in katalog.items():
            marka_obj, _ = Marka.objects.get_or_create(nazwa=marka_nazwa)
            for model_nazwa in modele_lista:
                mod_obj, _ = ModelPojazdu.objects.get_or_create(marka=marka_obj, nazwa=model_nazwa)
                modele_obiekty[f"{marka_nazwa} {model_nazwa}"] = mod_obj

        # 3. Przykładowe ogłoszenia
        przykladowe_ogloszenia = [
            {
                'sprzedawca': komis,
                'model_klucz': 'BMW Seria 3',
                'tytul': 'BMW Seria 3 320d xDrive M-Pakiet Salon Polska',
                'opis': 'Samochód w stanie idealnym, bezwypadkowy, serwisowany w ASO. Pełne wyposażenie: nagłośnienie Harman/Kardon, skórzana tapicerka, reflektory laserowe, napęd xDrive 4x4.',
                'rok_produkcji': 2021,
                'przebieg_km': 64000,
                'pojemnosc_cm3': 1995,
                'moc_km': 190,
                'paliwo': Paliwo.DIESEL,
                'skrzynia': SkrzyniaBiegow.AUTOMATYCZNA,
                'nadwozie': TypNadwozia.SEDAN,
                'kolor': 'Czarny szafir',
                'vin': 'WBA31AY080FK12345',
                'lokalizacja': 'Warszawa',
                'cena': Decimal('149900.00'),
                'status': StatusOgloszenia.AKTYWNE,
                'kolor_svg': '#1e272e',
            },
            {
                'sprzedawca': sprzedawca,
                'model_klucz': 'Toyota Corolla',
                'tytul': 'Toyota Corolla 1.8 Hybrid Comfort Tech Faktura VAT',
                'opis': 'Niezawodna hybryda z polskiego salonu od pierwszego właściciela. Średnie spalanie 4.2 l/100km. Nowe opony zimowe, kamera cofania, Apple CarPlay.',
                'rok_produkcji': 2022,
                'przebieg_km': 42000,
                'pojemnosc_cm3': 1798,
                'moc_km': 122,
                'paliwo': Paliwo.HYBRYDA,
                'skrzynia': SkrzyniaBiegow.AUTOMATYCZNA,
                'nadwozie': TypNadwozia.KOMBI,
                'kolor': 'Biała perła',
                'vin': 'JTNKH3BE60J054321',
                'lokalizacja': 'Kraków',
                'cena': Decimal('89900.00'),
                'status': StatusOgloszenia.AKTYWNE,
                'kolor_svg': '#2c3e50',
            },
            {
                'sprzedawca': komis,
                'model_klucz': 'Audi A4',
                'tytul': 'Audi A4 2.0 TFSI S-line Quattro Virtual Cockpit',
                'opis': 'Elegancki i dynamiczny sedan w wersji S-line z napędem na cztery koła. Pakiet asystentów jazdy, lampy Matrix LED, stan perfekcyjny.',
                'rok_produkcji': 2020,
                'przebieg_km': 78000,
                'pojemnosc_cm3': 1984,
                'moc_km': 204,
                'paliwo': Paliwo.BENZYNA,
                'skrzynia': SkrzyniaBiegow.AUTOMATYCZNA,
                'nadwozie': TypNadwozia.SEDAN,
                'kolor': 'Szary Daytona',
                'vin': 'WAUZZZF48LA098765',
                'lokalizacja': 'Warszawa',
                'cena': Decimal('129000.00'),
                'status': StatusOgloszenia.AKTYWNE,
                'kolor_svg': '#34495e',
            },
            {
                'sprzedawca': sprzedawca,
                'model_klucz': 'Volkswagen Golf',
                'tytul': 'Volkswagen Golf VII 1.4 TSI Highline Bezwypadkowy',
                'opis': 'Zadbane auto rodzinne, 6-biegowa skrzynia manualna, czujniki parkowania przód/tył, podgrzewane fotele, klimatyzacja dwustrefowa.',
                'rok_produkcji': 2017,
                'przebieg_km': 118000,
                'pojemnosc_cm3': 1395,
                'moc_km': 125,
                'paliwo': Paliwo.BENZYNA,
                'skrzynia': SkrzyniaBiegow.MANUALNA,
                'nadwozie': TypNadwozia.HATCHBACK,
                'kolor': 'Niebieski metalik',
                'vin': 'WVWZZZAUZHP112233',
                'lokalizacja': 'Kraków',
                'cena': Decimal('52000.00'),
                'status': StatusOgloszenia.AKTYWNE,
                'kolor_svg': '#2980b9',
            },
            {
                'sprzedawca': komis,
                'model_klucz': 'Volvo XC60',
                'tytul': 'Volvo XC60 B4 AWD Inscription Panorama Bower&Wilkins',
                'opis': 'Luksusowy szwedzki SUV z napędem AWD. Rewelacyjny stan, dach panoramiczny, wentylowane fotele z masażem.',
                'rok_produkcji': 2021,
                'przebieg_km': 51000,
                'pojemnosc_cm3': 1969,
                'moc_km': 197,
                'paliwo': Paliwo.DIESEL,
                'skrzynia': SkrzyniaBiegow.AUTOMATYCZNA,
                'nadwozie': TypNadwozia.SUV,
                'kolor': 'Granatowy',
                'vin': 'YV1UZA8VCM1654321',
                'lokalizacja': 'Warszawa',
                'cena': Decimal('179000.00'),
                'status': StatusOgloszenia.AKTYWNE,
                'kolor_svg': '#16a085',
            },
        ]

        utworzone_ogloszenia = []
        for dane in przykladowe_ogloszenia:
            model_obj = modele_obiekty[dane['model_klucz']]
            kolor_svg = dane.pop('kolor_svg')
            dane.pop('model_klucz')

            ogloszenie, created = Ogloszenie.objects.get_or_create(
                tytul=dane['tytul'],
                defaults={
                    **dane,
                    'model_pojazdu': model_obj,
                    'data_wygasniecia': timezone.now() + timedelta(days=30),
                }
            )
            utworzone_ogloszenia.append(ogloszenie)

            if created or not ogloszenie.zdjecia.exists():
                svg_data = generuj_obraz_svg(ogloszenie.tytul, kolor_svg)
                zdj = Zdjecie(ogloszenie=ogloszenie, kolejnosc=0)
                zdj.plik.save(f"auto_{ogloszenie.id}.svg", ContentFile(svg_data), save=True)

        # 4. Przykładowa konwersacja w wątku wiadomości
        pierwsze_ogl = utworzone_ogloszenia[0]
        if not Wiadomosc.objects.filter(ogloszenie=pierwsze_ogl, kupujacy=kupujacy).exists():
            w1 = Wiadomosc.objects.create(
                ogloszenie=pierwsze_ogl,
                kupujacy=kupujacy,
                nadawca=kupujacy,
                odbiorca=pierwsze_ogl.sprzedawca,
                tresc='Dzień dobry, czy samochód posiada kompletną książkę serwisową i dwa kluczyki?',
                przeczytana=True,
            )
            w2 = Wiadomosc.objects.create(
                ogloszenie=pierwsze_ogl,
                kupujacy=kupujacy,
                nadawca=pierwsze_ogl.sprzedawca,
                odbiorca=kupujacy,
                tresc='Dzień dobry panie Adamie, tak, samochód ma pełną historię w ASO BMW oraz komplet dokumentów i 2 kluczyki. Zapraszam na jazdę próbną.',
                przeczytana=False,
            )

        # 5. Przykładowe zamówienie i zakończona ocena transakcji
        drugie_ogl = utworzone_ogloszenia[1]
        zamowienie, zam_created = Zamowienie.objects.get_or_create(
            ogloszenie=drugie_ogl,
            kupujacy=kupujacy,
            defaults={
                'cena': drugie_ogl.cena,
                'status': StatusZamowienia.ZAKONCZONE,
                'uwagi_kupujacego': 'Chciałbym odebrać samochód w sobotę przed południem.',
                'data_decyzji': timezone.now() - timedelta(days=5),
                'data_zakonczenia': timezone.now() - timedelta(days=2),
            }
        )

        if zam_created:
            drugie_ogl.status = StatusOgloszenia.SPRZEDANE
            drugie_ogl.save()

            Ocena.objects.create(
                zamowienie=zamowienie,
                oceniajacy=kupujacy,
                oceniany=drugie_ogl.sprzedawca,
                liczba_gwiazdek=5,
                komentarz='Transakcja przebiegła wzorowo. Samochód dokładnie taki jak w ogłoszeniu, sprzedawca bardzo pomocny i uczciwy. Szczerze polecam!'
            )

        self.stdout.write(self.style.SUCCESS('Pomyślnie utworzono dane demonstracyjne serwisu Giełda samochodowa.'))
