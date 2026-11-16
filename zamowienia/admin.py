from django.contrib import admin
from .models import Zamowienie, Ocena

@admin.register(Zamowienie)
class ZamowienieAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'ogloszenie',
        'kupujacy',
        'cena',
        'status',
        'data_zlozenia',
        'data_decyzji',
        'data_zakonczenia',
    )
    list_filter = ('status', 'data_zlozenia')
    search_fields = ('ogloszenie__tytul', 'kupujacy__username', 'ogloszenie__sprzedawca__username')
    readonly_fields = ('data_zlozenia', 'data_decyzji', 'data_zakonczenia')

@admin.register(Ocena)
class OcenaAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'zamowienie',
        'oceniajacy',
        'oceniany',
        'liczba_gwiazdek',
        'data_wystawienia',
    )
    list_filter = ('liczba_gwiazdek', 'data_wystawienia')
    search_fields = ('oceniajacy__username', 'oceniany__username', 'komentarz')
    readonly_fields = ('data_wystawienia',)
