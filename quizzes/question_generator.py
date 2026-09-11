# quizzes/question_generator.py
import random
import re

from .models import (
    MultipleChoiceQuestion,
    WritingQuestion,
    MatchingQuestion,
    SynonymAntonymQuestion,
    FillInTheBlankQuestion,
)
from words.models import Word

# Boşluk doldurma sorularında kullanılan boşluk işareti
BLANK = FillInTheBlankQuestion.BLANK


# ---------------------------------------------------------------------------
# Cümlede kelimeyi maskeleme (boşluk doldurma soruları için)
# ---------------------------------------------------------------------------

def _inflected_forms(base):
    """
    Bir kelimenin cümlede geçebileceği yaygın çekimli hâllerini üretir.

    Örnek cümlelerde kelimenin kök hâli değil çekimli hâli geçiyor olabilir
    ("retain" -> "The company retained..."), bu yüzden sadece kök hâli aramak
    soruların çoğunun üretilememesine yol açardı.

    Türetimsel ekler (-ment, -tion, -ness) bilinçli olarak üretilmiyor; onlar
    çoğu zaman farklı bir kelime demek.
    """
    base = (base or "").strip()
    if not base or " " in base:
        # Çok kelimeli girdilerde (phrasal verb vb.) çekim tahmini yapma;
        # bu durumda v2Form/v3Form alanlarına güveniyoruz.
        return []

    forms = set()
    vowels = "aeiou"

    forms.add(base + "s")
    forms.add(base + "es")
    forms.add(base + "ing")
    forms.add(base + "ed")
    forms.add(base + "er")
    forms.add(base + "est")
    forms.add(base + "ly")

    if base.endswith("e") and len(base) > 2:
        stem = base[:-1]
        forms.add(stem + "ing")
        forms.add(base + "d")

    if base.endswith("y") and len(base) > 2 and base[-2] not in vowels:
        stem = base[:-1]
        forms.add(stem + "ies")
        forms.add(stem + "ied")
        forms.add(stem + "ier")
        forms.add(stem + "iest")
        forms.add(stem + "ily")

    # Son sessizin ikizlenmesi: stop -> stopped / stopping
    if (
        len(base) >= 3
        and base[-1] not in vowels
        and base[-1] not in "wxy"
        and base[-2] in vowels
        and base[-3] not in vowels
    ):
        doubled = base + base[-1]
        forms.add(doubled + "ed")
        forms.add(doubled + "ing")
        forms.add(doubled + "er")

    forms.discard(base)
    return sorted(forms)


def _surface_forms(word_obj, include_inflections=True):
    """
    Kelimenin cümlede aranacak yüzey biçimleri; uzundan kısaya sıralı.

    Sıralama önemli: önce "retained" denenmezse "retain" eşleşir ve cümlede
    ortada "ed" kalıntısı kalır.
    """
    base = (word_obj.englishWord or "").strip()
    forms = {base} if base else set()

    for extra in (word_obj.v2Form, word_obj.v3Form):
        if extra and extra.strip():
            forms.add(extra.strip())

    if include_inflections:
        forms.update(_inflected_forms(base))

    return sorted((f for f in forms if f), key=len, reverse=True)


def _mask_forms_in_sentence(sentence, forms):
    """
    Cümlede verilen biçimlerden ilk eşleşeni boşluğa çevirir.

    Başarılıysa (boşluklu_cümle, maskelenen_yüzey_biçim) döner; hiçbiri
    bulunamazsa None döner. Bulunamayan kelime için soru ÜRETİLMEZ — bozuk
    soru göstermektense hiç göstermemek daha iyi.
    """
    sentence = (sentence or "").strip()
    if not sentence:
        return None

    for form in forms:
        pattern = re.compile(r"\b" + re.escape(form) + r"\b", re.IGNORECASE)
        match = pattern.search(sentence)
        if match:
            masked = sentence[: match.start()] + BLANK + sentence[match.end():]
            return masked, match.group(0)

    return None


