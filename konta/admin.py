from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import Uzytkownik

@admin.action(description='Zablokuj wybrane konta użytkowników')
def zablokuj_uzytkownikow(modeladmin, request, queryset):
    zaktualizowano = queryset.update(zablokowany=True)
    modeladmin.message_user(request, f'Zablokowano {zaktualizowano} kont(a).')

@admin.action(description='Odblokuj wybrane konta użytkowników')
def odblokuj_uzytkownikow(modeladmin, request, queryset):
    zaktualizowano = queryset.update(zablokowany=False)
    modeladmin.message_user(request, f'Odblokowano {zaktualizowano} kont(a).')

@admin.register(Uzytkownik)
class UzytkownikAdmin(UserAdmin):
    list_display = (
        'username',
        'email',
        'rola',
        'nazwa_firmy',
        'miasto',
        'zablokowany',
        'pokaz_srednia_ocen',
        'is_staff',
        'data_rejestracji',
    )
    list_filter = ('rola', 'zablokowany', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'nazwa_firmy', 'first_name', 'last_name', 'miasto')
    actions = [zablokuj_uzytkownikow, odblokuj_uzytkownikow]

    fieldsets = UserAdmin.fieldsets + (
        (_('Dane profilu giełdy'), {
            'fields': ('rola', 'nazwa_firmy', 'telefon', 'miasto', 'zablokowany'),
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (_('Dane profilu giełdy'), {
            'fields': ('rola', 'nazwa_firmy', 'telefon', 'miasto'),
        }),
    )

    @admin.display(description='Średnia ocen')
    def pokaz_srednia_ocen(self, obj):
        srednia = obj.srednia_ocen()
        return f"{srednia} ★ ({obj.liczba_ocen()})" if srednia else 'Brak ocen'
