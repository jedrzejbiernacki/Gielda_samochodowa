# Giełda Samochodowa

Kompletna implementacja backendowa internetowego serwisu ogłoszeniowego „Giełda samochodowa”, zrealizowana zgodnie ze specyfikacją projektową zawartą w dokumentacji:
- `ibd-3.pdf` – Etap 1: Przygotowanie i uzasadnienie potrzeby realizacji. Analiza problemu.
- `ibd2-3.pdf` – Etap 2: Faza projektowa.

Projekt zrealizowano w języku **Python 3.12** z wykorzystaniem frameworka **Django 5.2 LTS**, bazy danych **MySQL 8.0** oraz środowiska kontenerowego **Docker Compose**.

---

## 1. Architektura systemu

System zaprojektowano w **architekturze trójwarstwowej** podzielonej na 5 wyspecjalizowanych aplikacji Django:
1. **Warstwa prezentacji**: Szablony Django (`templates/`), Bootstrap 5, skrypt `static/js/gielda.js`, arkusz `static/css/style.css`.
2. **Warstwa logiki**: Widoki (`views.py`), formularze (`forms.py`), klasy usług biznesowych (`services.py`), system uprawnień (`mixins.py`, `backends.py`).
3. **Warstwa danych**: Modele ORM (`models.py`), migracje schematu i baza MySQL 8 (lub SQLite do testów).

### Podział na moduły:
- **`config`** – Konfiguracja globalna projektu, routing URL, obsługa procesorów kontekstu.
- **`konta`** – Model `Uzytkownik` rozszerzający `AbstractUser` z rolami (`KUPUJACY`, `SPRZEDAWCA`, `KOMIS`), autoryzacją `SprzedawcaWymaganyMixin`, backendem `KontaAuthBackend` blokującym zablokowane konta oraz publicznym profilem sprzedawcy.
- **`ogloszenia`** – Słowniki `Marka` i `ModelPojazdu`, model `Ogloszenie` z pełnym cyklem życia i diagramem stanów, `Zdjecie` (do 10 zdjęć, walidacja do 5 MB), `Ulubione`, usługa wyszukiwarki `WyszukiwarkaOgloszen` oraz sesyjna `Porownywarka` (do 3 aut obok siebie).
- **`wiadomosci`** – Model `Wiadomosc` w wątkach `(ogloszenie, kupujacy)` ze złożonym indeksem bazy danych oraz usługa `SerwisPowiadomien` (wysyłka powiadomień e-mail).
- **`zamowienia`** – Model `Zamowienie` ze statusem rezerwacji i zamrożoną ceną, model `Ocena` (1–5 gwiazdek), usługa `SerwisZamowien` realizująca transakcje z blokadą wierszy (`SELECT ... FOR UPDATE`).

---

## 2. Konta demonstracyjne (po zasileniu danymi)

Uruchomienie polecenia `python manage.py przygotuj_dane` tworzy konta testowe:

| Rola | Login | Hasło | Opis |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin` | `Admin1234!` | Dostęp do `/admin/`, moderacja ogłoszeń i blokowanie kont |
| **Komis samochodowy** | `komis_premium` | `Komis1234!` | Premium Auto Centrum Warszawa |
| **Sprzedawca prywatny** | `sprzedawca_jan` | `Jan12345!` | Jan Kowalski (Kraków) |
| **Kupujący** | `kupujacy_adam` | `Adam1234!` | Adam Nowak (Wrocław) |

---

## 3. Uruchomienie lokalne

### Krok 1: Wirtualne środowisko i instalacja zależności
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Krok 2: Migracje i zasilenie bazy danymi testowymi
```bash
python manage.py migrate
python manage.py przygotuj_dane
```

### Krok 3: Uruchomienie serwera deweloperskiego
```bash
python manage.py runserver
```
Aplikacja będzie dostępna pod adresem: `http://127.0.0.1:8000/`

---

## 4. Uruchomienie w kontenerach Docker Compose

Zgodnie z Rozdziałem 10 środowisko składa się z 3 kontenerów:
- `db` – Baza MySQL 8.0 z kodowaniem `utf8mb4` i collation `utf8mb4_polish_ci`.
- `web` – Aplikacja Django z serwerem WSGI Gunicorn.
- `nginx` – Serwer Nginx 1.27 wystawiający aplikację na porcie `8080`, serwujący pliki `/static/` i `/media/`.

```bash
docker compose up --build
```
Aplikacja będzie dostępna pod adresem: `http://localhost:8080/`

---

## 5. Dedykowane polecenia zarządzające (Management Commands)

- **`python manage.py przygotuj_dane`** – Automatyczne zasilenie bazy markami, modelami, użytkownikami, ogłoszeniami, zdjęciami SVG, wątkami wiadomości oraz zakończonymi zamówieniami z ocenami.
- **`python manage.py wygas_ogloszenia`** – Realizacja wymagania **WF-17**: automatyczne wygaszanie ofert, których data ważności minęła (> 30 dni).

---

## 6. Uruchomienie testów jednostkowych

Wszystkie moduły posiadają zestaw testów automatycznych (`Django TestCase`) weryfikujących reguły biznesowe, walidację, cykl życia ofert oraz współbieżność zamówień:

```bash
python manage.py test
```