def build_blank_for_word(word_obj, include_inflections=True, randomize=True):
    """
    Kelime için boşluklu bir cümle üretir.

    Kelimenin DOLU olan örnek cümleleri arasından rastgele seçer. Aynı kelime
    her sorulduğunda aynı cümleyi görmek, kelimeyi tek bir bağlama bağlar;
    oysa amaç kelimeyi farklı kullanımlarda tanımak. Boş cümle alanları
    `Word.example_sentences` tarafından zaten süzülüyor.

    Örnek cümlelerin hiçbirinde kelime bulunamazsa collocation'lara düşer.

    Dönen değer: (boşluklu_metin, maskelenen_biçim) veya None.
    `randomize=False` deterministik sonuç verir (uygunluk kontrolü ve testler).
    """
    forms = _surface_forms(word_obj, include_inflections=include_inflections)
    if not forms:
        return None

    sentences = list(word_obj.example_sentences)
    if randomize:
        random.shuffle(sentences)

    for sentence in sentences:
        result = _mask_forms_in_sentence(sentence, forms)
        if result:
            return result

    # Örnek cümlelerde bulunamadıysa collocation'lardan boşluk üret
    if word_obj.collocations:
        collocations = [c.strip() for c in word_obj.collocations.split(",") if c.strip()]
        if randomize:
            random.shuffle(collocations)
        for collocation in collocations:
            result = _mask_forms_in_sentence(collocation, forms)
            if result:
                return result

    return None


def can_generate_blank(word_obj, include_inflections=True):
    """
    Bu kelimeden boşluk doldurma sorusu üretilebilir mi?

    Uygunluk kontrolü olduğu için karıştırmaya gerek yok: ilk eşleşmede
    döner, böylece kelime listesi üzerinde gezerken gereksiz iş yapılmaz.
    """
    return build_blank_for_word(
        word_obj, include_inflections=include_inflections, randomize=False
    ) is not None


def _fill_from_base_words(field_name, exclude_values, needed, exclude_ids=()):
    """
    (Yardımcı Fonksiyon)
    Kullanıcının kendi listesi yeterli çeldirici üretemediğinde, site genelindeki
    'base' (kur seviyesi) kelimelerden eksik çeldiricileri tamamlar.
    Böylece kullanıcıya "Yanlış Seçenek 1" gibi sahte şıklar gösterilmez.
    """
    if needed <= 0:
        return []

    taken = {str(v).strip().lower() for v in exclude_values if v}

    qs = (
        Word.objects
        .filter(isBaseWord=True)
        .exclude(id__in=list(exclude_ids))
        .exclude(**{f"{field_name}__isnull": True})
        .exclude(**{f"{field_name}": ""})
        .order_by("?")
        .values_list(field_name, flat=True)[: max(needed * 10, 30)]
    )

    extra = []
    for value in qs:
        if not value:
            continue
        key = str(value).strip().lower()
        if key in taken:
            continue
        taken.add(key)
        extra.append(value)
        if len(extra) >= needed:
            break

    return extra


def _get_distractors(correct_word_obj, all_words, field_name, count=3):
    """
    (Yardımcı Fonksiyon)
    Bir kelime için belirtilen 'field_name' (örn: 'meaningTr', 'englishWord') 
    üzerinden 'çeldiriciler' (yanlış şıklar) üretir.
    """
    # getattr: obj.alan_adı demekle aynıdır (ama alan_adı değişkenden gelir)
    correct_value = getattr(correct_word_obj, field_name)
    
    distractor_pool = []
    for word in all_words:
        # Kendisi olmasın
        if word.id == correct_word_obj.id:
            continue
            
        # Alandan değeri al (örn: word.meaningTr)
        value = getattr(word, field_name, None) 
        
        # Değer boş değilse ve doğru cevapla aynı değilse havuza ekle
        if value and value != correct_value:
            distractor_pool.append(value)
    
    # Havuzdaki çeldiricileri benzersiz yap
    distractors = list(set(distractor_pool))
    
    # Yeterli çeldirici varsa, oradan 'count' tane seç
    if len(distractors) >= count:
        return random.sample(distractors, count)
    
    # Yeterli yoksa eksiği site genelindeki 'base' kelimelerden tamamla.
    # (Eskiden "Yanlış Seçenek 1" gibi sahte şıklar üretiliyordu.)
    needed = count - len(distractors)
    if needed > 0:
        distractors.extend(
            _fill_from_base_words(
                field_name,
                distractors + [correct_value],
                needed,
                exclude_ids=[correct_word_obj.id],
            )
        )

    # Hâlâ eksikse sahte şık uydurmak yerine daha az şıklı soru üretilir.
    return distractors[:count]


