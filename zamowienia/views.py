from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import View, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.urls import reverse

from konta.mixins import SprzedawcaWymaganyMixin
from ogloszenia.models import Ogloszenie
from .models import Zamowienie, StatusZamowienia
from .forms import ZlozZamowienieForm, OdrzucZamowienieForm, OcenaForm
from .services import SerwisZamowien
from .exceptions import NiedozwolonaOperacjaZamowienia

class ZlozZamowienieView(LoginRequiredMixin, View):
    """Formularz i obsługa złożenia zamówienia (rezerwacji) wybranego samochodu."""
    def get(self, request, pk):
        ogloszenie = get_object_or_404(
            Ogloszenie.objects.select_related('model_pojazdu', 'model_pojazdu__marka', 'sprzedawca'),
            pk=pk
        )
        if ogloszenie.sprzedawca == request.user:
            messages.error(request, 'Nie możesz złożyć zamówienia na własne ogłoszenie.')
            return redirect('ogloszenia:szczegoly', pk=pk)

        if not ogloszenie.czy_dostepne():
            messages.error(request, 'To ogłoszenie nie jest obecnie dostępne do rezerwacji.')
            return redirect('ogloszenia:szczegoly', pk=pk)

        form = ZlozZamowienieForm()
        return render(request, 'zamowienia/zloz.html', {'ogloszenie': ogloszenie, 'form': form})

    def post(self, request, pk):
        ogloszenie = get_object_or_404(Ogloszenie, pk=pk)
        form = ZlozZamowienieForm(request.POST)

        if form.is_valid():
            try:
                zamowienie = SerwisZamowien.zloz_zamowienie(
                    kupujacy=request.user,
                    ogloszenie_id=pk,
                    uwagi=form.cleaned_data.get('uwagi', '')
                )
                messages.success(
                    request,
                    f'Pomyślnie złożono rezerwację na pojazd „{ogloszenie.tytul}”. Powiadomiliśmy sprzedawcę.'
                )
                return redirect('zamowienia:moje')
            except (NiedozwolonaOperacjaZamowienia, PermissionDenied) as e:
                messages.error(request, str(e))
                return redirect('ogloszenia:szczegoly', pk=pk)

        return render(request, 'zamowienia/zloz.html', {'ogloszenie': ogloszenie, 'form': form})


class MojeZamowieniaView(LoginRequiredMixin, ListView):
    """Lista zamówień złożonych przez zalogowanego kupującego."""
    model = Zamowienie
    template_name = 'zamowienia/moje.html'
    context_object_name = 'zamowienia'

    def get_queryset(self):
        return Zamowienie.objects.filter(
            kupujacy=self.request.user
        ).select_related('ogloszenie', 'ogloszenie__model_pojazdu', 'ogloszenie__model_pojazdu__marka', 'ogloszenie__sprzedawca').prefetch_related('ogloszenie__zdjecia').order_by('-data_zlozenia')


class OtrzymaneZamowieniaView(SprzedawcaWymaganyMixin, ListView):
    """Lista zamówień otrzymanych przez sprzedawcę."""
    model = Zamowienie
    template_name = 'zamowienia/otrzymane.html'
    context_object_name = 'zamowienia'

    def get_queryset(self):
        return Zamowienie.objects.filter(
            ogloszenie__sprzedawca=self.request.user
        ).select_related('ogloszenie', 'ogloszenie__model_pojazdu', 'ogloszenie__model_pojazdu__marka', 'kupujacy').order_by('-data_zlozenia')


class AkceptujZamowienieView(SprzedawcaWymaganyMixin, View):
    """Akceptacja rezerwacji przez sprzedawcę."""
    def post(self, request, pk):
        try:
            SerwisZamowien.akceptuj(request.user, pk)
            messages.success(request, 'Zamówienie zostało zaakceptowane. Pojazd oznaczono jako sprzedany.')
        except (NiedozwolonaOperacjaZamowienia, PermissionDenied) as e:
            messages.error(request, str(e))
        return redirect('zamowienia:otrzymane')


class OdrzucZamowienieView(SprzedawcaWymaganyMixin, View):
    """Odrzucenie rezerwacji przez sprzedawcę."""
    def post(self, request, pk):
        powod = request.POST.get('uzasadnienie', '')
        try:
            SerwisZamowien.odrzuc(request.user, pk, powod)
            messages.info(request, 'Zamówienie zostało odrzucone. Ogłoszenie powróciło do dostępnych ofert.')
        except (NiedozwolonaOperacjaZamowienia, PermissionDenied) as e:
            messages.error(request, str(e))
        return redirect('zamowienia:otrzymane')


class AnulujZamowienieView(LoginRequiredMixin, View):
    """Anulowanie rezerwacji przez kupującego przed decyzją sprzedawcy."""
    def post(self, request, pk):
        try:
            SerwisZamowien.anuluj(request.user, pk)
            messages.info(request, 'Twoja rezerwacja została anulowana.')
        except (NiedozwolonaOperacjaZamowienia, PermissionDenied) as e:
            messages.error(request, str(e))
        return redirect('zamowienia:moje')


class PotwierdzOdbiorView(LoginRequiredMixin, View):
    """Potwierdzenie odbioru samochodu przez kupującego (zakończenie transakcji)."""
    def post(self, request, pk):
        try:
            SerwisZamowien.potwierdz_odbior(request.user, pk)
            messages.success(
                request,
                'Odbiór pojazdu został potwierdzony! Transakcja została zakończona. Możesz teraz wystawić ocenę sprzedawcy.'
            )
            return redirect('zamowienia:ocen', pk=pk)
        except (NiedozwolonaOperacjaZamowienia, PermissionDenied) as e:
            messages.error(request, str(e))
            return redirect('zamowienia:moje')


class WystawOceneView(LoginRequiredMixin, View):
    """Wystawienie oceny i opinii o sprzedawcy po sfinalizowaniu transakcji."""
    def get(self, request, pk):
        zamowienie = get_object_or_404(
            Zamowienie.objects.select_related('ogloszenie', 'ogloszenie__sprzedawca'),
            pk=pk
        )
        if zamowienie.kupujacy != request.user and not request.user.is_staff:
            raise PermissionDenied('Nie masz uprawnień do wystawienia oceny dla tego zamówienia.')

        if not zamowienie.czy_mozna_ocenic():
            messages.warning(request, 'To zamówienie zostało już ocenione lub nie jest jeszcze zakończone.')
            return redirect('zamowienia:moje')

        form = OcenaForm()
        return render(request, 'zamowienia/ocen.html', {'zamowienie': zamowienie, 'form': form})

    def post(self, request, pk):
        zamowienie = get_object_or_404(Zamowienie, pk=pk)
        form = OcenaForm(request.POST)

        if form.is_valid():
            try:
                SerwisZamowien.wystaw_ocene(
                    kupujacy=request.user,
                    zamowienie_id=pk,
                    liczba_gwiazdek=int(form.cleaned_data['liczba_gwiazdek']),
                    komentarz=form.cleaned_data['komentarz']
                )
                messages.success(request, 'Dziękujemy! Twoja opinia została pomyślnie dodana.')
                return redirect('zamowienia:moje')
            except (NiedozwolonaOperacjaZamowienia, PermissionDenied) as e:
                messages.error(request, str(e))
                return redirect('zamowienia:moje')

        return render(request, 'zamowienia/ocen.html', {'zamowienie': zamowienie, 'form': form})
