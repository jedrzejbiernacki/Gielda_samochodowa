from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.db import transaction
from django.db.models import F

from konta.mixins import SprzedawcaWymaganyMixin
from .models import Ogloszenie, Marka, ModelPojazdu, Zdjecie, Ulubione, StatusOgloszenia
from .forms import FiltryOgloszenForm, OgloszenieForm, ZdjecieUploadForm
from .services import WyszukiwarkaOgloszen, Porownywarka
from .exceptions import NiedozwolonaZmianaStatusu

class ListaOgloszenView(ListView):
    """Lista ogłoszeń z wyszukiwarką, filtrami i stronicowaniem (12 na stronę)."""
    model = Ogloszenie
    template_name = 'ogloszenia/lista.html'
    context_object_name = 'ogloszenia'
    paginate_by = 12

    def get_queryset(self):
        self.formularz_filtrow = FiltryOgloszenForm(self.request.GET or None)
        if self.formularz_filtrow.is_valid():
            wyszukiwarka = WyszukiwarkaOgloszen(self.formularz_filtrow.cleaned_data)
            return wyszukiwarka.wyszukaj()
        return Ogloszenie.objects.filter(
            status=StatusOgloszenia.AKTYWNE,
            sprzedawca__zablokowany=False
        ).select_related('model_pojazdu', 'model_pojazdu__marka', 'sprzedawca').prefetch_related('zdjecia')

    def get_context_data(self, **kwargs):
        kontekst = super().get_context_data(**kwargs)
        kontekst['formularz_filtrow'] = self.formularz_filtrow
        get_params = self.request.GET.copy()
        if 'page' in get_params:
            get_params.pop('page')
        kontekst['parametry_url'] = get_params.urlencode()
        return kontekst


class SzczegolyOgloszeniaView(DetailView):
    """Szczegóły ogłoszenia, galeria zdjęć, dane sprzedawcy ze średnią ocen."""
    model = Ogloszenie
    template_name = 'ogloszenia/szczegoly.html'
    context_object_name = 'ogloszenie'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        Ogloszenie.objects.filter(pk=obj.pk).update(liczba_wyswietlen=F('liczba_wyswietlen') + 1)
        obj.refresh_from_db(fields=['liczba_wyswietlen'])
        return obj

    def get_context_data(self, **kwargs):
        kontekst = super().get_context_data(**kwargs)
        ogloszenie = self.object
        kontekst['zdjecia'] = ogloszenie.zdjecia.all()
        porownywarka = Porownywarka(self.request.session)
        kontekst['w_porownywarce'] = porownywarka.zawiera(ogloszenie.id)

        czy_ulubione = False
        if self.request.user.is_authenticated:
            czy_ulubione = Ulubione.objects.filter(
                uzytkownik=self.request.user,
                ogloszenie=ogloszenie
            ).exists()
        kontekst['czy_ulubione'] = czy_ulubione
        return kontekst


class DodajOgloszenieView(SprzedawcaWymaganyMixin, View):
    """Formularz dodawania nowego ogłoszenia ze zdjęciami i opcją zapisu jako szkic."""
    def get(self, request):
        form = OgloszenieForm()
        zdjecia_form = ZdjecieUploadForm()
        return render(request, 'ogloszenia/dodaj.html', {'form': form, 'zdjecia_form': zdjecia_form})

    def post(self, request):
        form = OgloszenieForm(request.POST)
        zdjecia_form = ZdjecieUploadForm(request.POST, request.FILES)

        if form.is_valid() and zdjecia_form.is_valid():
            ogloszenie = form.save(commit=False)
            ogloszenie.sprzedawca = request.user

            if 'zapisz_jako_szkic' in request.POST:
                ogloszenie.status = StatusOgloszenia.SZKIC
            else:
                ogloszenie.status = StatusOgloszenia.AKTYWNE

            ogloszenie.save()

            pliki = request.FILES.getlist('zdjecia')[:10]
            for kolejnosc, plik in enumerate(pliki):
                Zdjecie.objects.create(ogloszenie=ogloszenie, plik=plik, kolejnosc=kolejnosc)

            komunikat = 'Ogłoszenie zostało zapisane jako szkic.' if ogloszenie.status == StatusOgloszenia.SZKIC else 'Ogłoszenie zostało pomyślnie opublikowane!'
            messages.success(request, komunikat)
            return redirect('ogloszenia:szczegoly', pk=ogloszenie.pk)

        return render(request, 'ogloszenia/dodaj.html', {'form': form, 'zdjecia_form': zdjecia_form})


