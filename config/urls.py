from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('konto/', include('konta.urls', namespace='konta')),
    path('wiadomosci/', include('wiadomosci.urls', namespace='wiadomosci')),
    path('zamowienia/', include('zamowienia.urls', namespace='zamowienia')),
    path('platnosci/', include('platnosci.urls', namespace='platnosci')),
    path('', include('ogloszenia.urls', namespace='ogloszenia')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
