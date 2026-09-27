"""
Soru üretimi — bir karttan ekrana çıkacak soruya.

Her soru tipi kelime modelinin belirli bir parçasından doğuyor; hiçbiri
uydurulmuyor. Zenginleştirme hattının ürettiği veri ne kadar zenginse
sorular o kadar çeşitli — ve veri yoksa soru da üretilmiyor (None döner,
kart o turda atlanır). Eksik veriyle yarım soru sormak, sormamaktan kötü.

GERİ BİLDİRİM SORUNUN PARÇASIDIR
--------------------------------
Her `Question` nesnesi cevaptan sonra gösterilecek öğretici yükü de
taşıyor: doğru cevap, açıklama, örnek cümleler. Bunun sebebi şu: bir
hatırlama denemesinin hafızaya yaptığı katkının büyük kısmı, denemeden
HEMEN SONRA gelen düzeltmede oluşuyor. Cevabı verip "yanlış" yazıp
sonraki soruya geçen bir sistem, öğrenmenin en verimli anını çöpe atar.

Eski sistemde geri bildirim quiz bittikten sonra "inceleme" sayfasındaydı
— yani on soru sonra, öğrenci neyi neden yanlış yaptığını unuttuktan sonra.
"""

import random
from dataclasses import dataclass, field

from words.models import Register, Sentiment

from . import aspects, distractors, masking
from .aspects import Aspect, Format


SIK_ANAHTARLARI = ("A", "B", "C", "D", "E")


@dataclass
class Question:
    """Ekrana basılacak tek soru ve cevaplandıktan sonra gösterilecek her şey."""

    item_id: int
    aspect: str
    format: str

    # --- soru ---
    instruction: str = ""           # ne yapması isteniyor
    stem: str = ""                  # sorulan şey (kelime ya da başlık)
    sentence: str = ""              # boşluklu cümle (varsa)
    context: str = ""               # ek bilgi satırı (tür, ipucu)
    options: list = field(default_factory=list)   # [{"key","text"}]
    correct_key: str = ""
    accepted: list = field(default_factory=list)  # yazarak cevaplarda
    hint: str = ""
    expected_seconds: float = 10.0

    # --- geri bildirim ---
    answer_display: str = ""
    explanation: str = ""
    examples: list = field(default_factory=list)
    word_text: str = ""
    word_detail_id: int | None = None

    @property
    def aspect_label(self):
        """Şablonda gösterilen boyut adı. (Question bir model değil,
        o yüzden get_aspect_display yok.)"""
        try:
            return Aspect(self.aspect).label
        except ValueError:  # pragma: no cover
            return self.aspect

    @property
    def is_typed(self):
        return self.format in (Format.TYPE, Format.BLANK)

    @property
    def is_production(self):
        return aspects.is_production(self.aspect)

    def __post_init__(self):
        # Kabul listesindeki yinelenenler temizleniyor: `blank_token`
        # hedefi zaten küçük harfle döndürdüğü için aynı cevap iki kez
        # giriyordu. Zararsız ama dökümde ve hata ayıklamada kafa karıştırıyor.
        if self.accepted:
            gorulen, temiz = set(), []
            for kabul in self.accepted:
                anahtar = (kabul or "").strip().lower()
                if anahtar and anahtar not in gorulen:
                    gorulen.add(anahtar)
                    temiz.append(kabul)
            self.accepted = temiz

    def check(self, user_input: str) -> bool:
        """Cevabı değerlendirir."""
        if self.is_typed:
            return masking.answer_matches(user_input, self.accepted)
        return (user_input or "").strip().upper() == self.correct_key


# ----------------------------------------------------------------------
# Yardımcılar
# ----------------------------------------------------------------------