class EdytujOgloszenieView(LoginRequiredMixin, View):
    """Edycja ogłoszenia i zarządzanie zdjęciami przez właściciela."""
    def get_ogloszenie(self, request, pk):
        ogloszenie = get_object_or_404(Ogloszenie, pk=pk)
        if ogloszenie.sprzedawca != request.user and not request.user.is_staff:
            raise PermissionDenied('Nie masz uprawnień do edycji tego ogłoszenia.')
        return ogloszenie

    def get(self, request, pk):
        ogloszenie = self.get_ogloszenie(request, pk)
        form = OgloszenieForm(instance=ogloszenie)
        zdjecia_form = ZdjecieUploadForm()
        return render(request, 'ogloszenia/edytuj.html', {
            'form': form,
            'zdjecia_form': zdjecia_form,
            'ogloszenie': ogloszenie
        })

    def post(self, request, pk):
        ogloszenie = self.get_ogloszenie(request, pk)
        form = OgloszenieForm(request.POST, instance=ogloszenie)
        zdjecia_form = ZdjecieUploadForm(request.POST, request.FILES)

        usun_zdjecia_ids = request.POST.getlist('usun_zdjecie')
        if usun_zdjecia_ids:
            ogloszenie.zdjecia.filter(id__in=usun_zdjecia_ids).delete()

        if form.is_valid() and zdjecia_form.is_valid():
            ogloszenie = form.save()

            aktualna_liczba = ogloszenie.zdjecia.count()
            dostepny_limit = max(0, 10 - aktualna_liczba)
            nowe_pliki = request.FILES.getlist('zdjecia')[:dostepny_limit]
            for i, plik in enumerate(nowe_pliki):
                Zdjecie.objects.create(
                    ogloszenie=ogloszenie,
                    plik=plik,
                    kolejnosc=aktualna_liczba + i
                )

            messages.success(request, 'Ogłoszenie zostało zaktualizowane.')
            return redirect('ogloszenia:szczegoly', pk=ogloszenie.pk)

        return render(request, 'ogloszenia/edytuj.html', {
            'form': form,
            'zdjecia_form': zdjecia_form,
            'ogloszenie': ogloszenie
        })


class UsunOgloszenieView(LoginRequiredMixin, View):
    """Usunięcie ogłoszenia (blokowane, gdy istnieją powiązane zamówienia)."""
    def post(self, request, pk):
        ogloszenie = get_object_or_404(Ogloszenie, pk=pk)
        if ogloszenie.sprzedawca != request.user and not request.user.is_staff:
            raise PermissionDenied('Nie masz uprawnień do usunięcia tego ogłoszenia.')

        if ogloszenie.zamowienia.exists():
            messages.error(
                request,
                'Nie można usunąć ogłoszenia, do którego istnieją zamówienia (historia transakcji jest chroniona).'
            )
            return redirect('ogloszenia:moje_ogloszenia')

        ogloszenie.delete()
        messages.success(request, 'Ogłoszenie zostało usunięte.')
        return redirect('ogloszenia:moje_ogloszenia')


class PrzedluzOgloszenieView(LoginRequiredMixin, View):
    """Przedłużenie ważności ogłoszenia o kolejne 30 dni."""
    def post(self, request, pk):
        ogloszenie = get_object_or_404(Ogloszenie, pk=pk)
        if ogloszenie.sprzedawca != request.user and not request.user.is_staff:
            raise PermissionDenied('Brak uprawnień.')
        ogloszenie.przedluz(30)
        messages.success(request, 'Ważność ogłoszenia została przedłużona o 30 dni.')
        return redirect('ogloszenia:moje_ogloszenia')


