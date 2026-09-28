"""
LearnVocab - Ana URL yapılandırması.

Her uygulama (users, words, learnpass, ...) kendi urls.py dosyasında URL'lerini
tanımlar; bu dosya yalnızca onları include eder.
"""

from datetime import date
import hashlib

from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render
from django.urls import include, path

from readings import api as readings_api
from words import views as word_views


def showIndex(request):
    """
    Ana sayfa. 401 ve 501 kur seviyesinden 3 rastgele 'base' kelime seçilir
    ve "günün kelimeleri" olarak gösterilir. Seçim günlük olarak deterministik:
    aynı gün içinde sayfa yenilense bile aynı 3 kelime gelir, ertesi gün değişir.
    """
    from words.models import Word  # döngüsel import'tan kaçınmak için view içinde

    # 401 veya 501 seviyesinde, base kelime olan ve sahibi olmayanlar
    pool = Word.objects.filter(
        isBaseWord=True,
        cefr__in=("B2", "C1"),
    ).select_related("family").prefetch_related("meanings", "examples")

    daily_words = []
    pool_count = pool.count()
    if pool_count:
        # Bugünün tarihinden tutarlı bir seed üret
        seed_str = date.today().isoformat()
        digest = hashlib.sha1(seed_str.encode("utf-8")).hexdigest()
        # 3 rastgele indeks (tekilleştirilmiş)
        indices = []
        i = 0
        while len(indices) < min(3, pool_count) and i < 32:
            chunk = digest[i * 4: i * 4 + 8] or digest[:8]
            idx = int(chunk, 16) % pool_count
            if idx not in indices:
                indices.append(idx)
            i += 1
        ids = list(pool.values_list("id", flat=True))
        chosen_ids = [ids[i] for i in indices]
        # Seçilen sırayı korumak için liste comprehension
        words_by_id = {w.id: w for w in Word.objects.filter(id__in=chosen_ids)}
        daily_words = [words_by_id[i] for i in chosen_ids if i in words_by_id]

    return render(request, "pages/index.html", {"daily_words": daily_words})


def showAbout(request):
    return render(request, "pages/about.html")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", showIndex, name="index"),
    path("about/", showAbout, name="about"),
    # Okumalar (rapor 8) ve kelime sorgulama API'si (okuma baloncuğu, Chrome eklentisi)
    path("readings/", include("readings.urls")),
    path("api/kelime/", readings_api.kelime, name="kelime_api"),
    # Sözlük (rapor 4). Adres paylaşılabilir: /sozluk/?q=aim
    path("sozluk/", word_views.sozluk, name="sozluk"),
    path("users/", include("users.urls")),
    path("words/", include("words.urls")),
    # Arkadaşlık özelliği şu an KAPALI.
    # Uygulamanın kendisi (friends/views.py, friends/urls.py, templates/pages/friends.html)
    # ve kullanıcı modelindeki friends / incomingRequests alanları duruyor;
    # yalnızca dışarıya açılan yol kapatıldı. Geri açmak için bu satırı yorumdan
    # çıkarmak ve navbar'daki bağlantıyı geri koymak yeterli.
    # path("friends/", include("friends.urls")),
    path("profile/", include("userprofile.urls")),
    path("exercises/", include("learnpass.urls")),
    # Yorumlar özelliği şu an KAPALI (arkadaşlık gibi).
    # comments uygulaması, view'ları, şablonu ve Comment modeli duruyor;
    # veriler yalnızca admin panelinden görülebiliyor. Geri açmak için bu
    # satırı yorumdan çıkarmak ve navbar'a bağlantıyı geri koymak yeterli.
    # path("comments/", include("comments.urls")),
    path("texts/", include("texts.urls")),
    path("settings/", include("usersettings.urls")),
]

# Geliştirme ortamında media dosyalarını Django'nun servis etmesi için
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
