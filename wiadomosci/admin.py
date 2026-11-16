from django.contrib import admin
from .models import Wiadomosc

@admin.register(Wiadomosc)
class WiadomoscAdmin(admin.ModelAdmin):
    list_display = ('id', 'ogloszenie', 'kupujacy', 'nadawca', 'odbiorca', 'data_wyslania', 'przeczytana')
    list_filter = ('przeczytana', 'data_wyslania')
    search_fields = ('tresc', 'nadawca__username', 'odbiorca__username', 'ogloszenie__tytul')
    readonly_fields = ('data_wyslania',)