def generate_mc_question(word_link, attempt, all_words):
    """
    Verilen word_link için 4 FARKLI TİPTE Çoktan Seçmeli soru 
    objesi oluşturur ve kaydeder.
    """
    
    word_obj = word_link.word
    
    # 1. Olası soru tiplerini tanımla
    question_types = [
        'word_to_meaning',   # bu kelimenin anlamı?
        'meaning_to_word',   # bu anlama gelen kelime?
    ]
    
    # 2. Sadece 'explanation' alanı doluysa bu tipleri de ekle
    if word_obj.explanation:
        question_types.append('word_to_explanation') # bu kelimenin en iyi açıklaması?
        question_types.append('explanation_to_word') # açıklamaya uyan kelime?

    # 3. Örnek cümlede kelimenin KÖK hâli geçiyorsa boşluk doldurma da sorulabilir.
    # Çekimli hâller bilerek kullanılmıyor: şıklar kök hâl olduğu için boşluğa
    # dilbilgisel olarak oturmaları gerekiyor ("managed to ___ its customers").
    blank = build_blank_for_word(word_obj, include_inflections=False)
    if blank:
        question_types.append('cloze')

    # 4. Olası tiplerden birini rastgele seç
    chosen_type = random.choice(question_types)

    # 4. Seçilen tipe göre soruyu ve çeldiricileri hazırla
    
    if chosen_type == 'word_to_meaning':
        # "bu kelimenin anlamı?"
        question_text = f"'{word_obj.englishWord}' kelimesinin Türkçe anlamı nedir?"
        correct_answer = word_obj.meaningTr
        distractors = _get_distractors(word_obj, all_words, 'meaningTr', 3)
        
    elif chosen_type == 'meaning_to_word':
        # "bu anlama gelen kelime?"
        question_text = f"'{word_obj.meaningTr}' Türkçe anlamına gelen İngilizce kelime hangisidir?"
        correct_answer = word_obj.englishWord
        distractors = _get_distractors(word_obj, all_words, 'englishWord', 3)

    elif chosen_type == 'word_to_explanation':
        # "bu kelimenin en iyi açıklaması?"
        question_text = f"'{word_obj.englishWord}' kelimesini en iyi açıklayan ifade hangisidir?"
        correct_answer = word_obj.explanation
        distractors = _get_distractors(word_obj, all_words, 'explanation', 3)

    elif chosen_type == 'explanation_to_word':
        # "açıklamaya uyan kelime?"
        question_text = f"Aşağıdaki açıklamaya uyan kelime hangisidir?\n'{word_obj.explanation}'"
        correct_answer = word_obj.englishWord
        distractors = _get_distractors(word_obj, all_words, 'englishWord', 3)

    elif chosen_type == 'cloze':
        # "boşluğa uygun kelime?" — kelimeyi bağlam içinde sorar
        masked_sentence, _matched_form = blank
        question_text = f"Boşluğa uygun kelimeyi seçiniz:\n'{masked_sentence}'"
        correct_answer = word_obj.englishWord
        distractors = _get_distractors(word_obj, all_words, 'englishWord', 3)

    # 5. Seçenekleri birleştir ve karıştır
    options_list = distractors + [correct_answer]
    random.shuffle(options_list)
    
    # Çeldirici sayısı azsa daha az şıklı (ör. 3 şıklı) soru üretilir
    option_labels = ["A", "B", "C", "D"][:len(options_list)]
    
    # "A:koşmak;B:yemek;C:içmek;D:uyumak" formatını oluşturalım
    safe_delimiter = "_#_" # Güvenli bir ayraç
    options_data = safe_delimiter.join([f"{label}:{option}" for label, option in zip(option_labels, options_list)])
    
    # Doğru cevabın hangi harf olduğunu bulalım
    correct_label = ""
    for label, option in zip(option_labels, options_list):
        if option == correct_answer:
            correct_label = label
            break
            
    # 6. Soruyu veritabanında oluştur
    q = MultipleChoiceQuestion.objects.create(
        attempt=attempt,
        question_text=question_text,
        options_data=options_data,
        correct_option=correct_label
    )
    q.words.set([word_obj]) # M2M ilişkiyi kur


