from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import View, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.db.models import Max, Q
from django.urls import reverse

from ogloszenia.models import Ogloszenie
from .models import Wiadomosc
from .forms import WiadomoscForm
from .services import SerwisPowiadomien

class SkrzynkaView(LoginRequiredMixin, View):
    """Skrzynka odbiorcza – lista unikalnych wątków korespondencji."""
    def get(self, request):
        uzytkownik = request.user
        # Wątki, w których użytkownik jest nadawcą lub odbiorcą
        wiadomosci_qs = Wiadomosc.objects.filter(
            Q(nadawca=uzytkownik) | Q(odbiorca=uzytkownik)
        ).select_related('ogloszenie', 'kupujacy', 'nadawca', 'odbiorca', 'ogloszenie__sprzedawca')

        # Grupowanie po unikalnych parach (ogloszenie_id, kupujacy_id)
        pary = wiadomosci_qs.values_list('ogloszenie_id', 'kupujacy_id').distinct()

        watki = []
        for ogl_id, kup_id in pary:
            ostatnia = Wiadomosc.objects.filter(
                ogloszenie_id=ogl_id, kupujacy_id=kup_id
            ).select_related('ogloszenie', 'nadawca', 'odbiorca', 'ogloszenie__sprzedawca').latest('data_wyslania')

            ogloszenie = ostatnia.ogloszenie
            rozmowca = ogloszenie.sprzedawca if uzytkownik == ostatnia.kupujacy else ostatnia.kupujacy
            nieprzeczytane = Wiadomosc.objects.filter(
                ogloszenie_id=ogl_id,
                kupujacy_id=kup_id,
                odbiorca=uzytkownik,
                przeczytana=False
            ).count()

            watki.append({
                'ogloszenie': ogloszenie,
                'kupujacy_id': kup_id,
                'rozmowca': rozmowca,
                'ostatnia_wiadomosc': ostatnia,
                'nieprzeczytane': nieprzeczytane,
            })

        # Sortowanie wątków według czasu ostatniej wiadomości
        watki.sort(key=lambda w: w['ostatnia_wiadomosc'].data_wyslania, reverse=True)

        return render(request, 'wiadomosci/skrzynka.html', {'watki': watki})


class WatekView(LoginRequiredMixin, View):
    """Rozmowa w wątku dotyczącym danego ogłoszenia i kupującego."""
    def sprawdz_dostep(self, request, ogloszenie_id, kupujacy_id):
        ogloszenie = get_object_or_404(
            Ogloszenie.objects.select_related('sprzedawca', 'model_pojazdu', 'model_pojazdu__marka'),
            pk=ogloszenie_id
        )
        if request.user.id not in (ogloszenie.sprzedawca_id, kupujacy_id) and not request.user.is_staff:
            raise PermissionDenied('Nie masz dostępu do tego wątku wiadomości.')
        return ogloszenie

    def get(self, request, ogloszenie_id, kupujacy_id):
        ogloszenie = self.sprawdz_dostep(request, ogloszenie_id, kupujacy_id)

        # Oznaczenie wiadomości skierowanych do bieżącego użytkownika jako przeczytane
        Wiadomosc.objects.filter(
            ogloszenie_id=ogloszenie_id,
            kupujacy_id=kupujacy_id,
            odbiorca=request.user,
            przeczytana=False
        ).update(przeczytana=True)

        wiadomosci_list = Wiadomosc.objects.filter(
            ogloszenie_id=ogloszenie_id,
            kupujacy_id=kupujacy_id
        ).select_related('nadawca', 'odbiorca').order_by('data_wyslania')

        odbiorca = ogloszenie.sprzedawca if request.user.id == kupujacy_id else wiadomosci_list.first().kupujacy if wiadomosci_list.exists() else get_object_or_404(ogloszenie.sprzedawca.__class__, pk=kupujacy_id)

        form = WiadomoscForm()
        return render(request, 'wiadomosci/watek.html', {
            'ogloszenie': ogloszenie,
            'kupujacy_id': kupujacy_id,
            'odbiorca': odbiorca,
            'wiadomosci_list': wiadomosci_list,
            'form': form,
        })

    def post(self, request, ogloszenie_id, kupujacy_id):
        ogloszenie = self.sprawdz_dostep(request, ogloszenie_id, kupujacy_id)
        form = WiadomoscForm(request.POST)

        if form.is_valid():
            wiadomosc = form.save(commit=False)
            wiadomosc.ogloszenie = ogloszenie
            wiadomosc.nadawca = request.user

            from konta.models import Uzytkownik
            kupujacy = get_object_or_404(Uzytkownik, pk=kupujacy_id)
            wiadomosc.kupujacy = kupujacy

            # Ustalenie odbiorcy: jeśli pisze kupujący -> trafia do sprzedawcy; jeśli sprzedawca -> do kupującego
            if request.user.id == kupujacy_id:
                wiadomosc.odbiorca = ogloszenie.sprzedawca
            else:
                wiadomosc.odbiorca = kupujacy

            wiadomosc.save()
            SerwisPowiadomien.powiadom_o_nowej_wiadomosci(wiadomosc)
            messages.success(request, 'Wiadomość została wysłana.')
            return redirect('wiadomosci:watek', ogloszenie_id=ogloszenie_id, kupujacy_id=kupujacy_id)

        wiadomosci_list = Wiadomosc.objects.filter(
            ogloszenie_id=ogloszenie_id,
            kupujacy_id=kupujacy_id
        ).select_related('nadawca', 'odbiorca').order_by('data_wyslania')
        return render(request, 'wiadomosci/watek.html', {
            'ogloszenie': ogloszenie,
            'kupujacy_id': kupujacy_id,
            'wiadomosci_list': wiadomosci_list,
            'form': form,
        })


class NowaWiadomoscView(LoginRequiredMixin, View):
    """Rozpoczęcie wątku ze sprzedawcą ze strony szczegółów ogłoszenia."""
    def get(self, request, ogloszenie_id):
        ogloszenie = get_object_or_404(Ogloszenie, pk=ogloszenie_id)
        if ogloszenie.sprzedawca == request.user:
            messages.warning(request, 'Nie możesz wysłać wiadomości do samego siebie w sprawie własnego ogłoszenia.')
            return redirect('ogloszenia:szczegoly', pk=ogloszenie_id)

        # Otwarcie wątku pomiędzy bieżącym kupującym a sprzedawcą tego ogłoszenia
        return redirect('wiadomosci:watek', ogloszenie_id=ogloszenie_id, kupujacy_id=request.user.id)
