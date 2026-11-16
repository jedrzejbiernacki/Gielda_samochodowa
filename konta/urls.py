from django.urls import path
from .views import (
    RejestracjaView,
    LogowanieView,
    WylogowanieView,
    EdycjaProfiluView,
    ProfilSprzedawcyView,
)

app_name = 'konta'

urlpatterns = [
    path('rejestracja/', RejestracjaView.as_view(), name='rejestracja'),
    path('logowanie/', LogowanieView.as_view(), name='logowanie'),
    path('wylogowanie/', WylogowanieView.as_view(), name='wylogowanie'),
    path('profil/', EdycjaProfiluView.as_view(), name='profil'),
    path('sprzedawca/<int:pk>/', ProfilSprzedawcyView.as_view(), name='profil_sprzedawcy'),
]
