from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Uzytkownik, RolaUzytkownika

class RejestracjaForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Adres e-mail')
    first_name = forms.CharField(max_length=150, required=True, label='Imię')
    last_name = forms.CharField(max_length=150, required=True, label='Nazwisko')

    class Meta(UserCreationForm.Meta):
        model = Uzytkownik
        fields = (
            'username',
            'email',
            'first_name',
            'last_name',
            'rola',
            'nazwa_firmy',
            'telefon',
            'miasto',
        )

    def clean(self):
        cleaned_data = super().clean()
        rola = cleaned_data.get('rola')
        nazwa_firmy = cleaned_data.get('nazwa_firmy')

        if rola == RolaUzytkownika.KOMIS and not nazwa_firmy:
            self.add_error('nazwa_firmy', 'Dla konta komisu podanie nazwy firmy jest wymagane.')

        return cleaned_data

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Uzytkownik.objects.filter(email=email).exists():
            raise forms.ValidationError('Konto z tym adresem e-mail już istnieje.')
        return email

class LogowanieForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if user.zablokowany:
            raise forms.ValidationError(
                'To konto zostało zablokowane przez administratora. Skontaktuj się z obsługą serwisu.',
                code='konto_zablokowane',
            )

class EdycjaProfiluForm(forms.ModelForm):
    class Meta:
        model = Uzytkownik
        fields = [
            'first_name',
            'last_name',
            'email',
            'telefon',
            'miasto',
            'nazwa_firmy',
        ]

    def clean(self):
        cleaned_data = super().clean()
        if self.instance.rola == RolaUzytkownika.KOMIS:
            nazwa = cleaned_data.get('nazwa_firmy')
            if not nazwa:
                self.add_error('nazwa_firmy', 'Dla konta komisu podanie nazwy firmy jest wymagane.')
        return cleaned_data
