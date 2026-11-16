from django.urls import path
from .views import SkrzynkaView, WatekView, NowaWiadomoscView

app_name = 'wiadomosci'

urlpatterns = [
    path('', SkrzynkaView.as_view(), name='skrzynka'),
    path('watek/<int:ogloszenie_id>/<int:kupujacy_id>/', WatekView.as_view(), name='watek'),
    path('nowa/<int:ogloszenie_id>/', NowaWiadomoscView.as_view(), name='nowa'),
]
