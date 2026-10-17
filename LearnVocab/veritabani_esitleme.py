"""
Canlı veritabanı (MySQL) <-> SQLite dosyası (Efe, 17 Ekim; komut: manage.py veritabani).

  indir  : 'default' veritabanının (canlıda MySQL) BÜTÜN tabloları aynen yeni bir SQLite
           dosyasına kopyalanır. Dosyaya bir künye tablosu (_lv_esitleme) yazılır: ne zaman
           alındığı, migration durumu ve her içerik tablosunun parmak izi.
  yukle  : Dosyadaki İÇERİK tabloları (sözlük, okumalar, hazır listeler, konular, egzersiz ve
           seviye testi havuzları) 'default'a yazılır: yeni satır eklenir, değişen güncellenir,
           dosyada olmayan silinir. KULLANICI tablolarına (hesaplar, listeler, seri, yazılar,
           oturumlar …) DOKUNULMAZ: indirmeyle yükleme arasında canlıda olan her şey korunur.
           Silinen bir kelimeye bağlı kullanıcı kayıtları (listesindeki o kelime gibi) Django'nun
           kurallarıyla birlikte silinir; kuru denemede sayıları gösterilir.
  yukle --hepsi : İlk taşıma için: 'default'taki BÜTÜN tablolar boşaltılır ve dosyadan doldurulur.

Güvenlik:
  - yukle varsayılan olarak kuru denemedir (her şey yapılıp geri alınır, yalnızca rapor).
  - Gerçek yüklemeden önce 'default'un tam yedeği aynı yöntemle bir SQLite dosyasına alınır.
  - Dosya ile canlının migration'ları aynı değilse durur.
  - Dosya indirildikten sonra canlıdaki bir içerik tablosu değiştiyse durur (parmak izi tutmaz);
    --zorla ile geçilebilir (canlıdaki o değişiklikler dosyadakiyle ezilir).
  - Yükleme tek işlemde (transaction) yapılır; bütünlük denetimi geçmezse hiçbir şey yazılmaz.

Satırlar Django modelleri üzerinden okunur ama ham SQL ile yazılır: ORM ile yazmak auto_now
alanlarını (createdAt, son güncelleme …) "şimdi"ye çevirirdi. Dosyanın şeması migrate ile DEĞİL
doğrudan modellerden kurulur: projedeki veri migration'ları (RunPython) .using(alias) kullanmadığı
için migrate çalıştırmak onları canlı veritabanında yeniden işletirdi. Migration kayıtları kaynaktan
kopyalanır.
"""

import hashlib
import json
import os
from datetime import datetime

from django.apps import apps
from django.conf import settings
from django.db import connections, transaction
from django.db.migrations.recorder import MigrationRecorder

DOSYA = "dosya"                    # dosya için geçici veritabanı adı (alias)
KUNYE = "_lv_esitleme"
PARCA = 500                        # paylaşımlı MySQL'de küçük max_allowed_packet için

# Yalnızca bunlar yüklenir. Yeni bir model eklenince buraya ya da KULLANICI'ya yazılmalı
# (test: LearnVocab/test_veritabani_esitleme.py hepsinin sınıflandırıldığını denetler).
ICERIK = {
    "words_category", "words_wordfamily", "words_word", "words_meaning", "words_meaning_categories",
    "words_examplesentence", "words_collocation", "words_usagepattern", "words_wordform",
    "words_wordrelation", "words_falsefriend", "words_expressiongroup", "words_expression",
    "words_expression_extra_groups", "words_expression_categories", "words_expression_words",
    "words_expressionexample", "words_hazirliste", "words_hazirlistekelimesi",
    "texts_diyalog", "readings_readingtext", "readings_okumakonusu",
    "egzersizler_baglaccumlesi", "egzersizler_esdizimceldiricisi",
    "seviye_seviyekelimesi", "seviye_okumasorusu",
}
KULLANICI = {
    "django_admin_log", "auth_permission", "auth_group_permissions", "auth_group",
    "django_content_type", "django_session",
    "users_user", "users_user_friends", "users_user_incomingRequests", "users_user_groups",
    "users_user_user_permissions",
    "words_expression_saved_by", "words_userexpressionlink", "words_userwordlink",
    "words_hazirlistesecimi", "words_gununkelimesi", "words_bulunamayanarama",
    "comments_comment", "comments_comment_liked_by", "comments_comment_disliked_by",
    "texts_text", "texts_text_words", "texts_yazmaayari", "texts_diyalogcevabi",
    "usersettings_broadcastemail", "usersettings_usersettings",
    "learnpass_wordencounter", "learnpass_encounterlog", "learnpass_karsilasmaozeti",
    "readings_readingprogress", "readings_usertext",
    "egzersizler_egzersizoturumu", "egzersizler_egzersizcevabi",
    "bildirimler_pushaboneligi", "bildirimler_gunlukhatirlatma",
    "seviye_seviyetestisonucu", "seviye_seviyeduzeltmesi",
    "seri_gunlukcalisma", "seri_seridurumu",
    "account_emailaddress", "account_emailconfirmation",
    "socialaccount_socialapp", "socialaccount_socialaccount", "socialaccount_socialtoken",
}