def generate_writing_question(word_link, attempt):
    """
    (DEĞİŞİKLİK YOK - İsteğiniz üzerine)
    Verilen word_link için bir WritingQuestion objesi oluşturur ve kaydeder.
    """
    
    word_obj = word_link.word
    
    # Şimdilik hep "anlamı ver, kelimeyi bul" yapalım
    # Siz burayı da 'explanation' kullanarak çeşitlendirebilirsiniz.
    question_text = f"Türkçe anlamı '{word_obj.meaningTr}' ve İngilizce açıklaması '{word_obj.explanation}' olan İngilizce kelimeyi yazınız."
    correct_answer = word_obj.englishWord
    
    q = WritingQuestion.objects.create(
        attempt=attempt,
        question_text=question_text,
        correct_answer=correct_answer
    )
    q.words.set([word_obj]) # M2M ilişkiyi kur


def generate_matching_question(link_group, attempt):
    """
    Verilen 5'li link grubu için FARKLI TİPTE Eşleştirme sorusu 
    objesi oluşturur ve kaydeder.
    """
    
    words_list = [link.word for link in link_group]
    
    # 1. Olası formatları tanımla
    # 'word_meaning' -> Kelime (sol) <-> Anlam (sağ)
    # 'meaning_word' -> Anlam (sol) <-> Kelime (sağ)
    possible_formats = ['word_meaning', 'meaning_word'] 
    
    # 2. Kenar Durumu Kontrolü: Gruptaki 5 kelimenin HEPSİNDE açıklama var mı?
    if all(w.explanation for w in words_list):
        # 'word_explanation' -> Kelime (sol) <-> Açıklama (sağ)
        possible_formats.append('word_explanation')
        
    # 3. Olası formatlardan birini rastgele seç
    chosen_format = random.choice(possible_formats)

    # 4. Seçilen formata göre alan adlarını ve soru metnini ata
    if chosen_format == 'word_meaning':
        question_text = "İngilizce kelimeleri Türkçe anlamlarıyla eşleştiriniz."
        left_col_field_name = 'englishWord'
        right_col_field_name = 'meaningTr'
        
    elif chosen_format == 'meaning_word':
        # İsteğiniz: "anlam-kelime"
        question_text = "Türkçe anlamları İngilizce kelimelerle eşleştiriniz."
        left_col_field_name = 'meaningTr'
        right_col_field_name = 'englishWord'
        
    elif chosen_format == 'word_explanation':
        # İsteğiniz: "kelime-açıklama"
        question_text = "İngilizce kelimeleri açıklamalarıyla eşleştiriniz."
        left_col_field_name = 'englishWord'
        right_col_field_name = 'explanation'

    # 5. Sağ sütunun sırasını karıştır (öncekiyle aynı mantık)
    ids_list = [w.id for w in words_list]
    random.shuffle(ids_list)
    right_col_ids_str = ";".join(map(str, ids_list))
    
    # 6. Soruyu veritabanında oluştur (artık dinamik alan adlarıyla)
    q = MatchingQuestion.objects.create(
        attempt=attempt,
        question_text=question_text,
        left_col_field=left_col_field_name, # Dinamik
        right_col_field=right_col_field_name, # Dinamik
        right_col_order_ids=right_col_ids_str,
        word_count=len(words_list),
    )
    q.words.set(words_list) # 5 kelimeyi de M2M ilişkiye ekle


