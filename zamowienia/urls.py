from django.urls import path
from .views import (
    ZlozZamowienieView,
    MojeZamowieniaView,
    OtrzymaneZamowieniaView,
    AkceptujZamowienieView,
    OdrzucZamowienieView,
    AnulujZamowienieView,
    PotwierdzOdbiorView,
    WystawOceneView,
)

app_name = 'zamowienia'

urlpatterns = [
    path('zloz/<int:pk>/', ZlozZamowienieView.as_view(), name='zloz'),
    path('moje/', MojeZamowieniaView.as_view(), name='moje'),
    path('otrzymane/', OtrzymaneZamowieniaView.as_view(), name='otrzymane'),
    path('<int:pk>/akceptuj/', AkceptujZamowienieView.as_view(), name='akceptuj'),
    path('<int:pk>/odrzuc/', OdrzucZamowienieView.as_view(), name='odrzuc'),
    path('<int:pk>/anuluj/', AnulujZamowienieView.as_view(), name='anuluj'),
    path('<int:pk>/potwierdz/', PotwierdzOdbiorView.as_view(), name='potwierdz'),
    path('<int:pk>/ocen/', WystawOceneView.as_view(), name='ocen'),
]