def _siklar(dogru_metin, celdirici_metinler, rng):
    """
    Şıkları karıştırıp anahtarlarını dağıtır.

    Boş ya da yinelenen çeldiriciler atılıyor; geriye ikiden az şık
    kalırsa soru üretilemez (None döner).
    """
    metinler = [dogru_metin]
    for metin in celdirici_metinler:
        metin = (metin or "").strip()
        if metin and metin.lower() not in {m.lower() for m in metinler}:
            metinler.append(metin)

    if len(metinler) < 2:
        return None, None

    rng.shuffle(metinler)
    siklar = [{"key": SIK_ANAHTARLARI[i], "text": m}
              for i, m in enumerate(metinler)]
    dogru_anahtar = next(s["key"] for s in siklar if s["text"] == dogru_metin)
    return siklar, dogru_anahtar


def _ornekler(meaning, haric=None, adet=2):
    """Anlamın örnek cümleleri — geri bildirimde gösterilmek üzere."""
    if meaning is None:
        return []
    cumleler = [c.text for c in meaning.examples.all()]
    if haric:
        cumleler = [c for c in cumleler if c != haric]
    return cumleler[:adet]


def _tur_etiketi(word):
    return word.get_pos_display()


# ----------------------------------------------------------------------
# Boyut üreticileri
# ----------------------------------------------------------------------

def _q_recognize(item, bicim, rng):
    anlam = item.meaning
    if anlam is None:
        return None

    celdiriciler = distractors.meaning_distractors(anlam, count=3, rng=rng)
    metinler = [distractors.distractor_text(c) for c in celdiriciler]
    siklar, dogru = _siklar(anlam.meaning_tr, metinler, rng)
    if not siklar:
        return None

    soru = Question(
        item_id=item.id, aspect=item.aspect, format=bicim,
        instruction="Bu kelimenin anlamı hangisi?",
        stem=item.word.text,
        context=_tur_etiketi(item.word),
        options=siklar, correct_key=dogru,
        expected_seconds=aspects.expected_seconds(item.aspect),
        answer_display=anlam.meaning_tr,
        explanation=anlam.definition or "",
        examples=_ornekler(anlam),
        word_text=item.word.text, word_detail_id=item.word_id,
    )

    if bicim == Format.CHOICE_CONTEXT:
        cumleler = [c.text for c in anlam.examples.all()]
        if not cumleler:
            # Bağlam yoksa düz çoktan seçmeliye düş.
            soru.format = Format.CHOICE
            return soru
        cumle = rng.choice(cumleler)
        yazimlar = masking.surfaces_for_word(item.word)
        soru.instruction = "Kelime bu cümlede hangi anlamda kullanılmış?"
        soru.sentence = masking.highlight(cumle, yazimlar)
        soru.examples = _ornekler(anlam, haric=cumle)

    return soru


def _q_produce(item, bicim, rng):
    anlam = item.meaning
    if anlam is None:
        return None

    kelime = item.word
    yazimlar = masking.surfaces_for_word(kelime)

    if bicim == Format.CHOICE:
        celdiriciler = distractors.word_distractors(kelime, count=3, rng=rng)
        siklar, dogru = _siklar(kelime.text, [c.text for c in celdiriciler], rng)
        if not siklar:
            return None
        return Question(
            item_id=item.id, aspect=item.aspect, format=bicim,
            instruction="Bu anlama gelen kelime hangisi?",
            stem=anlam.meaning_tr,
            context=_tur_etiketi(kelime),
            options=siklar, correct_key=dogru,
            expected_seconds=aspects.expected_seconds(item.aspect),
            answer_display=kelime.text,
            explanation=anlam.definition or "",
            examples=_ornekler(anlam),
            word_text=kelime.text, word_detail_id=kelime.id,
        )

    # Yazarak. İlk harf ipucu olarak veriliyor: tamamen boş bir kutu
    # karşısında öğrenci aklına gelmeyen kelimeyi arayamaz ve deneme
    # hiç gerçekleşmez. Tek harf, aramayı başlatmaya yetiyor ama cevabı
    # vermiyor. (İpucu kullanıldığında not en fazla "zorlandı" oluyor.)
    return Question(
        item_id=item.id, aspect=item.aspect, format=Format.TYPE,
        instruction="Bu anlama gelen İngilizce kelimeyi yaz:",
        stem=anlam.meaning_tr,
        context=_tur_etiketi(kelime),
        accepted=yazimlar,
        hint=kelime.text[0] + "…",
        expected_seconds=aspects.expected_seconds(item.aspect),
        answer_display=kelime.text,
        explanation=anlam.definition or "",
        examples=_ornekler(anlam),
        word_text=kelime.text, word_detail_id=kelime.id,
    )


