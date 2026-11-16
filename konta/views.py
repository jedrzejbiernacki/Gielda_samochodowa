from django.views.generic import CreateView, UpdateView, DetailView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import get_object_or_404
from .models import Uzytkownik
from .forms import RejestracjaForm, LogowanieForm, EdycjaProfiluForm

class RejestracjaView(CreateView):
    model = Uzytkownik
    form_class = RejestracjaForm
    template_name = 'konta/rejestracja.html'
    success_url = reverse_lazy('konta:logowanie')

    def form_valid(self, form):
        messages.success(self.request, 'Konto zostało pomyślnie utworzone. Możesz się teraz zalogować.')
        return super().form_valid(form)

class LogowanieView(LoginView):
    form_class = LogowanieForm
    template_name = 'konta/logowanie.html'

    def form_valid(self, form):
        messages.success(self.request, f'Witaj ponownie, {form.get_user().nazwa_wyswietlana()}!')
        return super().form_valid(form)

class WylogowanieView(LogoutView):
    next_page = reverse_lazy('ogloszenia:lista')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, 'Zostałeś wylogowany.')
        return super().dispatch(request, *args, **kwargs)

class EdycjaProfiluView(LoginRequiredMixin, UpdateView):
    model = Uzytkownik
    form_class = EdycjaProfiluForm
    template_name = 'konta/profil.html'
    success_url = reverse_lazy('konta:profil')

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Twój profil został zaktualizowany.')
        return super().form_valid(form)

class ProfilSprzedawcyView(DetailView):
    model = Uzytkownik
    template_name = 'konta/profil_sprzedawcy.html'
    context_object_name = 'sprzedawca'

    def get_context_data(self, **kwargs):
        kontekst = super().get_context_data(**kwargs)
        sprzedawca = self.object
        from ogloszenia.models import Ogloszenie
        kontekst['ogloszenia'] = Ogloszenie.objects.filter(
            sprzedawca=sprzedawca,
            status='AKTYWNE'
        ).select_related('model_pojazdu', 'model_pojazdu__marka').prefetch_related('zdjecia')
        kontekst['oceny'] = sprzedawca.otrzymane_oceny.select_related('oceniajacy', 'zamowienie').order_by('-data_wystawienia')
        return kontekst
