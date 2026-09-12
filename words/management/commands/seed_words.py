"""
Örnek sözlük verisini yükler.

Tekrar çalıştırılabilir: var olan kayıtlar güncellenir, olmayanlar eklenir.
Çekim biçimleri (WordForm) her seferinde kelimeden yeniden üretilir.

    python manage.py seed_words
    python manage.py seed_words --flush     # önce çekirdeği temizle
    python manage.py seed_words --dry-run
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from words import inflect, seed_data
from words.models import (
    Category, Collocation, ExampleSentence, Expression, ExpressionExample,
    FalseFriend, Meaning, UsagePattern, Word, WordFamily, WordRelation,
)


class Command(BaseCommand):
    help = "Örnek kelime ailelerini veritabanına yükler."

    def add_arguments(self, parser):
        parser.add_argument("--flush", action="store_true",
                            help="Yüklemeden önce tüm aileleri ve kelimeleri sil.")
        parser.add_argument("--dry-run", action="store_true",
                            help="Hiçbir şey yazma, ne olacağını göster.")

    @transaction.atomic
    def handle(self, *args, **secenekler):
        kuru = secenekler["dry_run"]

        if secenekler["flush"] and not kuru:
            silinen = WordFamily.objects.count()
            WordFamily.objects.all().delete()   # Word ve altı CASCADE ile gider
            Expression.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"{silinen} aile silindi."))

        kategoriler = self._kategorileri_kur(kuru)
        sayac = self._aileleri_kur(kuru, kategoriler)
        sayac["bag"], atlanan = self._baglari_kur(kuru, sayac.pop("dizin"))
        sayac["ifade"] = self._ifadeleri_kur(kuru, kategoriler)

        ozet = (f"{sayac['aile']} aile, {sayac['kelime']} kelime, {sayac['anlam']} anlam, "
                f"{sayac['cumle']} örnek cümle, {sayac['collocation']} collocation, "
                f"{sayac['kalip']} kalıp, {sayac['yanlis_dost']} yanlış dost, "
                f"{sayac['bicim']} çekim biçimi, {sayac['bag']} bağ, "
                f"{sayac['ifade']} ifade, {len(kategoriler)} alan")
        if atlanan:
            ozet += f" ({atlanan} bağ atlandı)"
        if kuru:
            ozet += "  (DENEME: hiçbir şey yazılmadı)"
        self.stdout.write(self.style.SUCCESS(ozet))

    # ------------------------------------------------------------------

    def _kategorileri_kur(self, kuru):
        """Alan adlarını Category kayıtlarına çevirir; ad -> kayıt döner."""
        kategoriler = {}
        for ad in seed_data.KATEGORILER:
            if kuru:
                kategoriler[ad] = None
                continue
            kategoriler[ad], _ = Category.objects.get_or_create(
                slug=slugify(ad) or ad.lower(), defaults={"name": ad},
            )
        return kategoriler

    def _aileleri_kur(self, kuru, kategoriler):
        sayac = dict(aile=0, kelime=0, anlam=0, cumle=0, collocation=0,
                     kalip=0, yanlis_dost=0, bicim=0, dizin={})

        for aile_verisi in seed_data.AILELER:
            aile = None
            if not kuru:
                aile, _ = WordFamily.objects.update_or_create(
                    root=aile_verisi["root"],
                    defaults={"note": aile_verisi.get("note")},
                )
            sayac["aile"] += 1

            for kelime_verisi in aile_verisi["words"]:
                self._kelime_kur(kelime_verisi, aile, kuru, kategoriler, sayac)

        return sayac

    def _kelime_kur(self, veri, aile, kuru, kategoriler, sayac):
        yazim, tur = veri["text"], veri["pos"]
        v2, v3 = veri.get("v2"), veri.get("v3")

        sayac["kelime"] += 1
        sayac["anlam"] += len(veri["meanings"])
        sayac["bicim"] += len(inflect.forms_for(yazim, tur, v2, v3))
        for anlam in veri["meanings"]:
            sayac["cumle"] += len(anlam["sentences"])
            sayac["collocation"] += len(anlam["collocations"])
            sayac["kalip"] += len(anlam["patterns"])
        sayac["yanlis_dost"] += len(veri.get("false_friends", []))

        if kuru:
            return

        kelime, _ = Word.objects.update_or_create(
            text=yazim, pos=tur,
            defaults={
                "family": aile,
                "cefr": veri["cefr"],
                "isBaseWord": True,
                "visibility": "public",
                "v2Form": v2,
                "v3Form": v3,
            },
        )
        sayac["dizin"][f"{yazim}/{tur}"] = kelime

        # Anlamlar ve altındaki her şey her seferinde yeniden yazılıyor:
        # kaynak dosya tek doğruluk kaynağı.
        kelime.meanings.all().delete()
        for sira, anlam_verisi in enumerate(veri["meanings"]):
            self._anlam_kur(kelime, anlam_verisi, sira, kategoriler)

        kelime.false_friends.all().delete()
        FalseFriend.objects.bulk_create([
            FalseFriend(word=kelime, turkish_lookalike=benzer,
                        assumed_meaning=sanilan, correct_english=dogru)
            for benzer, sanilan, dogru in veri.get("false_friends", [])
        ])

        inflect.rebuild_forms(kelime)

    def _anlam_kur(self, kelime, veri, sira, kategoriler):
        anlam = Meaning.objects.create(
            word=kelime,
            meaning_tr=veri["tr"],
            definition=veri.get("definition"),
            sentiment=veri["sentiment"],
            register=veri["register"],
            sort_order=sira,
        )

        if veri["categories"]:
            anlam.categories.set([kategoriler[ad] for ad in veri["categories"]])

        ExampleSentence.objects.bulk_create([
            ExampleSentence(meaning=anlam, text=cumle, source="core", sort_order=i)
            for i, cumle in enumerate(veri["sentences"][:Meaning.EXAMPLE_SENTENCE_COUNT])
        ])

        Collocation.objects.bulk_create([
            Collocation(meaning=anlam, pattern=yapi, kind=tur, meaning_tr=tr, sort_order=i)
            for i, (yapi, tur, tr) in enumerate(veri["collocations"])
        ])

        UsagePattern.objects.bulk_create([
            UsagePattern(meaning=anlam, pattern=kalip, kind=tur, note=notu, sort_order=i)
            for i, (kalip, tur, notu) in enumerate(veri["patterns"])
        ])

    def _baglari_kur(self, kuru, dizin):
        if kuru:
            return len(seed_data.BAGLAR), 0

        sayi = atlanan = 0
        for kaynak, hedef, tur, not_ in seed_data.BAGLAR:
            a, b = dizin.get(kaynak), dizin.get(hedef)
            if a is None or b is None:
                atlanan += 1
                self.stdout.write(self.style.WARNING(
                    f"Bağ atlandı (kelime yok): {kaynak} -> {hedef}"))
                continue
            WordRelation.objects.update_or_create(
                from_word=a, to_word=b, type=tur, defaults={"note": not_},
            )
            sayi += 1
        return sayi, atlanan

    def _ifadeleri_kur(self, kuru, kategoriler):
        if kuru:
            return len(seed_data.IFADELER)

        sayi = 0
        for veri in seed_data.IFADELER:
            ifade, _ = Expression.objects.update_or_create(
                text=veri["text"],
                defaults={
                    "meaning_tr": veri["tr"],
                    "definition": veri.get("definition"),
                    "kind": veri.get("kind", "fixed"),
                    "cefr": veri.get("cefr", "Belirtilmemiş"),
                    "register": veri.get("register", "neutral"),
                    "sentiment": veri.get("sentiment", "neutral"),
                    "visibility": "public",
                },
            )
            ifade.categories.set([kategoriler[ad] for ad in veri.get("categories", [])])

            # İfade bir ya da birkaç kelimeye asılır; sözlükte olmayan
            # kelimeye asılmaz — bağ iki KAYIT arasındadır.
            kelimeler = []
            for anahtar in veri.get("words", []):
                yazim, tur = anahtar.split("/")
                kelime = Word.objects.filter(text=yazim, pos=tur).first()
                if kelime is not None:
                    kelimeler.append(kelime)
            ifade.words.set(kelimeler)

            ifade.examples.all().delete()
            ExpressionExample.objects.bulk_create([
                ExpressionExample(expression=ifade, text=c, sort_order=i)
                for i, c in enumerate(veri.get("sentences", []))
            ])
            sayi += 1
        return sayi