def _q_context(item, bicim, rng):
    anlam = item.meaning
    if anlam is None:
        return None

    kelime = item.word
    yazimlar = masking.surfaces_for_word(kelime)
    cumleler = [c.text for c in anlam.examples.all()]
    rng.shuffle(cumleler)

    for cumle in cumleler:
        maskeli, bulunan = masking.blank_word(cumle, yazimlar)
        if maskeli:
            return Question(
                item_id=item.id, aspect=item.aspect, format=Format.BLANK,
                instruction="Boşluğa uygun kelimeyi yaz:",
                sentence=maskeli,
                context=f"{anlam.meaning_tr} · {_tur_etiketi(kelime)}",
                accepted=yazimlar,
                hint=kelime.text[0] + "…",
                expected_seconds=aspects.expected_seconds(item.aspect),
                answer_display=bulunan,
                explanation=(f"Cümlede geçen biçim: <b>{bulunan}</b>"
                             if bulunan.lower() != kelime.text.lower() else ""),
                examples=_ornekler(anlam, haric=cumle),
                word_text=kelime.text, word_detail_id=kelime.id,
            )
    return None


def _q_collocation(item, bicim, rng):
    esdizim = item.target
    if esdizim is None or not esdizim.example:
        return None

    kelime = item.word
    kelime_yazimlari = set(masking.surfaces_for_word(kelime))
    # Eş dizimin kelimeye AİT OLMAYAN parçası maskeleniyor: `make a
    # decision` kartında sorulan şey `decision` değil `make`. Kelimenin
    # kendisini maskelemek bu kartı bağlam kartının kopyası yapardı.
    parcalar = masking.pattern_tokens(esdizim.pattern)
    hedefler = [p for p in parcalar if p not in kelime_yazimlari]
    if not hedefler:
        return None
    hedef = hedefler[0]

    maskeli, bulunan = masking.blank_token(esdizim.example, hedef)
    if not maskeli:
        return None

    ortak = (f"{esdizim.pattern}"
             + (f" — {esdizim.meaning_tr}" if esdizim.meaning_tr else ""))

    if bicim == Format.CHOICE:
        celdirici_adaylari = _esdizim_celdiricileri(esdizim, hedef, rng)
        siklar, dogru = _siklar(bulunan, celdirici_adaylari, rng)
        if not siklar:
            bicim = Format.BLANK
        else:
            return Question(
                item_id=item.id, aspect=item.aspect, format=Format.CHOICE,
                instruction="Boşluğa hangisi gelir?",
                sentence=maskeli,
                context=kelime.text,
                options=siklar, correct_key=dogru,
                expected_seconds=aspects.expected_seconds(item.aspect),
                answer_display=bulunan,
                explanation=f"Doğru eş dizim: <b>{ortak}</b>",
                examples=_ornekler(item.meaning, haric=esdizim.example),
                word_text=kelime.text, word_detail_id=kelime.id,
            )

    return Question(
        item_id=item.id, aspect=item.aspect, format=Format.BLANK,
        instruction="Boşluğa uygun kelimeyi yaz:",
        sentence=maskeli,
        context=f"{kelime.text} ile kullanılan kalıp",
        accepted=[bulunan, hedef],
        hint=bulunan[0] + "…",
        expected_seconds=aspects.expected_seconds(item.aspect),
        answer_display=bulunan,
        explanation=f"Doğru eş dizim: <b>{ortak}</b>",
        examples=_ornekler(item.meaning, haric=esdizim.example),
        word_text=kelime.text, word_detail_id=kelime.id,
    )


