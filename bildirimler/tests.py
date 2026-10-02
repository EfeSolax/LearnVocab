"""
Bildirimler ve PWA testleri. pywebpush her yerde mock'lanır: gerçek push
servisine istek gitmez. VAPID anahtarları sahte değerlerle override edilir.
"""

import json
import tempfile
from datetime import datetime, timedelta
from io import StringIO
from pathlib import Path
from unittest import mock
from zoneinfo import ZoneInfo

from django.core.management import CommandError, call_command
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from seri.models import GunlukCalisma, SeriDurumu
from texts.models import Text
from texts.sinyaller import degerlendirildi
from users.models import User

from . import ayar, gonder
from .management.commands.vapid_anahtari_uret import anahtar_cifti_uret
from .models import GunlukHatirlatma, PushAboneligi

SAHTE_VAPID = dict(VAPID_PUBLIC_KEY="BGenel-anahtar_test", VAPID_PRIVATE_KEY="ozel-anahtar-test",
                   VAPID_ADMIN_EMAIL="test@example.com")
KAPALI_VAPID = dict(VAPID_PUBLIC_KEY="", VAPID_PRIVATE_KEY="", VAPID_ADMIN_EMAIL="")

ABONELIK = {
    "endpoint": "https://fcm.googleapis.com/fcm/send/abc123",
    "keys": {"p256dh": "BNcRdreALRFXTkOOUHK1EtK2wtaz5Ry4YfYCA_0QTpQtUbVlUls0VJXg7A8u-Ts1XbjhazAkj7I99e8QcYP7DkM",
             "auth": "tBHItJI5svbpez7KI4CCXg"},
}

IST = ZoneInfo("Europe/Istanbul")


def _kullanici(ad="efe"):
    return User.objects.create_user(username=ad, email=f"{ad}@example.com", password="parola-123")


def _abonelik(user, sira=1):
    return PushAboneligi.objects.create(
        user=user, endpoint=f"https://push.example.com/{user.pk}/{sira}", p256dh="p", auth="a")


class _PushHatasi(Exception):
    def __init__(self, durum):
        super().__init__("push")
        self.response = mock.Mock(status_code=durum)


def _webpush_mock(hata=None):
    """gonder._webpush'un yerine geçen (webpush, WebPushException) çifti."""
    webpush = mock.Mock(side_effect=hata)
    return mock.patch.object(gonder, "_webpush", return_value=(webpush, _PushHatasi)), webpush


# ------------------------------------------------------------------ PWA

class PwaDosyalariTest(TestCase):
    def test_manifest(self):
        yanit = self.client.get("/manifest.webmanifest")
        self.assertEqual(yanit.status_code, 200)
        self.assertTrue(yanit["Content-Type"].startswith("application/manifest+json"))
        veri = json.loads(yanit.content)
        self.assertEqual(veri["name"], "LearnVocab")
        self.assertEqual(veri["display"], "standalone")
        self.assertEqual(veri["start_url"], "/")
        boyutlar = {i["sizes"] for i in veri["icons"]}
        self.assertIn("192x192", boyutlar)
        self.assertIn("512x512", boyutlar)

    def test_service_worker_kokten_sunulur(self):
        yanit = self.client.get("/sw.js")
        self.assertEqual(yanit.status_code, 200)
        self.assertTrue(yanit["Content-Type"].startswith("application/javascript"))
        self.assertEqual(yanit["Service-Worker-Allowed"], "/")
        self.assertIn("no-cache", yanit["Cache-Control"])
        govde = yanit.content.decode()
        self.assertIn("'push'", govde)
        self.assertIn("notificationclick", govde)
        # Önbellekleme yapmaz: fetch dinleyicisi yok.
        self.assertNotIn("'fetch'", govde)

    def test_ikonlar_var(self):
        from django.contrib.staticfiles import finders
        for ad in ("ikon-192.png", "ikon-512.png", "ikon-maskable-512.png", "apple-touch-icon.png"):
            self.assertTrue(finders.find(f"pwa/{ad}"), ad)

    def test_sayfada_manifest_ve_ios_etiketleri(self):
        yanit = self.client.get(reverse("learn_pass_page"))
        self.assertContains(yanit, 'rel="manifest"')
        self.assertContains(yanit, "apple-mobile-web-app-capable")
        self.assertContains(yanit, "apple-touch-icon")
        self.assertContains(yanit, "serviceWorker.register")