def generate_synonym_antonym_question(word_link, attempt, all_words):
    """
    Verilen word_link için bir SynonymAntonymQuestion oluşturur.
    Kelimenin eş anlamlısı veya zıt anlamlısı rastgele seçilip sorulur.
    Doğru cevap: kaydedilmiş eş/zıt anlamlılardan biri.
    Çeldiriciler: kullanıcının listesindeki diğer kelimelerin İngilizce halleri.
    """
    word_obj = word_link.word

    # Hangi soru tipinin sorulabileceğini belirle
    has_synonyms = bool(word_obj.synonyms and word_obj.synonyms.strip())
    has_antonyms = bool(word_obj.antonyms and word_obj.antonyms.strip())

    question_types = []
    if has_synonyms:
        question_types.append('synonym')
    if has_antonyms:
        question_types.append('antonym')

    if not question_types:
        return  # Bu kelimede ne eş ne de zıt anlamlı yok; soru atlanır

    chosen_type = random.choice(question_types)

    if chosen_type == 'synonym':
        synonyms_list = [s.strip() for s in word_obj.synonyms.split(',') if s.strip()]
        correct_answer = random.choice(synonyms_list)
        question_text = (
            f"Aşağıdakilerden hangisi '{word_obj.englishWord}' kelimesinin "
            f"eş anlamlısıdır (synonym)?"
        )
    else:  # antonym
        antonyms_list = [a.strip() for a in word_obj.antonyms.split(',') if a.strip()]
        correct_answer = random.choice(antonyms_list)
        question_text = (
            f"Aşağıdakilerden hangisi '{word_obj.englishWord}' kelimesinin "
            f"zıt anlamlısıdır (antonym)?"
        )

    # Çeldiricileri kullanıcının listesindeki İngilizce kelimelerden üret
    distractor_pool = []
    for word in all_words:
        if word.id == word_obj.id:
            continue
        eng = word.englishWord
        if eng and eng.lower() != correct_answer.lower():
            distractor_pool.append(eng)

    distractor_pool = list(set(distractor_pool))

    if len(distractor_pool) >= 3:
        distractors = random.sample(distractor_pool, 3)
    else:
        # Eksik çeldiricileri site genelindeki base kelimelerden tamamla
        distractors = distractor_pool[:]
        needed = 3 - len(distractors)
        distractors.extend(
            _fill_from_base_words(
                'englishWord',
                distractors + [correct_answer, word_obj.englishWord],
                needed,
                exclude_ids=[word_obj.id],
            )
        )

    # Seçenekleri birleştir, karıştır, etiketle
    options_list = distractors + [correct_answer]
    random.shuffle(options_list)

    option_labels = ["A", "B", "C", "D"][:len(options_list)]
    safe_delimiter = "_#_"
    options_data = safe_delimiter.join(
        [f"{label}:{option}" for label, option in zip(option_labels, options_list)]
    )

    correct_label = ""
    for label, option in zip(option_labels, options_list):
        if option == correct_answer:
            correct_label = label
            break

    q = SynonymAntonymQuestion.objects.create(
        attempt=attempt,
        question_text=question_text,
        options_data=options_data,
        correct_option=correct_label,
    )
    q.words.set([word_obj])


def generate_fill_blank_question(word_link, attempt):
    """
    Verilen word_link için bir FillInTheBlankQuestion oluşturur.

    Kelime için boşluk üretilemiyorsa (örnek cümlelerde ve collocation'larda
    kelimenin hiçbir biçimi bulunamadıysa) hiçbir şey oluşturmaz ve False döner.
    Çağıran taraf bu durumu ele almalıdır.
    """
    word_obj = word_link.word

    blank = build_blank_for_word(word_obj)
    if not blank:
        return False

    masked_sentence, matched_form = blank

    # Kök hâl ve cümlede geçen çekimli hâl; ikisi de kabul edilir.
    # (Amaç kelimeyi bilip bilmediğini ölçmek, çekimi doğru yazıp yazmadığını değil.)
    accepted = []
    for candidate in (word_obj.englishWord, matched_form):
        cleaned = (candidate or "").strip()
        if cleaned and cleaned.lower() not in {a.lower() for a in accepted}:
            accepted.append(cleaned)

    q = FillInTheBlankQuestion.objects.create(
        attempt=attempt,
        sentence_with_blank=masked_sentence,
        correct_answer=matched_form,
        accepted_answers=",".join(accepted),
        hint=word_obj.meaningTr,
    )
    q.words.set([word_obj])
    return True