def _esdizim_celdiricileri(esdizim, hedef, rng):
    """
    Eş dizim şıkları.

    En iyi çeldirici, Türkçeden çevirince akla gelen yanlış fiildir:
    "karar vermek" -> `do a decision`. Sabit bir liste kullanılıyor
    çünkü bu hatalar sayılı ve tahmin edilebilir.
    """
    from words.models import CollocationKind

    YAYGIN_FIILLER = ("do", "make", "take", "have", "get", "give", "put",
                      "hold", "reach", "set")
    YAYGIN_ZARFLAR = ("heavily", "strongly", "deeply", "highly", "widely",
                      "closely", "badly", "fully")

    if esdizim.kind in (CollocationKind.ADV_ADJ, CollocationKind.ADV_VERB):
        havuz = YAYGIN_ZARFLAR
    else:
        havuz = YAYGIN_FIILLER

    return distractors.token_distractors(hedef, havuz, count=3, rng=rng)


def _q_pattern(item, bicim, rng):
    kalip = item.target
    if kalip is None or not kalip.example:
        return None

    from words.models import PatternKind

    kelime = item.word
    kelime_yazimlari = set(masking.surfaces_for_word(kelime))
    parcalar = masking.pattern_tokens(kalip.pattern)
    hedefler = [p for p in parcalar if p not in kelime_yazimlari]
    if not hedefler:
        return None
    # Edat kalıbında maskelenecek şey edattır; kalıbın son anlamlı
    # parçası genelde odur ("depend on", "result in").
    hedef = hedefler[-1] if kalip.kind == PatternKind.PREPOSITION else hedefler[0]

    maskeli, bulunan = masking.blank_token(kalip.example, hedef)
    if not maskeli:
        return None

    aciklama = f"Kalıp: <b>{kalip.pattern}</b>"
    if kalip.note:
        aciklama += f" — {kalip.note}"

    if bicim == Format.CHOICE:
        havuz = (distractors.EDATLAR if kalip.kind == PatternKind.PREPOSITION
                 else distractors.FIIL_BICIMLERI)
        celdiriciler = distractors.token_distractors(bulunan, havuz, 3, rng)
        siklar, dogru = _siklar(bulunan, celdiriciler, rng)
        if siklar:
            return Question(
                item_id=item.id, aspect=item.aspect, format=Format.CHOICE,
                instruction="Boşluğa hangisi gelir?",
                sentence=maskeli, context=kelime.text,
                options=siklar, correct_key=dogru,
                expected_seconds=aspects.expected_seconds(item.aspect),
                answer_display=bulunan, explanation=aciklama,
                examples=_ornekler(item.meaning, haric=kalip.example),
                word_text=kelime.text, word_detail_id=kelime.id,
            )

    return Question(
        item_id=item.id, aspect=item.aspect, format=Format.BLANK,
        instruction="Boşluğu doldur:",
        sentence=maskeli, context=kelime.text,
        accepted=[bulunan, hedef],
        expected_seconds=aspects.expected_seconds(item.aspect),
        answer_display=bulunan, explanation=aciklama,
        examples=_ornekler(item.meaning, haric=kalip.example),
        word_text=kelime.text, word_detail_id=kelime.id,
    )


