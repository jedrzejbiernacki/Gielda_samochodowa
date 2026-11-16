from decimal import Decimal
from django import forms
from django.utils import timezone
from .models import (
    Ogloszenie,
    Marka,
    ModelPojazdu,
    Zdjecie,
    Paliwo,
    SkrzyniaBiegow,
    TypNadwozia,
    StatusOgloszenia,
    TypSprzedazy,
)

class FiltryOgloszenForm(forms.Form):
    fraza = forms.CharField(required=False, label='Szukana fraza', widget=forms.TextInput(attrs={'placeholder': 'Np. BMW Seria 3, klima, czarny...'}))
    marka = forms.ModelChoiceField(
        queryset=Marka.objects.all(),
        required=False,
        empty_label='Wszystkie marki',
        label='Marka'
    )
    model_pojazdu = forms.ModelChoiceField(
        queryset=ModelPojazdu.objects.none(),
        required=False,
        empty_label='Wszystkie modele',
        label='Model'
    )
    cena_od = forms.DecimalField(required=False, min_value=0, label='Cena od (zł)')
    cena_do = forms.DecimalField(required=False, min_value=0, label='Cena do (zł)')
    rok_od = forms.IntegerField(required=False, min_value=1950, label='Rocznik od')
    rok_do = forms.IntegerField(required=False, min_value=1950, label='Rocznik do')
    przebieg_od = forms.IntegerField(required=False, min_value=0, label='Przebieg od (km)')
    przebieg_do = forms.IntegerField(required=False, min_value=0, label='Przebieg do (km)')
    paliwo = forms.ChoiceField(
        choices=[('', 'Wszystkie rodzaje paliwa')] + list(Paliwo.choices),
        required=False,
        label='Paliwo'
    )
    skrzynia = forms.ChoiceField(
        choices=[('', 'Wszystkie skrzynie biegów')] + list(SkrzyniaBiegow.choices),
        required=False,
        label='Skrzynia biegów'
    )
    nadwozie = forms.ChoiceField(
        choices=[('', 'Wszystkie typy nadwozia')] + list(TypNadwozia.choices),
        required=False,
        label='Typ nadwozia'
    )
    lokalizacja = forms.CharField(required=False, label='Miejscowość', widget=forms.TextInput(attrs={'placeholder': 'Np. Warszawa, Kraków...'}))
    sortowanie = forms.ChoiceField(
        choices=[
            ('data_desc', 'Najnowsze dodane'),
            ('cena_asc', 'Cena: najtańsze'),
            ('cena_desc', 'Cena: najdroższe'),
            ('rok_desc', 'Rocznik: najnowszy'),
            ('przebieg_asc', 'Przebieg: najniższy'),
        ],
        required=False,
        initial='data_desc',
        label='Sortowanie'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        marka_id = None
        if 'marka' in self.data and self.data.get('marka'):
            try:
                marka_id = int(self.data.get('marka'))
            except (ValueError, TypeError):
                pass
        elif self.initial.get('marka'):
            marka_id = self.initial.get('marka')

        if marka_id:
            self.fields['model_pojazdu'].queryset = ModelPojazdu.objects.filter(marka_id=marka_id)
        else:
            self.fields['model_pojazdu'].queryset = ModelPojazdu.objects.all()
    def clean(self):
        cleaned_data = super().clean()
        cena_od = cleaned_data.get('cena_od')
        cena_do = cleaned_data.get('cena_do')
        if cena_od is not None and cena_do is not None and cena_od > cena_do:
            self.add_error('cena_od', 'Cena „od” nie może być większa niż „do”.')
        rok_od = cleaned_data.get('rok_od')
        rok_do = cleaned_data.get('rok_do')
        if rok_od is not None and rok_do is not None and rok_od > rok_do:
            self.add_error('rok_od', 'Rocznik „od” nie może być większy niż „do”.')
        przebieg_od = cleaned_data.get('przebieg_od')
        przebieg_do = cleaned_data.get('przebieg_do')
        if przebieg_od is not None and przebieg_do is not None and przebieg_od > przebieg_do:
            self.add_error('przebieg_od', 'Przebieg „od” nie może być większy niż „do”.')
        return cleaned_data



class OgloszenieForm(forms.ModelForm):
    marka = forms.ModelChoiceField(
        queryset=Marka.objects.all(),
        required=True,
        empty_label='Wybierz markę',
        label='Marka'
    )

    class Meta:
        model = Ogloszenie
        fields = [
            'marka',
            'model_pojazdu',
            'tytul',
            'opis',
            'rok_produkcji',
            'przebieg_km',
            'pojemnosc_cm3',
            'moc_km',
            'paliwo',
            'skrzynia',
            'nadwozie',
            'kolor',
            'vin',
            'lokalizacja',
            'cena',
            'typ_sprzedazy',
            'cena_wywolawcza',
            'data_zakonczenia_licytacji',
        ]
        widgets = {
            'opis': forms.Textarea(attrs={'rows': 6, 'placeholder': 'Szczegółowy opis stanu technicznego, wyposażenia, historii...'}),
            'data_zakonczenia_licytacji': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cena'].required = False
        self.fields['cena_wywolawcza'].required = False
        self.fields['data_zakonczenia_licytacji'].required = False

        if self.instance and self.instance.pk and self.instance.model_pojazdu:
            self.fields['marka'].initial = self.instance.model_pojazdu.marka
            self.fields['model_pojazdu'].queryset = ModelPojazdu.objects.filter(marka=self.instance.model_pojazdu.marka)
        else:
            marka_id = self.data.get('marka')
            if marka_id:
                try:
                    self.fields['model_pojazdu'].queryset = ModelPojazdu.objects.filter(marka_id=int(marka_id))
                except (ValueError, TypeError):
                    self.fields['model_pojazdu'].queryset = ModelPojazdu.objects.none()
            else:
                self.fields['model_pojazdu'].queryset = ModelPojazdu.objects.all()

    def clean_vin(self):
        vin = self.cleaned_data.get('vin')
        if vin:
            vin = vin.strip().upper()
            if len(vin) != 17:
                raise forms.ValidationError('Numer VIN musi mieć dokładnie 17 znaków.')
        return vin

    def clean_rok_produkcji(self):
        rok = self.cleaned_data.get('rok_produkcji')
        maks_rok = timezone.now().year + 1
        if rok and rok > maks_rok:
            raise forms.ValidationError(f'Rok produkcji nie może przekraczać {maks_rok}.')
        return rok

    def clean(self):
        cleaned_data = super().clean()
        typ_sprzedazy = cleaned_data.get('typ_sprzedazy')
        cena = cleaned_data.get('cena')
        cena_wywolawcza = cleaned_data.get('cena_wywolawcza')
        data_zakonczenia = cleaned_data.get('data_zakonczenia_licytacji')

        if typ_sprzedazy == TypSprzedazy.LICYTACJA:
            if not cena_wywolawcza:
                self.add_error('cena_wywolawcza', 'Cena wywoławcza jest wymagana dla licytacji.')
            if not data_zakonczenia:
                self.add_error('data_zakonczenia_licytacji', 'Data zakończenia licytacji jest wymagana dla licytacji.')
            elif data_zakonczenia <= timezone.now():
                self.add_error('data_zakonczenia_licytacji', 'Data zakończenia licytacji musi być w przyszłości.')
            if not cena and cena_wywolawcza:
                cleaned_data['cena'] = cena_wywolawcza
        else:
            if not cena:
                self.add_error('cena', 'Cena jest wymagana.')

        return cleaned_data


class OfertaForm(forms.Form):
    kwota = forms.DecimalField(
        min_value=Decimal('1.00'),
        label='Twoja oferta (zł)',
        widget=forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control', 'placeholder': 'Wpisz kwotę'})
    )


class MultipleFileInput(forms.FileInput):
    allow_multiple_selected = True

class ZdjecieUploadForm(forms.Form):
    zdjecia = forms.FileField(
        required=False,
        widget=MultipleFileInput(attrs={'multiple': True, 'class': 'form-control'}),
        label='Dodaj zdjęcia (maksymalnie 10, do 5 MB każde)'
    )

    def clean_zdjecia(self):
        pliki = self.files.getlist('zdjecia')
        maks_rozmiar = 5 * 1024 * 1024  # 5 MB
        for plik in pliki:
            if plik.size > maks_rozmiar:
                raise forms.ValidationError(f'Plik {plik.name} przekracza dopuszczalny rozmiar 5 MB.')
        return pliki