class EsitlemeHatasi(Exception):
    """Kullanıcıya gösterilecek, işlemi durduran sorun."""


class _KuruDeneme(Exception):
    pass


# ---------------------------------------------------------------------------
# Modeller ve satırlar
# ---------------------------------------------------------------------------

def modeller():
    """Veritabanında tablosu olan bütün modeller (ara M2M tabloları dahil), tablo adıyla."""
    sonuc = {}
    for model in apps.get_models(include_auto_created=True):
        meta = model._meta
        if meta.managed and not meta.proxy and not meta.swapped:
            sonuc.setdefault(meta.db_table, model)
    return sonuc


def siniflandirilmamis():
    return sorted(set(modeller()) - ICERIK - KULLANICI)


def _alanlar(model):
    return [f for f in model._meta.concrete_fields]


def satirlar(model, alias):
    """{pk: (değerler…)} — Python değerleri (Django'nun okuma dönüşümleriyle), pk sırasıyla."""
    alanlar = _alanlar(model)
    pk_sira = alanlar.index(model._meta.pk)
    sonuc = {}
    for satir in (model._default_manager.db_manager(alias).order_by("pk")
                  .values_list(*[f.attname for f in alanlar]).iterator(chunk_size=PARCA)):
        sonuc[satir[pk_sira]] = satir
    return sonuc


def parmak_izi(model, alias):
    h = hashlib.sha256()
    for satir in satirlar(model, alias).values():
        h.update(repr(satir).encode())
    return h.hexdigest()


def _yaz(model, alias, degerler, guncelle=False):
    """Satırları ham SQL ile yazar (INSERT ya da pk'ye göre UPDATE)."""
    if not degerler:
        return
    baglanti = connections[alias]
    alanlar = _alanlar(model)
    q = baglanti.ops.quote_name
    tablo = q(model._meta.db_table)
    hazir = [[f.get_db_prep_save(v, baglanti) for f, v in zip(alanlar, satir)] for satir in degerler]
    with baglanti.cursor() as imlec:
        if guncelle:
            pk = model._meta.pk
            digerleri = [i for i, f in enumerate(alanlar) if f is not pk]
            sql = (f"UPDATE {tablo} SET {', '.join(f'{q(alanlar[i].column)} = %s' for i in digerleri)}"
                   f" WHERE {q(pk.column)} = %s")
            pk_i = alanlar.index(pk)
            parametreler = [[s[i] for i in digerleri] + [s[pk_i]] for s in hazir]
        else:
            sql = (f"INSERT INTO {tablo} ({', '.join(q(f.column) for f in alanlar)}) "
                   f"VALUES ({', '.join(['%s'] * len(alanlar))})")
            parametreler = hazir
        for i in range(0, len(parametreler), PARCA):
            imlec.executemany(sql, parametreler[i:i + PARCA])


def _bosalt(alias, tablolar):
    baglanti = connections[alias]
    with baglanti.cursor() as imlec:
        for tablo in tablolar:
            imlec.execute(f"DELETE FROM {baglanti.ops.quote_name(tablo)}")


def _uygulanan_migrationlar(alias):
    return sorted(MigrationRecorder(connections[alias]).applied_migrations())


def _migration_kayitlarini_kopyala(kaynak, hedef):
    Migration = MigrationRecorder.Migration
    satir = list(Migration.objects.using(kaynak).values_list("app", "name", "applied"))
    Migration.objects.using(hedef).bulk_create(
        [Migration(app=a, name=n, applied=t) for a, n, t in satir])


# ---------------------------------------------------------------------------
# Dosya veritabanı
# ---------------------------------------------------------------------------