def _q_false_friend(item, bicim, rng):
    yanlis_dost = item.target
    if yanlis_dost is None:
        return None

    kelime = item.word
    dogru_anlam = kelime.meaningTr or ""

    if bicim == Format.TRUE_FALSE or not dogru_anlam:
        # Doğru/yanlış biçimi tuzağı DOĞRUDAN kuruyor: öğrenciye zaten
        # kafasında olan eşitliği gösterip onaylatıyor ya da reddettiriyor.
        # Yanıldığında düzeltme, kendi yanlışının üstüne biniyor.
        return Question(
            item_id=item.id, aspect=item.aspect, format=Format.TRUE_FALSE,
            instruction="Bu eşleştirme doğru mu?",
            stem=f"{kelime.text}  =  {yanlis_dost.turkish_lookalike}",
            options=[{"key": "A", "text": "Doğru"},
                     {"key": "B", "text": "Yanlış"}],
            correct_key="B",
            expected_seconds=aspects.expected_seconds(item.aspect),
            answer_display="Yanlış",
            explanation=_yanlis_dost_aciklamasi(kelime, yanlis_dost, dogru_anlam),
            examples=_ornekler(kelime.primary_meaning),
            word_text=kelime.text, word_detail_id=kelime.id,
        )

    celdiriciler = []
    if yanlis_dost.assumed_meaning:
        celdiriciler.append(yanlis_dost.assumed_meaning)
    anlam = kelime.primary_meaning
    if anlam:
        celdiriciler += [distractors.distractor_text(c)
                         for c in distractors.meaning_distractors(anlam, 2, rng)]

    siklar, dogru = _siklar(dogru_anlam, celdiriciler, rng)
    if not siklar:
        return None

    return Question(
        item_id=item.id, aspect=item.aspect, format=Format.CHOICE,
        instruction="Bu kelime ne demek?",
        stem=kelime.text,
        context="Dikkat: Türkçeye benzeyen bir kelime",
        options=siklar, correct_key=dogru,
        expected_seconds=aspects.expected_seconds(item.aspect),
        answer_display=dogru_anlam,
        explanation=_yanlis_dost_aciklamasi(kelime, yanlis_dost, dogru_anlam),
        examples=_ornekler(anlam),
        word_text=kelime.text, word_detail_id=kelime.id,
    )


def _yanlis_dost_aciklamasi(kelime, yanlis_dost, dogru_anlam):
    satir = (f"<b>{kelime.text}</b>, Türkçedeki "
             f"<b>{yanlis_dost.turkish_lookalike}</b> demek DEĞİLDİR; "
             f"{dogru_anlam or 'başka bir anlama gelir'}.")
    if yanlis_dost.correct_english:
        satir += (f" “{yanlis_dost.turkish_lookalike}” için doğru kelime: "
                  f"<b>{yanlis_dost.correct_english}</b>.")
    if yanlis_dost.note:
        satir += f" {yanlis_dost.note}"
    return satir


def _q_confusable(item, bicim, rng):
    bag = item.target
    if bag is None:
        return None

    # Soru her tekrarda ters yönden de sorulabilsin diye iki kelimeden
    # biri rastgele "sorulan" seçiliyor. Yalnızca tek yönden sorulursa
    # öğrenci `affect`i öğrenir, `effect`i öğrenmez — oysa ayrım
    # çift yönlüdür.
    ciftler = [(bag.from_word, bag.to_word), (bag.to_word, bag.from_word)]
    rng.shuffle(ciftler)

    for sorulan, oteki in ciftler:
        anlam = sorulan.primary_meaning
        if anlam is None:
            continue
        cumleler = [c.text for c in anlam.examples.all()]
        rng.shuffle(cumleler)
        yazimlar = masking.surfaces_for_word(sorulan)
        for cumle in cumleler:
            maskeli, bulunan = masking.blank_word(cumle, yazimlar)
            if not maskeli:
                continue
            siklar, dogru = _siklar(sorulan.text, [oteki.text], rng)
            if not siklar:
                continue
            aciklama = (f"<b>{sorulan.text}</b>: {sorulan.meaningTr}<br>"
                        f"<b>{oteki.text}</b>: {oteki.meaningTr}")
            if bag.note:
                aciklama += f"<br>{bag.note}"
            return Question(
                item_id=item.id, aspect=item.aspect, format=Format.PAIR,
                instruction="Boşluğa hangisi gelir?",
                sentence=maskeli,
                context="Bu iki kelime birbiriyle karıştırılır",
                options=siklar, correct_key=dogru,
                expected_seconds=aspects.expected_seconds(item.aspect),
                answer_display=bulunan,
                explanation=aciklama,
                examples=_ornekler(anlam, haric=cumle),
                word_text=sorulan.text, word_detail_id=sorulan.id,
            )
    return None