# ------------------------------------------------------------ Abonelik

@override_settings(**SAHTE_VAPID)
class AbonelikUclariTest(TestCase):
    def setUp(self):
        self.user = _kullanici()
        self.client = Client(enforce_csrf_checks=True)
        self.client.force_login(self.user)
        # CSRF çerezini almak için bir sayfa aç.
        self.client.get(reverse("learn_pass_page"))
        self.csrf = self.client.cookies["csrftoken"].value

    def _post(self, ad, veri, csrf=True):
        basliklar = {"HTTP_X_CSRFTOKEN": self.csrf} if csrf else {}
        return self.client.post(reverse(ad), data=json.dumps(veri),
                                content_type="application/json", **basliklar)

    def test_abone_ol(self):
        yanit = self._post("bildirim_abone_ol", ABONELIK)
        self.assertEqual(yanit.status_code, 200)
        abonelik = PushAboneligi.objects.get()
        self.assertEqual(abonelik.user, self.user)
        self.assertEqual(abonelik.endpoint, ABONELIK["endpoint"])
        self.assertEqual(abonelik.auth, ABONELIK["keys"]["auth"])

    def test_ayni_cihaz_tekrar_abone_olunca_cogalmaz(self):
        self._post("bildirim_abone_ol", ABONELIK)
        self._post("bildirim_abone_ol", ABONELIK)
        self.assertEqual(PushAboneligi.objects.count(), 1)

    def test_birden_cok_cihaz(self):
        self._post("bildirim_abone_ol", ABONELIK)
        ikinci = dict(ABONELIK, endpoint="https://updates.push.services.mozilla.com/wpush/v2/xyz")
        self._post("bildirim_abone_ol", ikinci)
        self.assertEqual(self.user.push_abonelikleri.count(), 2)

    def test_ayni_cihaz_baska_hesaba_gecer(self):
        _abonelik(_kullanici("baska"))
        PushAboneligi.objects.update(endpoint=ABONELIK["endpoint"])
        self._post("bildirim_abone_ol", ABONELIK)
        self.assertEqual(PushAboneligi.objects.get().user, self.user)

    def test_csrf_olmadan_reddedilir(self):
        yanit = self._post("bildirim_abone_ol", ABONELIK, csrf=False)
        self.assertEqual(yanit.status_code, 403)
        self.assertFalse(PushAboneligi.objects.exists())

    def test_girissiz_reddedilir(self):
        istemci = Client()
        yanit = istemci.post(reverse("bildirim_abone_ol"), data=json.dumps(ABONELIK),
                             content_type="application/json")
        self.assertEqual(yanit.status_code, 403)
        self.assertFalse(PushAboneligi.objects.exists())

    def test_get_kabul_edilmez(self):
        self.assertEqual(self.client.get(reverse("bildirim_abone_ol")).status_code, 405)

    def test_gecersiz_veri(self):
        kotu = [
            "bozuk json",
            {},
            dict(ABONELIK, endpoint="http://duz-http.example.com/x"),
            dict(ABONELIK, endpoint="javascript:alert(1)"),
            dict(ABONELIK, endpoint="https://x.example.com/" + "a" * 600),
            dict(ABONELIK, keys={}),
            dict(ABONELIK, keys={"p256dh": "<script>", "auth": "x"}),
            dict(ABONELIK, keys="dizi"),
        ]
        for veri in kotu:
            govde = veri if isinstance(veri, str) else json.dumps(veri)
            yanit = self.client.post(reverse("bildirim_abone_ol"), data=govde,
                                     content_type="application/json", HTTP_X_CSRFTOKEN=self.csrf)
            self.assertEqual(yanit.status_code, 400, veri)
        self.assertFalse(PushAboneligi.objects.exists())

    def test_abonelikten_cik(self):
        self._post("bildirim_abone_ol", ABONELIK)
        baskasi = _abonelik(_kullanici("baska"))
        yanit = self._post("bildirim_abonelikten_cik", {"endpoint": ABONELIK["endpoint"]})
        self.assertEqual(yanit.status_code, 200)
        self.assertFalse(self.user.push_abonelikleri.exists())
        # Başkasının aboneliğine dokunulmaz.
        self._post("bildirim_abonelikten_cik", {"endpoint": baskasi.endpoint})
        self.assertTrue(PushAboneligi.objects.filter(pk=baskasi.pk).exists())

    def test_hepsinden_cik(self):
        _abonelik(self.user, 1)
        _abonelik(self.user, 2)
        self.assertEqual(self._post("bildirim_abonelikten_cik", {}).status_code, 400)
        self._post("bildirim_abonelikten_cik", {"hepsi": True})
        self.assertFalse(self.user.push_abonelikleri.exists())


