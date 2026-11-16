from django import forms
from .models import Ocena

class ZlozZamowienieForm(forms.Form):
    uwagi = forms.CharField(
        required=False,
        label='Uwagi do rezerwacji (np. proponowany termin spotkania)',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Wpisz swoje uwagi, pytania lub proponowany termin odbioru...'
        })
    )
    akceptacja_warunkow = forms.BooleanField(
        required=True,
        label='Potwierdzam chęć rezerwacji tego pojazdu i akceptuję warunki giełdy.'
    )

class OdrzucZamowienieForm(forms.Form):
    uzasadnienie = forms.CharField(
        required=False,
        label='Uzasadnienie odrzucenia rezerwacji (opcjonalnie)',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Wpisz powód odrzucenia...'
        })
    )

class OcenaForm(forms.ModelForm):
    GWIAZDKI_CHOICES = [
        (5, '5 ★★★★★ - Zdecydowanie polecam'),
        (4, '4 ★★★★☆ - Dobry kontakt i auto zgodne z opisem'),
        (3, '3 ★★★☆☆ - Przeciętnie'),
        (2, '2 ★★☆☆☆ - Niezadowalająco'),
        (1, '1 ★☆☆☆☆ - Zdecydowanie nie polecam'),
    ]

    liczba_gwiazdek = forms.ChoiceField(
        choices=GWIAZDKI_CHOICES,
        widget=forms.RadioSelect,
        label='Twoja ocena'
    )

    class Meta:
        model = Ocena
        fields = ['liczba_gwiazdek', 'komentarz']
        widgets = {
            'komentarz': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Podziel się swoją opinią o sprzedawcy, zgodności auta z ogłoszeniem i przebiegu transakcji...'
            })
        }
        labels = {
            'komentarz': 'Komentarz do oceny'
        }
