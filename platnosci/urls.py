from django.urls import path
from .views import OplacOgloszenieView, WyroznijOgloszenieView, HistoriaOplatView

app_name = 'platnosci'

urlpatterns = [
    path('oplac/<int:pk>/', OplacOgloszenieView.as_view(), name='oplac'),
    path('wyroznij/<int:pk>/', WyroznijOgloszenieView.as_view(), name='wyroznij'),
    path('historia/', HistoriaOplatView.as_view(), name='historia'),
]
