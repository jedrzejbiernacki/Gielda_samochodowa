from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from django.core.management import call_command

from konta.models import Uzytkownik, RolaUzytkownika
from ogloszenia.models import (
    Marka,
    ModelPojazdu,
    Ogloszenie,
    StatusOgloszenia,
    Paliwo,
    SkrzyniaBiegow,
    TypNadwozia,
)
from ogloszenia.exceptions import NiedozwolonaZmianaStatusu
from ogloszenia.services import WyszukiwarkaOgloszen, Porownywarka

class TestOgloszenia(TestCase):
    def setUp(self):
        self.sprzedawca = Uzytkownik.objects.create_user(
            username='sprzedawca1',
            email='sprz@test.pl',
            password='Password123!',
            rola=RolaUzytkownika.SPRZEDAWCA
        )
        self.marka_bmw = Marka.objects.create(nazwa='BMW')
        self.model_3 = ModelPojazdu.objects.create(marka=self.marka_bmw, nazwa='Seria 3')
        self.marka_audi = Marka.objects.create(nazwa='Audi')
        self.model_a4 = ModelPojazdu.objects.create(marka=self.marka_audi, nazwa='A4')

        self.ogloszenie = Ogloszenie.objects.create(
            sprzedawca=self.sprzedawca,
            model_pojazdu=self.model_3,
            tytul='BMW Seria 3 320d Bardzo ładne',
            opis='Świetny stan, polecam.',
            rok_produkcji=2020,
            przebieg_km=75000,
            pojemnosc_cm3=1995,
            moc_km=190,
            paliwo=Paliwo.DIESEL,
            skrzynia=SkrzyniaBiegow.AUTOMATYCZNA,
            nadwozie=TypNadwozia.SEDAN,
            kolor='Czarny',
            vin='WBA31AY080FK12345',
            lokalizacja='Warszawa',
            cena=Decimal('120000.00'),
            status=StatusOgloszenia.AKTYWNE,
            data_wygasniecia=timezone.now() + timedelta(days=30),
        )

    def test_cykl_zycia_i_przejscia_stanow(self):
        # 1. Zarezerwuj aktywne
        self.ogloszenie.zarezerwuj()
        self.assertEqual(self.ogloszenie.status, StatusOgloszenia.ZAREZERWOWANE)

        # 2. Próba ponownej rezerwacji zgłasza błąd
        with self.assertRaises(NiedozwolonaZmianaStatusu):
            self.ogloszenie.zarezerwuj()

        # 3. Zwolnij rezerwację -> AKTYWNE
        self.ogloszenie.zwolnij_rezerwacje()
        self.assertEqual(self.ogloszenie.status, StatusOgloszenia.AKTYWNE)

        # 4. Oznacz jako sprzedane -> SPRZEDANE
        self.ogloszenie.oznacz_jako_sprzedane()
        self.assertEqual(self.ogloszenie.status, StatusOgloszenia.SPRZEDANE)

        # 5. Nie można zarezerwować sprzedanego
        with self.assertRaises(NiedozwolonaZmianaStatusu):
            self.ogloszenie.zarezerwuj()

    def test_czy_dostepne(self):
        self.assertTrue(self.ogloszenie.czy_dostepne())

        # Wygasłe
        self.ogloszenie.data_wygasniecia = timezone.now() - timedelta(days=1)
        self.assertFalse(self.ogloszenie.czy_dostepne())

        # Odnowione
        self.ogloszenie.przedluz(30)
        self.assertTrue(self.ogloszenie.czy_dostepne())

        # Zablokowany sprzedawca
        self.sprzedawca.zablokowany = True
        self.sprzedawca.save()
        self.assertFalse(self.ogloszenie.czy_dostepne())

    def test_wyszukiwarka_ogloszen(self):
        # Utwórz drugie ogłoszenie Audi A4
        Ogloszenie.objects.create(
            sprzedawca=self.sprzedawca,
            model_pojazdu=self.model_a4,
            tytul='Audi A4 2.0 TFSI',
            opis='Super stan',
            rok_produkcji=2018,
            przebieg_km=110000,
            paliwo=Paliwo.BENZYNA,
            skrzynia=SkrzyniaBiegow.MANUALNA,
            nadwozie=TypNadwozia.KOMBI,
            kolor='Srebrny',
            lokalizacja='Kraków',
            cena=Decimal('75000.00'),
            status=StatusOgloszenia.AKTYWNE,
            data_wygasniecia=timezone.now() + timedelta(days=30),
        )

        # Filtrowanie po marce BMW
        wyszukiwarka = WyszukiwarkaOgloszen({'marka': self.marka_bmw})
        wyniki = wyszukiwarka.wyszukaj()
        self.assertEqual(wyniki.count(), 1)
        self.assertEqual(wyniki.first().model_pojazdu.marka.nazwa, 'BMW')

        # Filtrowanie po cenie do 100 000 zł
        wyszukiwarka_cena = WyszukiwarkaOgloszen({'cena_do': Decimal('100000.00')})
        wyniki_cena = wyszukiwarka_cena.wyszukaj()
        self.assertEqual(wyniki_cena.count(), 1)
        self.assertEqual(wyniki_cena.first().model_pojazdu.marka.nazwa, 'Audi')

        # Błędny zakres: cena_od > cena_do
        wyszukiwarka_blad = WyszukiwarkaOgloszen({
            'cena_od': Decimal('150000.00'),
            'cena_do': Decimal('50000.00')
        })
        wyniki_blad = wyszukiwarka_blad.wyszukaj()
        self.assertEqual(wyniki_blad.count(), 0)
        self.assertIn('cena_od', wyszukiwarka_blad.bledy)

    def test_porownywarka_limit_3_pojazdow(self):
        sesja = {}
        por = Porownywarka(sesja)

        self.assertTrue(por.dodaj(101))
        self.assertTrue(por.dodaj(102))
        self.assertTrue(por.dodaj(103))
        # Czwarty samochód odrzucony ze względu na limit 3
        self.assertFalse(por.dodaj(104))
        self.assertEqual(len(por.lista_id), 3)

        # Usunięcie
        por.usun(102)
        self.assertEqual(len(por.lista_id), 2)
        self.assertNotIn(102, por.lista_id)

    def test_komenda_wygas_ogloszenia(self):
        # Ogłoszenie z przeszłą datą ważności
        self.ogloszenie.data_wygasniecia = timezone.now() - timedelta(days=2)
        self.ogloszenie.save()

        call_command('wygas_ogloszenia')

        self.ogloszenie.refresh_from_db()
        self.assertEqual(self.ogloszenie.status, StatusOgloszenia.WYGASLE)