def _q_nuance(item, bicim, rng):
    anlam = item.meaning
    if anlam is None or anlam.sentiment == Sentiment.NEUTRAL:
        return None

    kelime = item.word

    dogru_metin = anlam.get_sentiment_display()
    tum_secenekler = [etiket for _kod, etiket in Sentiment.choices]
    baslik = "Bu kelimenin TONU nedir?"
    aciklama = (f"<b>{kelime.text}</b> — {anlam.meaning_tr} · "
                f"ton: <b>{dogru_metin}</b>. Türkçe karşılık bu bilgiyi "
                f"taşımaz: aynı Türkçeye çevrilen iki kelimenin tonu zıt "
                f"olabilir (famous / notorious).")
    if anlam.register != Register.NEUTRAL:
        aciklama += f" Üslup: <b>{anlam.get_register_display()}</b>."

    celdiriciler = [s for s in tum_secenekler if s != dogru_metin]
    rng.shuffle(celdiriciler)
    siklar, dogru = _siklar(dogru_metin, celdiriciler[:3], rng)
    if not siklar:
        return None

    return Question(
        item_id=item.id, aspect=item.aspect, format=Format.CHOICE,
        instruction=baslik,
        stem=kelime.text,
        context=anlam.meaning_tr,
        options=siklar, correct_key=dogru,
        expected_seconds=aspects.expected_seconds(item.aspect),
        answer_display=dogru_metin,
        explanation=aciklama,
        examples=_ornekler(anlam),
        word_text=kelime.text, word_detail_id=kelime.id,
    )


def _q_family(item, bicim, rng):
    kelime = item.word
    if not kelime.family_id:
        return None

    uyeler = [u for u in kelime.family.words.all()]
    if len(uyeler) < 2:
        return None

    # Aile sorusunun sorulduğu cümle, ailenin BAŞKA bir üyesine ait
    # olmalı: öğrenci cümleye hangi türevin gireceğini seçecek.
    rng.shuffle(uyeler)
    for hedef in uyeler:
        anlam = hedef.primary_meaning
        if anlam is None:
            continue
        cumleler = [c.text for c in anlam.examples.all()]
        rng.shuffle(cumleler)
        yazimlar = masking.surfaces_for_word(hedef)
        for cumle in cumleler:
            maskeli, bulunan = masking.blank_word(cumle, yazimlar)
            if not maskeli:
                continue

            digerleri = [u.text for u in uyeler if u.id != hedef.id][:3]
            aciklama = "Aile: " + " · ".join(
                f"<b>{u.text}</b> ({u.get_pos_display()})" for u in uyeler
            )

            if bicim == Format.CHOICE:
                siklar, dogru = _siklar(hedef.text, digerleri, rng)
                if not siklar:
                    continue
                return Question(
                    item_id=item.id, aspect=item.aspect, format=Format.CHOICE,
                    instruction="Cümleye ailenin hangi üyesi girer?",
                    sentence=maskeli,
                    context=f"{kelime.family.root} ailesi",
                    options=siklar, correct_key=dogru,
                    expected_seconds=aspects.expected_seconds(item.aspect),
                    answer_display=bulunan,
                    explanation=aciklama,
                    examples=_ornekler(anlam, haric=cumle),
                    word_text=hedef.text, word_detail_id=hedef.id,
                )

            # Bağlam satırında Türkçe anlam GÖSTERİLMİYOR: aile
            # sorusunda anlamı vermek cevabı vermektir. Gösterilen tek
            # ipucu, cümleye hangi TÜRÜN gireceği — asıl sorulan da bu.
            return Question(
                item_id=item.id, aspect=item.aspect, format=Format.BLANK,
                instruction=f"Boşluğa “{kelime.family.root}” ailesinden "
                            f"uygun kelimeyi yaz:",
                sentence=maskeli,
                context=f"aranan tür: {hedef.get_pos_display()}",
                accepted=yazimlar,
                expected_seconds=aspects.expected_seconds(item.aspect),
                answer_display=bulunan,
                explanation=aciklama,
                examples=_ornekler(anlam, haric=cumle),
                word_text=hedef.text, word_detail_id=hedef.id,
            )
    return None


