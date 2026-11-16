from django.test import TestCase, Client
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from konta.models import Uzytkownik, RolaUzytkownika
from konta.forms import RejestracjaForm

class TestKonta(TestCase):
    def setUp(self):
        self.kupujacy = Uzytkownik.objects.create_user(
            username='kupujacy1',
            email='kupujacy1@example.com',
            password='Password123!',
            rola=RolaUzytkownika.KUPUJACY,
            first_name='Jan',
            last_name='Kowalski'
        )
        self.sprzedawca = Uzytkownik.objects.create_user(
            username='sprzedawca1',
            email='sprzedawca1@example.com',
            password='Password123!',
            rola=RolaUzytkownika.SPRZEDAWCA,
            first_name='Piotr',
            last_name='Nowak'
        )
        self.komis = Uzytkownik.objects.create_user(
            username='komis1',
            email='komis1@example.com',
            password='Password123!',
            rola=RolaUzytkownika.KOMIS,
            nazwa_firmy='Auto Hit Sp. z o.o.',
            first_name='Marek',
            last_name='Zieliński'
        )

    def test_czy_sprzedawca_role(self):
        self.assertFalse(self.kupujacy.czy_sprzedawca())
        self.assertTrue(self.sprzedawca.czy_sprzedawca())
        self.assertTrue(self.komis.czy_sprzedawca())

    def test_nazwa_wyswietlana(self):
        self.assertEqual(self.komis.nazwa_wyswietlana(), 'Auto Hit Sp. z o.o.')
        self.assertEqual(self.kupujacy.nazwa_wyswietlana(), 'Jan Kowalski')

    def test_walidacja_nazwy_firmy_dla_komisu(self):
        dane_brak_firmy = {
            'username': 'nowykomis',
            'email': 'nowy@komis.pl',
            'first_name': 'Adam',
            'last_name': 'Test',
            'rola': RolaUzytkownika.KOMIS,
            'nazwa_firmy': '',
            'password1': 'Haslo12345!',
            'password2': 'Haslo12345!',
        }
        form = RejestracjaForm(data=dane_brak_firmy)
        self.assertFalse(form.is_valid())
        self.assertIn('nazwa_firmy', form.errors)

    def test_blokada_logowania_zablokowanego_konta(self):
        self.kupujacy.zablokowany = True
        self.kupujacy.save()

        client = Client()
        login_sukces = client.login(username='kupujacy1', password='Password123!')
        self.assertFalse(login_sukces)

    def test_dostęp_sprzedawca_wymagany_mixin(self):
        client = Client()
        # Kupujący próbuje wejść na formularz dodawania ogłoszenia -> 403 Forbidden
        client.force_login(self.kupujacy)
        response = client.get(reverse('ogloszenia:dodaj'))
        self.assertEqual(response.status_code, 403)

        # Sprzedawca ma dostęp -> 200 OK
        client.force_login(self.sprzedawca)
        response = client.get(reverse('ogloszenia:dodaj'))
        self.assertEqual(response.status_code, 200)
