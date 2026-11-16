from datetime import timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse
from django.template.exceptions import TemplateDoesNotExist
from django.core.exceptions import PermissionDenied

from konta.mixins import SprzedawcaWymaganyMixin
from ogloszenia.models import Ogloszenie, StatusOgloszenia
from .models import Cennik, OplataZaOgloszenie, Wyroznienie, TypOplaty
from .services import SymulacjaOplaty


class OplacOgloszenieView(LoginRequiredMixin, SprzedawcaWymaganyMixin, View):
    """Widok uiszczenia opłaty za publikację ogłoszenia ponad darmowy limit."""

    def get(self, request, pk):
        ogloszenie = get_object_or_404(Ogloszenie, pk=pk)
        if ogloszenie.sprzedawca != request.user and not request.user.is_staff:
            raise PermissionDenied('Nie masz uprawnień do tego ogłoszenia.')

        cennik = Cennik.load()
        kwota = cennik.cena_dodatkowe_ogloszenie
        kontekst = {
            'ogloszenie': ogloszenie,
            'kwota': kwota,
            'cennik': cennik,
        }
        try:
            return render(request, 'platnosci/oplac.html', kontekst)
        except TemplateDoesNotExist:
            return HttpResponse(f"Opłata za dodatkowe ogłoszenie: {kwota} zł")

    def post(self, request, pk):
        ogloszenie = get_object_or_404(Ogloszenie, pk=pk)
        if ogloszenie.sprzedawca != request.user and not request.user.is_staff:
            raise PermissionDenied('Nie masz uprawnień do tego ogłoszenia.')

        cennik = Cennik.load()
        kwota = cennik.cena_dodatkowe_ogloszenie

        oplata = OplataZaOgloszenie.objects.create(
            uzytkownik=request.user,
            ogloszenie=ogloszenie,
            kwota=kwota,
            typ_oplaty=TypOplaty.DODATKOWE_OGLOSZENIE,
            oplacone=False
        )

        symulacja = SymulacjaOplaty()
        symulacja.przetworz_oplate(oplata.pk)

        if ogloszenie.status in (StatusOgloszenia.SZKIC, StatusOgloszenia.WYGASLE):
            ogloszenie.opublikuj()
        else:
            ogloszenie.status = StatusOgloszenia.AKTYWNE
            ogloszenie.save(update_fields=['status', 'data_aktualizacji'])

        messages.success(request, 'Opłata została pomyślnie uiszczona. Ogłoszenie zostało aktywowane!')
        return redirect('ogloszenia:szczegoly', pk=ogloszenie.pk)


class WyroznijOgloszenieView(LoginRequiredMixin, View):
    """Widok wyróżnienia ogłoszenia na okres 7 lub 30 dni."""

    def get(self, request, pk):
        ogloszenie = get_object_or_404(Ogloszenie, pk=pk)
        if ogloszenie.sprzedawca != request.user and not request.user.is_staff:
            raise PermissionDenied('Nie masz uprawnień do tego ogłoszenia.')

        cennik = Cennik.load()
        kontekst = {
            'ogloszenie': ogloszenie,
            'cennik': cennik,
        }
        try:
            return render(request, 'platnosci/wyroznij.html', kontekst)
        except TemplateDoesNotExist:
            return HttpResponse(f"Wyróżnienie ogłoszenia: {ogloszenie.tytul}")

    def post(self, request, pk):
        ogloszenie = get_object_or_404(Ogloszenie, pk=pk)
        if ogloszenie.sprzedawca != request.user and not request.user.is_staff:
            raise PermissionDenied('Nie masz uprawnień do tego ogłoszenia.')

        cennik = Cennik.load()
        wariant = request.POST.get('dni') or request.POST.get('wariant')
        if str(wariant) in ('30', '30dni'):
            dni = 30
            kwota = cennik.cena_wyroznienie_30dni
        else:
            dni = 7
            kwota = cennik.cena_wyroznienie_7dni

        teraz = timezone.now()
        data_zakonczenia = teraz + timedelta(days=dni)

        oplata = OplataZaOgloszenie.objects.create(
            uzytkownik=request.user,
            ogloszenie=ogloszenie,
            kwota=kwota,
            typ_oplaty=TypOplaty.WYROZNIENIE,
            oplacone=False
        )

        symulacja = SymulacjaOplaty()
        symulacja.przetworz_oplate(oplata.pk)
        oplata.data_waznosci = data_zakonczenia
        oplata.save(update_fields=['data_waznosci'])

        Wyroznienie.objects.update_or_create(
            ogloszenie=ogloszenie,
            defaults={
                'oplata': oplata,
                'data_rozpoczecia': teraz,
                'data_zakonczenia': data_zakonczenia,
            }
        )

        ogloszenie.wyroznione = True
        ogloszenie.save(update_fields=['wyroznione', 'data_aktualizacji'])

        messages.success(request, f'Ogłoszenie zostało pomyślnie wyróżnione na {dni} dni!')
        return redirect('ogloszenia:szczegoly', pk=ogloszenie.pk)


class HistoriaOplatView(LoginRequiredMixin, ListView):
    """Widok listy historii płatności bieżącego użytkownika."""
    model = OplataZaOgloszenie
    template_name = 'platnosci/historia.html'
    context_object_name = 'oplaty'

    def get_queryset(self):
        return OplataZaOgloszenie.objects.filter(
            uzytkownik=self.request.user
        ).select_related('ogloszenie').order_by('-data_utworzenia')

    def render_to_response(self, context, **response_kwargs):
        try:
            return super().render_to_response(context, **response_kwargs)
        except TemplateDoesNotExist:
            return HttpResponse("Historia opłat użytkownika")
