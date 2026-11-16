from django.contrib import admin
from .models import Marka, ModelPojazdu, Ogloszenie, Zdjecie, Ulubione, StatusOgloszenia

@admin.action(description='Zablokuj wybrane ogłoszenia (moderacja)')
def zablokuj_ogloszenia(modeladmin, request, queryset):
    zaktualizowano = queryset.update(status=StatusOgloszenia.ZABLOKOWANE)
    modeladmin.message_user(request, f'Zablokowano {zaktualizowano} ogłoszeń.')

@admin.action(description='Odblokuj wybrane ogłoszenia')
def odblokuj_ogloszenia(modeladmin, request, queryset):
    zaktualizowano = queryset.update(status=StatusOgloszenia.AKTYWNE)
    modeladmin.message_user(request, f'Odblokowano {zaktualizowano} ogłoszeń.')

class ZdjecieInline(admin.TabularInline):
    model = Zdjecie
    extra = 1
    fields = ('plik', 'kolejnosc', 'data_dodania')
    readonly_fields = ('data_dodania',)

@admin.register(Marka)
class MarkaAdmin(admin.ModelAdmin):
    list_display = ('nazwa', 'liczba_modeli')
    search_fields = ('nazwa',)

    def liczba_modeli(self, obj):
        return obj.modele.count()
    liczba_modeli.short_description = 'Liczba modeli'

@admin.register(ModelPojazdu)
class ModelPojazduAdmin(admin.ModelAdmin):
    list_display = ('nazwa', 'marka', 'liczba_ogloszen')
    list_filter = ('marka',)
    search_fields = ('nazwa', 'marka__nazwa')

    def liczba_ogloszen(self, obj):
        return obj.ogloszenia.count()
    liczba_ogloszen.short_description = 'Liczba ogłoszeń'

@admin.register(Ogloszenie)
class OgloszenieAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'tytul',
        'sprzedawca',
        'model_pojazdu',
        'cena',
        'rok_produkcji',
        'status',
        'liczba_wyswietlen',
        'data_dodania',
        'data_wygasniecia',
    )
    list_filter = ('status', 'paliwo', 'skrzynia', 'nadwozie', 'model_pojazdu__marka')
    search_fields = ('tytul', 'opis', 'vin', 'sprzedawca__username', 'sprzedawca__nazwa_firmy', 'lokalizacja')
    actions = [zablokuj_ogloszenia, odblokuj_ogloszenia]
    inlines = [ZdjecieInline]
    readonly_fields = ('liczba_wyswietlen', 'data_dodania', 'data_aktualizacji')

@admin.register(Ulubione)
class UlubioneAdmin(admin.ModelAdmin):
    list_display = ('uzytkownik', 'ogloszenie', 'data_dodania')
    list_filter = ('data_dodania',)
    search_fields = ('uzytkownik__username', 'ogloszenie__tytul')
