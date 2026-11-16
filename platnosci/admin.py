from django.contrib import admin
from .models import Cennik, OplataZaOgloszenie, Wyroznienie

@admin.register(Cennik)
class CennikAdmin(admin.ModelAdmin):
    list_display = (
        '__str__',
        'limit_ogloszen_prywatny',
        'limit_ogloszen_komis',
        'cena_dodatkowe_ogloszenie',
        'cena_wyroznienie_7dni',
        'cena_wyroznienie_30dni',
    )

    def has_add_permission(self, request):
        if Cennik.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(OplataZaOgloszenie)
class OplataZaOgloszenieAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'uzytkownik',
        'ogloszenie',
        'typ_oplaty',
        'kwota',
        'oplacone',
        'data_oplacenia',
        'data_utworzenia',
    )
    list_filter = ('typ_oplaty', 'oplacone', 'data_utworzenia')
    search_fields = ('uzytkownik__username', 'uzytkownik__email', 'ogloszenie__tytul')

@admin.register(Wyroznienie)
class WyroznienieAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'ogloszenie',
        'oplata',
        'data_rozpoczecia',
        'data_zakonczenia',
        'aktywne',
    )
    list_filter = ('data_rozpoczecia', 'data_zakonczenia')
    search_fields = ('ogloszenie__tytul',)