# --------------------------------------------------------------- Gönderim

@override_settings(**SAHTE_VAPID)
class GonderimTest(TestCase):
    def setUp(self):
        self.user = _kullanici()

    def test_butun_cihazlara_gider(self):
        _abonelik(self.user, 1)
        _abonelik(self.user, 2)
        yama, webpush = _webpush_mock()
        with yama:
            self.assertEqual(gonder.kullaniciya(self.user, "Başlık", "Gövde", "/x/"), 2)
        self.assertEqual(webpush.call_count, 2)
        cagri = webpush.call_args.kwargs
        self.assertEqual(json.loads(cagri["data"]), {"baslik": "Başlık", "govde": "Gövde", "url": "/x/"})
        self.assertEqual(cagri["vapid_claims"]["sub"], "mailto:test@example.com")
        self.assertEqual(cagri["vapid_private_key"], SAHTE_VAPID["VAPID_PRIVATE_KEY"])
        self.assertTrue(all(a.son_basari for a in PushAboneligi.objects.all()))

    def test_410_ve_404_abonelik_silinir(self):
        for durum in (410, 404):
            abonelik = _abonelik(self.user, durum)
            yama, _ = _webpush_mock(_PushHatasi(durum))
            with yama, self.assertLogs("bildirimler.gonder", "INFO"):
                self.assertEqual(gonder.kullaniciya(self.user, "b", "g"), 0)
            self.assertFalse(PushAboneligi.objects.filter(pk=abonelik.pk).exists())

    def test_gecici_hatada_abonelik_kalir(self):
        abonelik = _abonelik(self.user)
        yama, _ = _webpush_mock(_PushHatasi(500))
        with yama, self.assertLogs("bildirimler.gonder", "WARNING"):
            self.assertEqual(gonder.kullaniciya(self.user, "b", "g"), 0)
        self.assertTrue(PushAboneligi.objects.filter(pk=abonelik.pk).exists())

    def test_beklenmedik_hata_disari_tasmaz(self):
        _abonelik(self.user)
        yama, _ = _webpush_mock(RuntimeError("ağ"))
        with yama, self.assertLogs("bildirimler.gonder", "ERROR"):
            self.assertEqual(gonder.kullaniciya(self.user, "b", "g"), 0)


@override_settings(**KAPALI_VAPID)
class VapidYokkenTest(TestCase):
    """Anahtar yoksa her şey sessizce kapalı; site bozulmaz."""

    def setUp(self):
        self.user = _kullanici()

    def test_kapali(self):
        self.assertFalse(ayar.acik())

    def test_gonderim_atlanir(self):
        _abonelik(self.user)
        yama, webpush = _webpush_mock()
        with yama:
            self.assertEqual(gonder.kullaniciya(self.user, "b", "g"), 0)
        webpush.assert_not_called()

    def test_abonelik_ucu_kapali(self):
        self.client.force_login(self.user)
        yanit = self.client.post(reverse("bildirim_abone_ol"), data=json.dumps(ABONELIK),
                                 content_type="application/json")
        self.assertEqual(yanit.status_code, 404)

    def test_on_ekran_ve_ayar_cizilmez(self):
        from django.template.loader import render_to_string
        self.assertNotIn("data-bildirim-ayari", render_to_string("bildirimler/_ayar.html"))
        self.client.force_login(self.user)
        html = self.client.get(reverse("index")).content.decode()
        self.assertNotIn("bildirim-on-ekrani", html)
        self.assertNotIn("lvBildirim", html)

    def test_hatirlatma_komutu_bir_sey_gondermez(self):
        _abonelik(self.user)
        yama, webpush = _webpush_mock()
        with yama:
            call_command("bildirim_gonder_hatirlatma", stdout=StringIO())
        webpush.assert_not_called()
        self.assertFalse(GunlukHatirlatma.objects.exists())

    def test_sayfalar_calisir(self):
        self.assertEqual(self.client.get(reverse("learn_pass_page")).status_code, 200)
        self.assertEqual(self.client.get("/manifest.webmanifest").status_code, 200)


