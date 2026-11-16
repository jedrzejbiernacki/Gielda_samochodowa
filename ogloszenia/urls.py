from django.urls import path
from .views import (
    ListaOgloszenView,
    SzczegolyOgloszeniaView,
    DodajOgloszenieView,
    EdytujOgloszenieView,
    UsunOgloszenieView,
    PrzedluzOgloszenieView,
    ZmienStatusOgloszeniaView,
    MojeOgloszeniaView,
    UlubioneListaView,
    PrzelaczUlubioneView,
    PorownywarkaView,
    PorownywarkaDodajView,
    PorownywarkaUsunView,
    PorownywarkaWyczyscView,
    ApiModeleView,
)

app_name = 'ogloszenia'

urlpatterns = [
    path('', ListaOgloszenView.as_view(), name='lista'),
    path('ogloszenie/<int:pk>/', SzczegolyOgloszeniaView.as_view(), name='szczegoly'),
    path('ogloszenie/dodaj/', DodajOgloszenieView.as_view(), name='dodaj'),
    path('ogloszenie/<int:pk>/edytuj/', EdytujOgloszenieView.as_view(), name='edytuj'),
    path('ogloszenie/<int:pk>/usun/', UsunOgloszenieView.as_view(), name='usun'),
    path('ogloszenie/<int:pk>/przedluz/', PrzedluzOgloszenieView.as_view(), name='przedluz'),
    path('ogloszenie/<int:pk>/status/', ZmienStatusOgloszeniaView.as_view(), name='zmien_status'),
    path('moje-ogloszenia/', MojeOgloszeniaView.as_view(), name='moje_ogloszenia'),
    path('ulubione/', UlubioneListaView.as_view(), name='ulubione'),
    path('ulubione/przelacz/<int:pk>/', PrzelaczUlubioneView.as_view(), name='ulubione_przelacz'),
    path('porownanie/', PorownywarkaView.as_view(), name='porownanie'),
    path('porownanie/dodaj/<int:pk>/', PorownywarkaDodajView.as_view(), name='porownanie_dodaj'),
    path('porownanie/usun/<int:pk>/', PorownywarkaUsunView.as_view(), name='porownanie_usun'),
    path('porownanie/wyczysc/', PorownywarkaWyczyscView.as_view(), name='porownanie_wyczysc'),
    path('api/modele/', ApiModeleView.as_view(), name='api_modele'),
]
