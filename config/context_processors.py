def gielda_kontekst(request):
    """Kontekst globalny dla szablonów: nieprzeczytane wiadomości, liczba aut w porównywarce."""
    kontekst = {
        'liczba_nieprzeczytanych': 0,
        'liczba_w_porownywarce': 0,
    }
    if request.user.is_authenticated:
        from wiadomosci.models import Wiadomosc
        kontekst['liczba_nieprzeczytanych'] = Wiadomosc.objects.filter(
            odbiorca=request.user,
            przeczytana=False
        ).count()

    porownywarka = request.session.get('porownywarka', [])
    kontekst['liczba_w_porownywarce'] = len(porownywarka)
    return kontekst