@override_settings(**SAHTE_VAPID)
class OnEkranTest(TestCase):
    """Rapor 18.29: izin ön ekranı 3 biten egzersiz + 20 L&P kartından sonra çıkar."""

    def setUp(self):
        self.user = User.objects.create_user(username="onekran", password="Sifre1234", cefr="B1")
        self.client.force_login(self.user)

    def _html(self, ad="index", **kw):
        return self.client.get(reverse(ad, kwargs=kw)).content.decode()

    def _olcutu_sagla(self, egzersiz=3, kart=20):
        from egzersizler.models import EgzersizOturumu
        from learnpass.models import WordEncounter
        from words.testing import make_word
        for _ in range(egzersiz):
            EgzersizOturumu.objects.create(user=self.user, tur="hizli", tip="anlam", istenen=10,
                                           sorular=[], durum=EgzersizOturumu.DURUM_BITTI)
        w = make_word("onekran")
        WordEncounter.objects.create(user=self.user, word=w, last_verdict="known",
                                     known_count=kart - 5, unknown_count=5, times_seen=kart)

    def test_olcut_saglanmadan_cikmaz(self):
        self.assertNotIn('id="bildirim-on-ekrani"', self._html())
        self._olcutu_sagla(egzersiz=2, kart=40)
        self.assertNotIn('id="bildirim-on-ekrani"', self._html())

    def test_az_lp_karti_yetmez(self):
        self._olcutu_sagla(egzersiz=3, kart=19)
        self.assertNotIn('id="bildirim-on-ekrani"', self._html())

    def test_olcut_saglaninca_kapibarali_on_ekran(self):
        self._olcutu_sagla()
        html = self._html()
        self.assertIn('id="bildirim-on-ekrani"', html)
        self.assertIn("window.lvBildirim = ", html)
        self.assertIn("günün kelimesini", html)
        self.assertIn("Ana Ekrana Ekle", html)
        on_ekran = html[html.index('id="bildirim-on-ekrani"'):]
        self.assertIn('data-kapibara="zil"', on_ekran)                # kapibara zil tutar (rapor 18.33)
        # Tarayıcının izin penceresi yalnızca ac() içinde, o da tıklamayla çağrılır.
        self.assertEqual(html.count("Notification.requestPermission()"), 1)
        self.assertGreater(on_ekran.index("window.lvBildirim.ac()"), on_ekran.index("addEventListener('click'"))

    def test_calisma_ekranlarinda_cikmaz(self):
        self._olcutu_sagla()
        self.assertNotIn('id="bildirim-on-ekrani"', self._html("learn_pass_run", mode="karma"))

    def test_seviyesi_belirsizken_once_seviye_daveti(self):
        self._olcutu_sagla()
        self.user.cefr = ""
        self.user.save()
        html = self._html()
        self.assertIn("data-seviye-daveti", html)
        self.assertNotIn('id="bildirim-on-ekrani"', html)

    def test_lp_bitis_ekraninda_eski_kart_yok(self):
        self.assertNotIn("Yarın hatırlatayım mı?", self._html("learn_pass_run", mode="karma"))

    def test_ayarlarda_bildirim_bolumu(self):
        html = self._html("settings_page")
        self.assertIn("data-bildirim-ayari", html)
        self.assertIn("window.lvBildirim.kapat()", html)



# ------------------------------------------------------ "Yazın değerlendirildi"