class dosya_veritabani:
    """with dosya_veritabani(yol, alias): geçici bir SQLite bağlantısı."""

    def __init__(self, yol, alias=DOSYA):
        self.yol, self.alias = str(yol), alias

    def __enter__(self):
        self.onceki = connections.settings.get(self.alias)
        ayar = dict(connections.settings["default"])
        ayar.update({"ENGINE": "django.db.backends.sqlite3", "NAME": self.yol, "USER": "", "PASSWORD": "",
                     "HOST": "", "PORT": "", "OPTIONS": {}, "TEST": {**ayar["TEST"], "NAME": None, "MIRROR": None}})
        connections.settings[self.alias] = ayar
        try:                                     # eski ayarla açılmış bir bağlantı kalmasın
            del connections[self.alias]
        except AttributeError:
            pass
        return connections[self.alias]

    def __exit__(self, *hata):
        connections[self.alias].close()
        del connections[self.alias]
        if self.onceki is None:
            del connections.settings[self.alias]
        else:
            connections.settings[self.alias] = self.onceki


def _sema_kur(alias):
    """Boş SQLite dosyasında bütün tabloları modellerden kurar (migrate çalıştırmadan)."""
    with connections[alias].schema_editor() as editor:
        for model in apps.get_models():          # ara M2M tabloları create_model ile birlikte kurulur
            meta = model._meta
            if meta.managed and not meta.proxy and not meta.swapped:
                editor.create_model(model)
    MigrationRecorder(connections[alias]).ensure_schema()


def _kunye_yaz(alias, bilgiler):
    baglanti = connections[alias]
    with baglanti.cursor() as imlec:
        imlec.execute(f"CREATE TABLE {KUNYE} (anahtar TEXT PRIMARY KEY, deger TEXT)")
        imlec.executemany(f"INSERT INTO {KUNYE} VALUES (%s, %s)",
                          [(k, json.dumps(v, ensure_ascii=False)) for k, v in bilgiler.items()])


def _kunye_oku(alias):
    baglanti = connections[alias]
    if KUNYE not in baglanti.introspection.table_names():
        return None
    with baglanti.cursor() as imlec:
        imlec.execute(f"SELECT anahtar, deger FROM {KUNYE}")
        return {k: json.loads(v) for k, v in imlec.fetchall()}


def _kopyala(kaynak, hedef, tablolar, rapor=print):
    """kaynak'taki tabloların bütün satırlarını hedef'e ekler (hedef boş olmalı)."""
    hepsi = modeller()
    for tablo in tablolar:
        model = hepsi[tablo]
        satir = list(satirlar(model, kaynak).values())
        _yaz(model, hedef, satir)
        rapor(f"  {tablo}: {len(satir)}")


# ---------------------------------------------------------------------------
# indir
# ---------------------------------------------------------------------------

def indir(yol, rapor=print, alias=DOSYA):
    """'default'un tam kopyasını yol'daki YENİ SQLite dosyasına yazar."""
    if os.path.exists(yol):
        raise EsitlemeHatasi(f"{yol} zaten var; başka bir ad ver ya da dosyayı kaldır.")
    if siniflandirilmamis():
        raise EsitlemeHatasi("Sınıflandırılmamış tablolar (LearnVocab/veritabani_esitleme.py ICERIK "
                             f"ya da KULLANICI'ya ekle): {', '.join(siniflandirilmamis())}")
    hepsi = modeller()
    with dosya_veritabani(yol, alias) as hedef:
        rapor("Şema kuruluyor…")
        _sema_kur(alias)
        with hedef.constraint_checks_disabled():
            # Okuma tek işlem içinde: InnoDB'de tutarlı bir anlık görüntü (yazanlar beklemez);
            # dosyaya yazma da tek işlemde (her parça ayrı ayrı diske yazılmasın)
            with transaction.atomic(using="default"), transaction.atomic(using=alias):
                rapor("Tablolar kopyalanıyor…")
                _kopyala("default", alias, sorted(hepsi), rapor)
                _migration_kayitlarini_kopyala("default", alias)
                kunye = {
                    "olusturuldu": datetime.now().isoformat(timespec="seconds"),
                    "kaynak": connections["default"].vendor,
                    "migrationlar": _uygulanan_migrationlar("default"),
                    "parmak_izleri": {t: parmak_izi(hepsi[t], "default") for t in sorted(ICERIK)},
                }
        hedef.check_constraints()
        _kunye_yaz(alias, kunye)
    rapor(f"Hazır: {yol}")
    return kunye


# ---------------------------------------------------------------------------
# yukle
# ---------------------------------------------------------------------------

