from django.test import TestCase
from decimal import Decimal
from django.core.exceptions import PermissionDenied
from django.core import mail

from konta.models import Uzytkownik, RolaUzytkownika
from ogloszenia.models import Marka, ModelPojazdu, Ogloszenie, StatusOgloszenia, Paliwo, SkrzyniaBiegow, TypNadwozia
from zamowienia.models import Zamowienie, StatusZamowienia, Ocena
from zamowienia.services import SerwisZamowien
from zamowienia.exceptions import NiedozwolonaOperacjaZamowienia

class TestZamowienia(TestCase):
    def setUp(self):
        self.sprzedawca = Uzytkownik.objects.create_user(
            username='sprzedawca_z',
            email='sprzedawca@z.pl',
            password='Password123!',
            rola=RolaUzytkownika.SPRZEDAWCA
        )
        self.kupujacy = Uzytkownik.objects.create_user(
            username='kupujacy_z',
            email='kupujacy@z.pl',
            password='Password123!',
            rola=RolaUzytkownika.KUPUJACY
        )
        self.inny_kupujacy = Uzytkownik.objects.create_user(
            username='inny_z',
            email='inny@z.pl',
            password='Password123!',
            rola=RolaUzytkownika.KUPUJACY
        )

        marka = Marka.objects.create(nazwa='Toyota')
        model = ModelPojazdu.objects.create(marka=marka, nazwa='Yaris')
        self.ogloszenie = Ogloszenie.objects.create(
            sprzedawca=self.sprzedawca,
            model_pojazdu=model,
            tytul='Toyota Yaris 1.5 Hybrid',
            opis='Ekonomiczne auto miejskie',
            rok_produkcji=2021,
            przebieg_km=30000,
            paliwo=Paliwo.HYBRYDA,
            skrzynia=SkrzyniaBiegow.AUTOMATYCZNA,
            nadwozie=TypNadwozia.HATCHBACK,
            kolor='Czerwony',
            lokalizacja='Łódź',
            cena=Decimal('69900.00'),
            status=StatusOgloszenia.AKTYWNE
        )

    def test_zlozenie_zamowienia_rezerwacja(self):
        zamowienie = SerwisZamowien.zloz_zamowienie(
            kupujacy=self.kupujacy,
            ogloszenie_id=self.ogloszenie.id,
            uwagi='Odbiór w sobotę rano'
        )

        self.assertEqual(zamowienie.status, StatusZamowienia.ZLOZONE)
        self.assertEqual(zamowienie.cena, Decimal('69900.00'))

        self.ogloszenie.refresh_from_db()
        self.assertEqual(self.ogloszenie.status, StatusOgloszenia.ZAREZERWOWANE)

        # Powiadomienie e-mail poszło do sprzedawcy
        self.assertTrue(len(mail.outbox) > 0)

    def test_blokada_zakupu_wlasnego_ogloszenia(self):
        with self.assertRaises(PermissionDenied):
            SerwisZamowien.zloz_zamowienie(
                kupujacy=self.sprzedawca,
                ogloszenie_id=self.ogloszenie.id
            )

    def test_blokada_podwojnej_rezerwacji(self):
        # Pierwsza rezerwacja
        SerwisZamowien.zloz_zamowienie(
            kupujacy=self.kupujacy,
            ogloszenie_id=self.ogloszenie.id
        )

        # Druga rezerwacja przez innego kupującego musi zostać odrzucona
        with self.assertRaises(NiedozwolonaOperacjaZamowienia):
            SerwisZamowien.zloz_zamowienie(
                kupujacy=self.inny_kupujacy,
                ogloszenie_id=self.ogloszenie.id
            )

    def test_pelny_cykl_transakcji_i_ocena(self):
        # 1. Złożenie zamówienia
        zamowienie = SerwisZamowien.zloz_zamowienie(
            kupujacy=self.kupujacy,
            ogloszenie_id=self.ogloszenie.id
        )

        # 2. Akceptacja przez sprzedawcę
        zamowienie = SerwisZamowien.akceptuj(self.sprzedawca, zamowienie.id)
        self.assertEqual(zamowienie.status, StatusZamowienia.ZAAKCEPTOWANE)
        self.ogloszenie.refresh_from_db()
        self.assertEqual(self.ogloszenie.status, StatusOgloszenia.SPRZEDANE)

        # 3. Potwierdzenie odbioru przez kupującego
        zamowienie = SerwisZamowien.potwierdz_odbior(self.kupujacy, zamowienie.id)
        self.assertEqual(zamowienie.status, StatusZamowienia.ZAKONCZONE)
        self.assertTrue(zamowienie.czy_mozna_ocenic())

        # 4. Wystawienie oceny
        ocena = SerwisZamowien.wystaw_ocene(
            kupujacy=self.kupujacy,
            zamowienie_id=zamowienie.id,
            liczba_gwiazdek=5,
            komentarz='Wszystko w jak najlepszym porządku!'
        )
        self.assertEqual(ocena.liczba_gwiazdek, 5)
        self.assertEqual(self.sprzedawca.srednia_ocen(), 5.0)

        # 5. Nie można ocenić po raz drugi
        with self.assertRaises(NiedozwolonaOperacjaZamowienia):
            SerwisZamowien.wystaw_ocene(
                kupujacy=self.kupujacy,
                zamowienie_id=zamowienie.id,
                liczba_gwiazdek=4,
                komentarz='Próba dubla'
            )

    def test_odrzucenie_i_powrot_ogloszenia_do_aktywnych(self):
        zamowienie = SerwisZamowien.zloz_zamowienie(
            kupujacy=self.kupujacy,
            ogloszenie_id=self.ogloszenie.id
        )

        SerwisZamowien.odrzuc(self.sprzedawca, zamowienie.id, 'Brak kontaktu')
        zamowienie.refresh_from_db()
        self.assertEqual(zamowienie.status, StatusZamowienia.ODRZUCONE)

        self.ogloszenie.refresh_from_db()
        self.assertEqual(self.ogloszenie.status, StatusOgloszenia.AKTYWNE)

    def test_anulowanie_przez_kupujacego(self):
        zamowienie = SerwisZamowien.zloz_zamowienie(
            kupujacy=self.kupujacy,
            ogloszenie_id=self.ogloszenie.id
        )

        SerwisZamowien.anuluj(self.kupujacy, zamowienie.id)
        zamowienie.refresh_from_db()
        self.assertEqual(zamowienie.status, StatusZamowienia.ANULOWANE)

        self.ogloszenie.refresh_from_db()
        self.assertEqual(self.ogloszenie.status, StatusOgloszenia.AKTYWNE)