def _q_form(item, bicim, rng):
    kelime = item.word
    if not kelime.v2Form:
        return None

    v2 = kelime.v2Form
    v3 = kelime.v3Form or v2

    if bicim == Format.CHOICE:
        from words.models import Word

        adaylar = list(Word.objects
                       .filter(pos=kelime.pos)
                       .exclude(id=kelime.id)
                       .exclude(v2Form__isnull=True).exclude(v2Form="")
                       .values_list("v2Form", flat=True)[:40])
        rng.shuffle(adaylar)
        siklar, dogru = _siklar(v2, adaylar[:3], rng)
        if siklar:
            return Question(
                item_id=item.id, aspect=item.aspect, format=Format.CHOICE,
                instruction="Bu fiilin 2. hâli hangisi?",
                stem=kelime.text,
                context=kelime.meaningTr,
                options=siklar, correct_key=dogru,
                expected_seconds=aspects.expected_seconds(item.aspect),
                answer_display=v2,
                explanation=f"<b>{kelime.text} · {v2} · {v3}</b>",
                examples=_ornekler(kelime.primary_meaning),
                word_text=kelime.text, word_detail_id=kelime.id,
            )

    # Yazarak: ikisi birden isteniyor. Ayrı ayrı sormak kartı ikiye
    # bölerdi; oysa düzensiz fiil ezberi zaten üçlü olarak yapılıyor.
    kabul = [f"{v2} {v3}", f"{v2}, {v3}", f"{v2}-{v3}"]
    if v2.lower() == v3.lower():
        kabul.append(v2)

    return Question(
        item_id=item.id, aspect=item.aspect, format=Format.TYPE,
        instruction="Bu fiilin 2. ve 3. hâlini yaz:",
        stem=kelime.text,
        context=kelime.meaningTr,
        accepted=kabul,
        hint=f"{v2[0]}… {v3[0]}…",
        expected_seconds=aspects.expected_seconds(item.aspect),
        answer_display=f"{v2} · {v3}",
        explanation=f"<b>{kelime.text} · {v2} · {v3}</b>",
        examples=_ornekler(kelime.primary_meaning),
        word_text=kelime.text, word_detail_id=kelime.id,
    )


URETICILER = {
    Aspect.RECOGNIZE: _q_recognize,
    Aspect.PRODUCE: _q_produce,
    Aspect.CONTEXT: _q_context,
    Aspect.COLLOCATION: _q_collocation,
    Aspect.PATTERN: _q_pattern,
    Aspect.FALSE_FRIEND: _q_false_friend,
    Aspect.CONFUSABLE: _q_confusable,
    Aspect.NUANCE: _q_nuance,
    Aspect.FAMILY: _q_family,
    Aspect.FORM: _q_form,
}


def _kararli_rng(item):
    """
    Karta özel, TEKRARLANABİLİR rastgelelik.

    Bu tohum bir ayrıntı değil, doğruluk meselesi: soru bir kez ekrana
    basılırken, bir kez de cevap değerlendirilirken üretiliyor. Rastgele
    tohumla ikisi farklı çıkar — şıklar karışır, doğru şıkkın anahtarı
    değişir ve doğru cevap veren öğrenci yanlış yapmış sayılır.

    Tohum (kart id + tekrar sayısı): aynı kart aynı tekrarda hep aynı
    soruyu verir, tekrar sayısı artınca soru değişir.
    """
    return random.Random((item.id * 1000003) ^ (item.reps * 97))


def build(item, rng=None, format_override=None):
    """
    Karttan soru üretir; üretilemezse None.

    Biçim, kartın kaçıncı tekrarı olduğuna göre sırayla dönüyor
    (bkz. aspects.format_for_rep). None dönmesi hata değil: kelimenin o
    boyutta yeterli verisi yok demektir ve oturum kartı atlar.
    """
    rng = rng or _kararli_rng(item)
    uretici = URETICILER.get(item.aspect)
    if uretici is None:
        return None

    bicim = format_override or aspects.format_for_rep(item.aspect, item.reps)
    try:
        return uretici(item, bicim, rng)
    except Exception:  # pragma: no cover
        # Tek bir bozuk kayıt bütün oturumu düşürmemeli.
        return None