class ZmienStatusOgloszeniaView(LoginRequiredMixin, View):
    """Zmiana statusu przez sprzedawcę: publikacja szkicu lub oznaczenie jako sprzedane."""
    def post(self, request, pk):
        ogloszenie = get_object_or_404(Ogloszenie, pk=pk)
        if ogloszenie.sprzedawca != request.user and not request.user.is_staff:
            raise PermissionDenied('Brak uprawnień.')

        akcja = request.POST.get('akcja')
        try:
            if akcja == 'opublikuj':
                ogloszenie.opublikuj()
                messages.success(request, 'Ogłoszenie zostało opublikowane.')
            elif akcja == 'sprzedane':
                ogloszenie.oznacz_jako_sprzedane()
                messages.success(request, 'Ogłoszenie oznaczono jako sprzedane.')
        except NiedozwolonaZmianaStatusu as e:
            messages.error(request, str(e))

        return redirect('ogloszenia:moje_ogloszenia')


class MojeOgloszeniaView(SprzedawcaWymaganyMixin, ListView):
    """Lista własnych ogłoszeń sprzedawcy z możliwością zarządzania statusami."""
    model = Ogloszenie
    template_name = 'ogloszenia/moje_ogloszenia.html'
    context_object_name = 'ogloszenia'

    def get_queryset(self):
        return Ogloszenie.objects.filter(
            sprzedawca=self.request.user
        ).select_related('model_pojazdu', 'model_pojazdu__marka').prefetch_related('zdjecia').order_by('-data_dodania')


class UlubioneListaView(LoginRequiredMixin, ListView):
    """Lista ulubionych ogłoszeń kupującego."""
    model = Ulubione
    template_name = 'ogloszenia/ulubione.html'
    context_object_name = 'ulubione_lista'

    def get_queryset(self):
        return Ulubione.objects.filter(
            uzytkownik=self.request.user
        ).select_related('ogloszenie', 'ogloszenie__model_pojazdu', 'ogloszenie__model_pojazdu__marka', 'ogloszenie__sprzedawca').prefetch_related('ogloszenie__zdjecia')


class PrzelaczUlubioneView(LoginRequiredMixin, View):
    """Dodanie lub usunięcie ogłoszenia z listy ulubionych."""
    def post(self, request, pk):
        ogloszenie = get_object_or_404(Ogloszenie, pk=pk)
        ulubione, created = Ulubione.objects.get_or_create(
            uzytkownik=request.user,
            ogloszenie=ogloszenie
        )
        if created:
            messages.success(request, f'Ogłoszenie „{ogloszenie.tytul}” dodano do ulubionych.')
        else:
            ulubione.delete()
            messages.info(request, f'Ogłoszenie „{ogloszenie.tytul}” usunięto z ulubionych.')

        return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('ogloszenia:szczegoly', kwargs={'pk': pk})))


class PorownywarkaView(View):
    """Porównanie do 3 samochodów w tabeli obok siebie."""
    def get(self, request):
        porownywarka = Porownywarka(request.session)
        samochody = porownywarka.ogloszenia()
        return render(request, 'ogloszenia/porownanie.html', {'samochody': samochody})


class PorownywarkaDodajView(View):
    """Dodanie auta do porównywarki w sesji."""
    def post(self, request, pk):
        porownywarka = Porownywarka(request.session)
        sukces = porownywarka.dodaj(pk)
        if sukces:
            messages.success(request, 'Dodano pojazd do porównania.')
        else:
            messages.warning(request, 'Możesz porównać maksymalnie 3 samochody jednocześnie.')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('ogloszenia:porownanie')))


class PorownywarkaUsunView(View):
    """Usunięcie auta z porównywarki."""
    def post(self, request, pk):
        porownywarka = Porownywarka(request.session)
        porownywarka.usun(pk)
        messages.info(request, 'Usunięto pojazd z porównania.')
        return redirect('ogloszenia:porownanie')


class PorownywarkaWyczyscView(View):
    """Wyczyszczenie porównywarki."""
    def post(self, request):
        porownywarka = Porownywarka(request.session)
        porownywarka.wyczysc()
        messages.info(request, 'Porównywarka została wyczyszczona.')
        return redirect('ogloszenia:porownanie')


class ApiModeleView(View):
    """Endpoint JSON zwracający listę modeli dla wybranej marki."""
    def get(self, request):
        marka_id = request.GET.get('marka_id')
        if not marka_id:
            return JsonResponse({'modele': []})
        try:
            modele = ModelPojazdu.objects.filter(marka_id=int(marka_id)).values('id', 'nazwa')
            return JsonResponse({'modele': list(modele)})
        except (ValueError, TypeError):
            return JsonResponse({'modele': []})
