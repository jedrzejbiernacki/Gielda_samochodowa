from django.test import TestCase, Client
from django.urls import reverse
from django.core import mail
from decimal import Decimal

from konta.models import Uzytkownik, RolaUzytkownika
from ogloszenia.models import Marka, ModelPojazdu, Ogloszenie, StatusOgloszenia, Paliwo, SkrzyniaBiegow, TypNadwozia
from wiadomosci.models import Wiadomosc
from wiadomosci.services import SerwisPowiadomien

class TestWiadomosci(TestCase):
    def setUp(self):
        self.sprzedawca = Uzytkownik.objects.create_user(
            username='sprzedawca_w',
            email='sprzedawca@w.pl',
            password='Password123!',
            rola=RolaUzytkownika.SPRZEDAWCA
        )
        self.kupujacy = Uzytkownik.objects.create_user(
            username='kupujacy_w',
            email='kupujacy@w.pl',
            password='Password123!',
            rola=RolaUzytkownika.KUPUJACY
        )
        self.inny_uzytkownik = Uzytkownik.objects.create_user(
            username='inny_u',
            email='inny@w.pl',
            password='Password123!',
            rola=RolaUzytkownika.KUPUJACY
        )

        marka = Marka.objects.create(nazwa='Ford')
        model = ModelPojazdu.objects.create(marka=marka, nazwa='Focus')
        self.ogloszenie = Ogloszenie.objects.create(
            sprzedawca=self.sprzedawca,
            model_pojazdu=model,
            tytul='Ford Focus 1.5 EcoBoost',
            opis='Opis auta',
            rok_produkcji=2019,
            przebieg_km=90000,
            paliwo=Paliwo.BENZYNA,
            skrzynia=SkrzyniaBiegow.MANUALNA,
            nadwozie=TypNadwozia.HATCHBACK,
            kolor='Biały',
            lokalizacja='Poznań',
            cena=Decimal('58000.00'),
            status=StatusOgloszenia.AKTYWNE
        )

    def test_wyslanie_wiadomosci_i_powiadomienia_email(self):
        msg = Wiadomosc.objects.create(
            ogloszenie=self.ogloszenie,
            kupujacy=self.kupujacy,
            nadawca=self.kupujacy,
            odbiorca=self.sprzedawca,
            tresc='Dzień dobry, czy cena podlega negocjacji?'
        )

        self.assertFalse(msg.przeczytana)
        msg.oznacz_jako_przeczytana()
        self.assertTrue(msg.przeczytana)

        # Test powiadomienia e-mail
        sukces = SerwisPowiadomien.powiadom_o_nowej_wiadomosci(msg)
        self.assertTrue(sukces)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.sprzedawca.email, mail.outbox[0].to)
        self.assertIn('Nowa wiadomość w sprawie', mail.outbox[0].subject)

    def test_uprawnienia_do_watku(self):
        client = Client()
        url = reverse('wiadomosci:watek', kwargs={
            'ogloszenie_id': self.ogloszenie.id,
            'kupujacy_id': self.kupujacy.id
        })

        # Obcy użytkownik nie ma wglądu w wątek
        client.force_login(self.inny_uzytkownik)
        response = client.get(url)
        self.assertEqual(response.status_code, 403)

        # Kupujący ma wgląd
        client.force_login(self.kupujacy)
        response = client.get(url)
        self.assertEqual(response.status_code, 200)

        # Sprzedawca ma wgląd
        client.force_login(self.sprzedawca)
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
