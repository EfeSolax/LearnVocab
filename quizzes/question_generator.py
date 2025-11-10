# quizzes/question_generator.py
import random
from .models import MultipleChoiceQuestion, WritingQuestion, MatchingQuestion
from words.models import Word

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
    
    # Yeterli yoksa, olanları al ve sahte/basit çeldiricilerle tamamla
    needed = count - len(distractors)
    if needed > 0:
        # Bu kısmı daha sonra geliştirebilirsiniz
        distractors.extend([f"Yanlış Seçenek {i+1}" for i in range(needed)])
        
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

    # 3. Olası tiplerden birini rastgele seç
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

    # 5. Seçenekleri birleştir ve karıştır
    options_list = distractors + [correct_answer]
    random.shuffle(options_list)
    
    option_labels = ["A", "B", "C", "D"]
    
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
        right_col_order_ids=right_col_ids_str
    )
    q.words.set(words_list) # 5 kelimeyi de M2M ilişkiye ekle
    