@override_settings(**SAHTE_VAPID)
class YaziSinyaliTest(TestCase):
    def setUp(self):
        self.user = _kullanici()
        _abonelik(self.user)
        self.yazi = Text.objects.create(owner=self.user, content="I go to school every day.")

    def test_arka_planda_degerlendirilince_bildirim_gider(self):
        yama, webpush = _webpush_mock()
        with yama:
            degerlendirildi(self.yazi, arka_planda=True)
        webpush.assert_called_once()
        veri = json.loads(webpush.call_args.kwargs["data"])
        self.assertEqual(veri["baslik"], "Yazın değerlendirildi")
        self.assertEqual(veri["url"], reverse("review_text", args=[self.yazi.pk]))

    def test_kullanici_ekrandayken_bildirim_gitmez(self):
        yama, webpush = _webpush_mock()
        with yama:
            degerlendirildi(self.yazi, arka_planda=False)
        webpush.assert_not_called()


# --------------------------------------------------------- Günlük hatırlatma

@override_settings(**SAHTE_VAPID)
class HatirlatmaKomutuTest(TestCase):
    """Rapor 18.9: yerel 12.00 ve 23.45; gün tamamlandıysa ya da seri 0 ise gitmez."""

    OGLE = datetime(2026, 9, 28, 12, 5, tzinfo=IST)
    GECE = datetime(2026, 9, 28, 23, 50, tzinfo=IST)

    def setUp(self):
        dun = self.OGLE.date() - timedelta(days=1)
        self.seri_var = _kullanici("seri-var")
        self.tamamlamis = _kullanici("tamamlamis")
        self.seri_yok = _kullanici("seri-yok")
        self.abone_olmayan = _kullanici("abone-degil")
        for u in (self.seri_var, self.tamamlamis, self.abone_olmayan):
            SeriDurumu.objects.create(user=u, mevcut=4, hak=1, son_islenen_gun=dun)
        SeriDurumu.objects.create(user=self.seri_yok, mevcut=0, son_islenen_gun=dun)
        GunlukCalisma.objects.create(user=self.tamamlamis, gun=self.OGLE.date(), lp=10, tamamlandi=True)
        for u in (self.seri_var, self.tamamlamis, self.seri_yok):
            _abonelik(u)

    def _calistir(self, simdi, *arg):
        yama, webpush = _webpush_mock()
        with yama, mock.patch.object(timezone, "now", return_value=simdi):
            call_command("bildirim_gonder_hatirlatma", *arg, stdout=StringIO())
        return webpush

    def _govde(self, webpush):
        return json.loads(webpush.call_args.kwargs["data"])

    def test_ogle_yalnizca_serisi_olup_gunu_bitirmemise(self):
        webpush = self._calistir(self.OGLE)
        self.assertEqual(webpush.call_count, 1)
        self.assertEqual(set(GunlukHatirlatma.objects.values_list("user__username", "tur")),
                         {("seri-var", "ogle")})
        veri = self._govde(webpush)
        self.assertIn("Bugünün çalışması seni bekliyor", veri["govde"])
        self.assertEqual(veri["url"], reverse("learn_pass_page"))

    def test_ayni_pencerede_bir_kez(self):
        self._calistir(self.OGLE)
        webpush = self._calistir(self.OGLE + timedelta(minutes=5))
        webpush.assert_not_called()

    def test_pencere_disinda_gitmez(self):
        for saat in (11, 13, 19, 23):
            webpush = self._calistir(self.OGLE.replace(hour=saat, minute=10))
            webpush.assert_not_called()

    def test_gece_dondurma_hakki_varsa(self):
        webpush = self._calistir(self.GECE)
        self.assertIn("1 dondurma hakkın kullanılacak", self._govde(webpush)["govde"])

    def test_gece_hak_yoksa_seri_uyarisi(self):
        SeriDurumu.objects.filter(user=self.seri_var).update(hak=0)
        webpush = self._calistir(self.GECE)
        self.assertIn("4 günlük serin gece yarısı bitiyor", self._govde(webpush)["govde"])

    def test_ogle_ve_gece_ayri_ayri_gider(self):
        self._calistir(self.OGLE)
        self._calistir(self.GECE)
        self.assertEqual(GunlukHatirlatma.objects.filter(user=self.seri_var).count(), 2)

    def test_yerel_saat(self):
        """Londra'daki kullanıcıya Londra'nın 12.00'sinde (İstanbul 14.05) gider."""
        SeriDurumu.objects.filter(user=self.seri_var).update(saat_dilimi="Europe/London")
        self._calistir(self.OGLE).assert_not_called()
        self.assertEqual(self._calistir(self.OGLE + timedelta(hours=2)).call_count, 1)

    def test_cok_cihazli_kullaniciya_tek_kayit(self):
        _abonelik(self.seri_var, 2)
        webpush = self._calistir(self.OGLE)
        self.assertEqual(webpush.call_count, 2)
        self.assertEqual(GunlukHatirlatma.objects.get(user=self.seri_var).gonderilen, 2)

    def test_dry_run(self):
        self._calistir(self.OGLE, "--dry-run").assert_not_called()
        self.assertFalse(GunlukHatirlatma.objects.exists())


