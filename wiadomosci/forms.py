from django import forms
from .models import Wiadomosc

class WiadomoscForm(forms.ModelForm):
    class Meta:
        model = Wiadomosc
        fields = ['tresc']
        widgets = {
            'tresc': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'maxlength': 2000,
                'placeholder': 'Wpisz treść wiadomości (do 2000 znaków)...'
            })
        }
        labels = {
            'tresc': 'Twoja wiadomość'
        }