def _icerik_yukle(rapor):
    """Dosyadaki içerik tablolarını default'a eşitler. Döner: {tablo: (eklenen, güncellenen, silinen)}
    ve silmenin kullanıcı tablolarındaki etkisi."""
    hepsi = modeller()
    ozet, silinecek = {}, {}
    with connections["default"].constraint_checks_disabled():
        for tablo in sorted(ICERIK):
            model = hepsi[tablo]
            yeni, eski = satirlar(model, DOSYA), satirlar(model, "default")
            eklenecek = [s for pk, s in yeni.items() if pk not in eski]
            guncellenecek = [s for pk, s in yeni.items() if pk in eski and eski[pk] != s]
            _yaz(model, "default", eklenecek)
            _yaz(model, "default", guncellenecek, guncelle=True)
            silinecek[tablo] = [pk for pk in eski if pk not in yeni]
            ozet[tablo] = [len(eklenecek), len(guncellenecek), len(silinecek[tablo])]
    # Silme ORM ile: Django'nun on_delete kuralları (CASCADE, SET_NULL) bağlı kayıtlara da uygulanır
    etkiler = {}
    for tablo, pkler in silinecek.items():
        for i in range(0, len(pkler), PARCA):
            _, sayilar = hepsi[tablo]._default_manager.filter(pk__in=pkler[i:i + PARCA]).delete()
            for etiket, n in sayilar.items():
                etkiler[etiket] = etkiler.get(etiket, 0) + n
    return ozet, etkiler


def _hepsini_yukle(rapor):
    hepsi = modeller()
    with connections["default"].constraint_checks_disabled():
        _bosalt("default", hepsi)
        _kopyala(DOSYA, "default", sorted(hepsi), rapor)


def yukle(yol, uygula=False, hepsi=False, zorla=False, yedek_klasoru=None, rapor=print):
    if not os.path.exists(yol):
        raise EsitlemeHatasi(f"{yol} bulunamadı.")
    if siniflandirilmamis():
        raise EsitlemeHatasi(f"Sınıflandırılmamış tablolar: {', '.join(siniflandirilmamis())}")

    with dosya_veritabani(yol):
        kunye = _kunye_oku(DOSYA)
        if _uygulanan_migrationlar(DOSYA) != _uygulanan_migrationlar("default"):
            raise EsitlemeHatasi("Dosyanın ve veritabanının migration'ları farklı. Önce iki tarafta da "
                                 "'manage.py migrate' çalıştır (dosya için: DB_NAME=dosya manage.py migrate).")
        connections[DOSYA].check_constraints()
        if not hepsi:
            if kunye is None:
                raise EsitlemeHatasi("Dosyada künye yok (bu araçla indirilmemiş). İlk taşıma içinse --hepsi kullan.")
            # Çakışma: canlıdaki tablo indirmeden beri değişmiş VE dosyadakinden farklı (aynıysa sorun yok)
            degisen = []
            for t, iz in kunye["parmak_izleri"].items():
                canli = parmak_izi(modeller()[t], "default")
                if canli != iz and canli != parmak_izi(modeller()[t], DOSYA):
                    degisen.append(t)
            if degisen and not zorla:
                raise EsitlemeHatasi("Dosya indirildikten sonra canlıda şu içerik tabloları değişmiş: "
                                     f"{', '.join(degisen)}. Yeniden indir ya da --zorla ile canlıdakini ez.")

        if uygula and yedek_klasoru:
            os.makedirs(yedek_klasoru, exist_ok=True)
            yedek = os.path.join(yedek_klasoru, f"yedek-{datetime.now():%Y%m%d-%H%M%S}.sqlite3")
            rapor(f"Önce tam yedek: {yedek}")
            indir(yedek, rapor=lambda *_: None, alias="dosya_yedek")

        sonuc = {}
        try:
            with transaction.atomic(using="default"):
                if hepsi:
                    _hepsini_yukle(rapor)
                else:
                    sonuc["ozet"], sonuc["etkiler"] = _icerik_yukle(rapor)
                connections["default"].check_constraints()
                if not uygula:
                    raise _KuruDeneme
        except _KuruDeneme:
            pass
        if uygula and kunye is not None:
            # Dosya çalışma kopyası olarak kullanılmaya devam edebilsin: künye yeni canlı durumunu gösterir
            kunye["parmak_izleri"] = {t: parmak_izi(modeller()[t], "default") for t in sorted(ICERIK)}
            kunye["son_yukleme"] = datetime.now().isoformat(timespec="seconds")
            with connections[DOSYA].cursor() as imlec:
                imlec.execute(f"DELETE FROM {KUNYE}")
                imlec.executemany(f"INSERT INTO {KUNYE} VALUES (%s, %s)",
                                  [(k, json.dumps(v, ensure_ascii=False)) for k, v in kunye.items()])
    if uygula:
        from django.core.cache import cache
        cache.clear()
    return sonuc