# ------------------------------------------------------------ VAPID komutu

class VapidKomutuTest(TestCase):
    """Gerçek .env'e DOKUNMAZ: her test geçici bir dosya kullanır."""

    def setUp(self):
        self.klasor = tempfile.TemporaryDirectory()
        self.env = Path(self.klasor.name) / ".env"

    def tearDown(self):
        self.klasor.cleanup()

    def _calistir(self, *arg):
        cikti = StringIO()
        call_command("vapid_anahtari_uret", "--env-dosyasi", str(self.env), *arg, stdout=cikti)
        return cikti.getvalue()

    def _degerler(self):
        return dict(s.split("=", 1) for s in self.env.read_text().splitlines() if "=" in s)

    def test_anahtar_cifti_gecerli(self):
        import base64
        genel, ozel = anahtar_cifti_uret()
        self.assertEqual(len(base64.urlsafe_b64decode(genel + "==")), 65)
        self.assertEqual(len(base64.urlsafe_b64decode(ozel + "==")), 32)
        # pywebpush'un kullandığı py_vapid bu biçimi okuyabilmeli.
        from py_vapid import Vapid
        Vapid.from_string(private_key=ozel)

    def test_yeni_dosyaya_yazar_ve_ekrana_basmaz(self):
        self.env.write_text("SECRET_KEY=abc\nDEBUG=True\n")
        cikti = self._calistir("--eposta", "efe@example.com")
        d = self._degerler()
        self.assertEqual(d["SECRET_KEY"], "abc")
        self.assertTrue(d["VAPID_PUBLIC_KEY"])
        self.assertTrue(d["VAPID_PRIVATE_KEY"])
        self.assertEqual(d["VAPID_ADMIN_EMAIL"], "efe@example.com")
        self.assertNotIn(d["VAPID_PUBLIC_KEY"], cikti)
        self.assertNotIn(d["VAPID_PRIVATE_KEY"], cikti)

    def test_bos_satirlari_doldurur(self):
        self.env.write_text("VAPID_PUBLIC_KEY=\nVAPID_PRIVATE_KEY=\nVAPID_ADMIN_EMAIL=a@b.com\n")
        self._calistir("--eposta", "baska@example.com")
        d = self._degerler()
        self.assertTrue(d["VAPID_PRIVATE_KEY"])
        self.assertEqual(d["VAPID_ADMIN_EMAIL"], "a@b.com")
        self.assertEqual(self.env.read_text().count("VAPID_PUBLIC_KEY"), 1)

    def test_var_olan_anahtari_ezmez(self):
        icerik = "SECRET_KEY=abc\nVAPID_PUBLIC_KEY=eski-genel\nVAPID_PRIVATE_KEY=eski-ozel\n"
        self.env.write_text(icerik)
        with self.assertRaises(CommandError) as hata:
            self._calistir()
        self.assertEqual(self.env.read_text(), icerik)
        self.assertNotIn("eski-ozel", str(hata.exception))

    def test_yalnizca_biri_doluysa_da_ezmez(self):
        icerik = "VAPID_PRIVATE_KEY=eski-ozel\n"
        self.env.write_text(icerik)
        with self.assertRaises(CommandError):
            self._calistir()
        self.assertEqual(self.env.read_text(), icerik)

    def test_dosya_yoksa_olusturur(self):
        self._calistir()
        self.assertTrue(self._degerler()["VAPID_PRIVATE_KEY"])
