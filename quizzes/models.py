# Django importları
from django.db import models
from django.db.models import F
from django.db.models.expressions import RawSQL
from django.db.models import Sum

# Karşılaştırma için gerekli importlar
from difflib import SequenceMatcher
import re

# Gerekli model importları
from users.models import User
from words.models import Word, UserWordLink

# Quiz tipini belirten class (extends TextChoices)
class QuizType(models.TextChoices):
    MATCHING = 'matching', 'Eşleştirme'
    MULTIPLE_CHOICE = 'multiple_choice', 'Çoktan Seçmeli'
    WRITING = 'writing', 'Yazma'
    MIXED = 'mixed', 'Karma'
    RANDOM = "random", "Rastgele"

# QuizAttempt (isteği) oluşturulan class 
class QuizAttempt(models.Model):
    # Quiz'in sahibi User, ondelete=CASCADE (otomatik silinme)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="quizAttempts")

    # Oluşturulduğu zaman auto_now_add, quiz tamamlandı mı (otomatik false)
    createdAt = models.DateTimeField(auto_now_add=True)
    isCompleted = models.BooleanField(default = False)

    # Quiz'de kaç soru var, kaçı doğru kaçı yanlış bilindi
    totalQuestion = models.IntegerField()
    totalCorrect = models.IntegerField(default=0)
    totalWrong = models.IntegerField(default=0)

    # QuizType yukarıdaki class'tan seçilecek
    quizType = models.CharField(max_length=20, choices= QuizType.choices, default=QuizType.MIXED)

    # QuizAttempt'in nasıl görüneceği (kullanıcı adı, quiz tipini göster, oluşturulduğu tarih)
    def __str__(self):
        return f"{self.owner.username} - {self.get_quizType_display()} ({self.createdAt.strftime('%d-%m-%Y')})"
    
    # Toplam boş sayısını döndür (toplam - doğru - yanlış)
    def totalEmpty(self):
        return self.totalQuestion - (self.totalCorrect + self.totalWrong)

    # Doğru sayısı hesaplama fonksiyonu
    def calculateScore(self):
        # Çoktan seçmeli ve yazma sorularındaki doğruları say ve eşleştirmede doğru eşleştirmeleri say
        mc_correct = self.multiplechoicequestion_questions.filter(is_correct=True).count()
        wq_correct = self.writingquestion_questions.filter(is_correct=True).count()
        mq_correct_sum_agg = self.matchingquestion_questions.aggregate(Sum('correct_matches'))
        mq_correct_sum = mq_correct_sum_agg['correct_matches__sum'] or 0
        
        # Toplam doğru sayısını bunların toplamına eşitle
        self.totalCorrect = mc_correct + wq_correct + mq_correct_sum

        # Çoktan seçmeli ve yazma sorularında yanlış yapılanları say        
        mc_wrong = self.multiplechoicequestion_questions.filter(is_correct=False).count()
        wq_wrong = self.writingquestion_questions.filter(is_correct=False).count()
        
        # Eşleştirme sorularında yanlış eşleştirilen soruları say
        mq_wrong_sum_agg = self.matchingquestion_questions.aggregate(Sum('wrong_matches'))
        mq_wrong_sum = mq_wrong_sum_agg['wrong_matches__sum'] or 0
        
        # Toplam yanlış sayısını bunların toplaımına eşitle 
        self.totalWrong = mc_wrong + wq_wrong + mq_wrong_sum
        
        # Quiz bitirildi mi'yi True yap ve quiz attempt'i kaydet.
        self.isCompleted = True
        self.save()

    # Toplam geçen süreyi alan fonksiyon
    @property
    def total_time_taken(self):
        # Tüm soru tiplerinde geçen süreyi al e bunları topla ve dön
        mc_time = self.multiplechoicequestion_questions.all().aggregate(Sum('time_taken'))['time_taken__sum'] or 0
        wq_time = self.writingquestion_questions.all().aggregate(Sum('time_taken'))['time_taken__sum'] or 0
        mq_time = self.matchingquestion_questions.all().aggregate(Sum('time_taken'))['time_taken__sum'] or 0
        return mc_time + wq_time + mq_time

    # Geçen toplam süreyi gösteren fonskiyon
    @property
    def formatted_total_time(self) -> str:
        # Toplam geçen süreyi al ve bu süre 0 ise 0 dön
        total_seconds = int(self.total_time_taken)

        if total_seconds == 0:
            return "0 sn"
        
        # Toplam dakikayı ve kalan saniyeyi bul ve dakika 0'dan farklıysa bunu dön, yoksa 
        # geçen süreyi saniye olarak dön
        minutes = total_seconds // 60
        seconds = total_seconds % 60

        if minutes > 0:
            return f"{minutes} dk {seconds} sn"
        return f"{seconds} sn"
        
# Tüm QuizQuestionların extend ettiği abstract question modeli
class QuizQuestion(models.Model):
    # Bu soruyu içeren quizattempt objesi
    attempt = models.ForeignKey(
        QuizAttempt,
        on_delete=models.CASCADE,
        related_name="%(class)s_questions" 
    )
    # attempt.questions.all() HATA VERİR, çünkü bu abstract bir class. Bunun yerine 
    # attempt.multiplechoicequestion_set.all() gibi sorgular yapmak gerekir 
    # Bu yüzden related_name ile soruları (class)'ın adını yazdıktan sonra alabiliriz
    
    # Quiz'de kullanılan kelimeleri al
    words = models.ManyToManyField(Word, related_name="%(class)s_quiz_questions")

    # Kullanıcının cevapları (tüm cevaplar bir charfield olarak tutulacak)
    user_answer = models.CharField(max_length=250, blank=True, null=True)

    # Sorunun doğru olup olmadığı bilgisi ve soruda geçen süre
    is_correct = models.BooleanField(default=False)
    time_taken = models.FloatField(null=True, blank=True, help_text="Süreyi saniye cinsinden saklar")

    class Meta:
        abstract = True # Bu model için veritabanında tablo OLUŞTURULMAYACAK.
        ordering = ['id'] # Soruların sıralı gelmesi için

    # Tüm alt sınıflar için ortak istatistik güncelleme metodu
    def update_word_stats(self):
        # Attempt'in sahibinin bu kelime ile olan ilişkisini tutan wordlink'i al 
        links = UserWordLink.objects.filter(user=self.attempt.owner, word__in=self.words.all())
        
        # F() expression kullanarak veri tabanındaki güncellemeleri kesikli yapıyoruz.
        # Böylece aynı anda veriler güncellenemeyecek.
        # Soru doğruysa veya yanlışsa kullanıcının bu soruları kaç kere doğru veya 
        # yanlış yaptığının bilgisini güncelle.
        if self.is_correct: links.update(correctCount=F('correctCount') + 1)
        else: links.update(wrongCount=F('wrongCount') + 1)

    # Bu metot her alt sınıf tarafından override edilmeli yoksa hata fırlatır
    def check_answer(self, user_input, time_taken=None):
        raise NotImplementedError("check_answer() metodu alt sınıfta tanımlanmalıdır.")

# Çoktan seçmeli soruların modeli (Question abstract class'ını extend ediyor)
class MultipleChoiceQuestion(QuizQuestion):

    # Sorunun metni ve seçeneklerin metni ve doğru cevabın şıkkı charfield olarak tutulacak
    question_text = models.CharField(max_length=300)
    options_data = models.TextField(max_length=500)
    correct_option = models.CharField(max_length=1)

    # Şıkların tutulduğu metni şık listesine çevirir (str -> list)
    # "A:koşmak_#_B:yemek" ->  [('A', 'koşmak'), ('B', 'yemek')]
    @property
    def options_as_list(self):
        # Şıkların arasındaki ayraç
        safe_delimiter = "_#_" 
        try:
            # Option data'nın ayraca göre ayrılmış hali üzerinde gez ve bunları tuple olarak oluştur.
            return [tuple(pair.split(':', 1)) for pair in self.options_data.split(safe_delimiter)]
        
        except Exception as e:
            # Hata varsa görelim
            print(f"options_as_list HATA: {e}, Data: {self.options_data}") # Hata ayıklama için
            return []
        
    # Cevabı kontrol eden fonksiyon (kullanıcı cevabını al)
    def check_answer(self, user_input, time_taken = None):
        # Cevabı düzenle ve eğer ki doğru cevapla kullanıcınınki aynı ise doğru de
        self.user_answer = user_input.strip()
        self.is_correct = (self.user_answer == self.correct_option)

        # Geçen süre boş değilse ata 
        if time_taken is not None:
            self.time_taken = time_taken

        # Cevabı kaydet ve cevaplara göre question modelindeki kelimelerin durumunu
        # güncelle fonksiyonunu çağır
        self.save()
        self.update_word_stats() 

# Yazma sorularınun modeli (Question abstract class'ını extend ediyor)
class WritingQuestion(QuizQuestion):
    # Soru metni ve doğru cevaplar
    question_text = models.CharField(max_length=300)
    correct_answer = models.CharField(max_length=100)

    def check_answer(self, user_input, time_taken = None):
        # Kullanıcının cevabını al ve düzenle ve doğru cevabı da kullanıcının cevabını da küçült
        self.user_answer = user_input.strip()
        clean_user_input = self.user_answer.lower()
        clean_correct_answer = self.correct_answer.lower()

        # Eğer cevap ve doğru cevap tam olarak aynıysa doğru yapıldı
        if clean_user_input == clean_correct_answer:
            self.is_correct = True

        # Değilse ama 
        else:
            # Cevapta dikkate alınmayacak kelimeler (amaç kelimenin kendisi doğru yazıldı mı)
            abbreviations = {'sb', 'sth', 'smb', 'smth'}
            
            # Doğru cevaptaki "temel" kelimeleri bul ve üstteki kısaltmaları at
            correct_words_list = re.findall(r'\b[a-z0-9/-]+\b', clean_correct_answer)
            essential_correct_set = {w for w in correct_words_list if w not in abbreviations}

            # Kullanıcı girdisindeki kelimeleri bul ve üstteki kısaltmaları at
            user_words_list = re.findall(r'\b[a-z0-9/-]+\b', clean_user_input)
            essential_user_set = {w for w in user_words_list if w not in abbreviations}
            
            # Eğer cevaptaki ve doğru cevaptaki temel kelimeler aynıysa cevap doğru kabul et
            if essential_correct_set == essential_user_set:
                self.is_correct = True

            # Değilse ama 
            else:
                # Küçük yazım hataları varsa bunların oranını (ratio) tespit et
                essential_correct_str = " ".join(sorted(list(essential_correct_set)))
                essential_user_str = " ".join(sorted(list(essential_user_set)))
                ratio = SequenceMatcher(None, essential_user_str, essential_correct_str).ratio()
                
                # Benzerlik %80 ve üzerindeyse kabul et değilse yanlış
                if ratio >= 0.80:
                    self.is_correct = True
                else:
                    self.is_correct = False

        # Geçen zaman none değilse geçen zamanı ata
        if time_taken is not None:
            self.time_taken = time_taken
        
        # Cevabı kaydet ve abstract class'taki kelimeleri güncelle
        self.save()
        self.update_word_stats()
    
# Eşleştirme sorularının modeli (Question abstract class'ını extend ediyor)
class MatchingQuestion(QuizQuestion):    
    # Sorunun text'i (default var), soruda eşleştirilecek alanların kullanımı (default var)
    question_text = models.CharField(max_length=100, default="Kelimeleri eşleştiriniz.")
    left_col_field = models.CharField(max_length=50, default="englishWord")
    right_col_field = models.CharField(max_length=50, default="meaningTr")

    # Kaç tane soru tutulduğu verisi (default var)
    word_count = models.IntegerField(default=5)

    # Doğru eşleşmeler ve yanlış eşleşmeleri say
    correct_matches = models.IntegerField(default=0, help_text="Doğru eşleşen çift sayısı")
    wrong_matches = models.IntegerField(default=0, help_text="Yanlış eşleşen çift sayısı")

    # Sağ sütundaki veriler (kelime id'leri)
    right_col_order_ids = models.CharField(max_length=100)

    # Verilen kelimelerin istenilen field alanlarını alır ve liste olarak döner
    # [{'id': 123, 'text': 'run'}, {'id': 124, 'text': 'eat'}]
    def _get_items_for_column(self, word_list, field_name):
        items = []
        # Kelime listesinin içinde gez ve get attribute ile kelimenin istenen field'ını al
        # Listeye bu kelimeyi id'si ve text'iyle ekle
        for word in word_list:
            text = getattr(word, field_name, "HATA") 
            items.append({'id': word.id, 'text': text})
        return items

    # Sol sütundaki kelimeleri döner 
    @property
    def left_column_items(self):
        table_name = self.words.model._meta.db_table
        
        # RawSQL kullanarak 'id'nin hangi tabloya ait olduğunu netleştiriyoruz.
        # Çift tırnak, SQLite'ın tablo/sütun adlarını tanıması için.
        # Params için boş liste [] gönderiyoruz.
        words = self.words.all().order_by(RawSQL(f'"{table_name}"."id"', []))
        return self._get_items_for_column(words, self.left_col_field)

    # Sağ sütundaki kelimeleri karışık bir şekilde döner
    @property
    def right_column_items(self):
        # Sağ sütundaki kelimelerin id'lerini al. (;'e göre ayır) ve karıştır
        ids = self.right_col_order_ids.split(';')
        
        clauses = []
        params = []
        table_name = self.words.model._meta.db_table 
        
        for i, pk in enumerate(ids):
            clauses.append(f'WHEN "{table_name}"."id"=%s THEN %s')
            params.append(pk)
            params.append(i)
            
        ordering = 'CASE %s END' % ' '.join(clauses)
        words = self.words.all().order_by().order_by(RawSQL(ordering, params)) 
        
        return self._get_items_for_column(words, self.right_col_field)
    
    # Doğru cevapları sıralı bir şekilde dön
    @property
    def correct_column_items(self):
        table_name = self.words.model._meta.db_table
        words = self.words.all().order_by(RawSQL(f'"{table_name}"."id"', []))
        return self._get_items_for_column(words, self.right_col_field)
    
    # Kullanıcının girdiği cevapları al
    @property
    def right_column_items_user_ordered(self):

        if not self.user_answer:
            # Cevap verilmemişse (örn: süre dolmuş), boş liste dön
            return []

        # self.user_answer "sol_id:sağ_id;sol_id:sağ_id" formatındadır
        try:
            # 1. Kullanıcının cevap haritasını çıkar: {'sol_id_str': 'sağ_id_str'}
            answer_map = dict(pair.split(':') for pair in self.user_answer.split(';'))
        except ValueError:
            return [] # Hatalı format

        # 2. Sol sütunu HER ZAMAN aynı sırayla (ID sırası) al
        ordered_left_items = self.left_column_items 
        
        # 3. Sağ sütundaki TÜM kelimeleri bir haritada topla (hızlı erişim için)
        all_right_words = {str(word.id): word for word in self.words.all()}
        
        ordered_right_items = []
        for left_item in ordered_left_items:
            left_id_str = str(left_item['id'])
            # Kullanıcının bu sol öğeye karşılık hangi sağ ID'yi seçtiğini bul
            right_id_str = answer_map.get(left_id_str)
            
            # Bu ID'ye karşılık gelen kelime objesini bul
            matched_word = all_right_words.get(right_id_str)
            
            if matched_word:
                # 'item' formatıyla (sizin çiziminizdeki gibi) listeye ekle
                ordered_right_items.append({
                    'id': matched_word.id,
                    'text': getattr(matched_word, self.right_col_field, "HATA")
                })
        
        return ordered_right_items

    # Cevapları kontrol et metodu
    def check_answer(self, user_input, time_taken = None):
        self.user_answer = user_input.strip()
        if time_taken is not None:
            self.time_taken = time_taken

        # 1. Doğru cevap haritasını oluştur: {'sol_id': 'sağ_id'}
        correct_pairs_map = {str(w.id): str(w.id) for w in self.words.all()}
        
        # 2. Kullanıcı cevap haritasını oluştur
        user_pairs_map = {}
        try:
            # Gelen "1:1;2:2;..." formatını parse et
            pairs = self.user_answer.split(';')
            for pair in pairs:
                if ':' in pair: # Boş string veya hatalı formata karşı koruma
                    left_id, right_id = pair.split(':', 1)
                    user_pairs_map[left_id] = right_id
        except Exception:
            pass # Hatalı format, user_pairs_map boş kalır

        correct_word_ids = []
        wrong_word_ids = []

        # 3. Her bir kelimeyi (sol_id) tek tek kontrol et
        for left_id, correct_right_id in correct_pairs_map.items():
            user_right_id = user_pairs_map.get(left_id) # Kullanıcı bu sol_id için ne demiş?
            
            if user_right_id == correct_right_id:
                correct_word_ids.append(left_id)
            else:
                # Kullanıcı ya hiç eşleştirmemiş (None) ya da yanlış eşleştirmiş
                wrong_word_ids.append(left_id)

        # 4. YENİ alanları (correct_matches, wrong_matches) doldur
        self.correct_matches = len(correct_word_ids)
        self.wrong_matches = len(wrong_word_ids)
        
        # Eski 'is_correct' flag'ını da (tamamı doğruysa True) olarak güncelleyelim
        self.is_correct = (self.correct_matches == self.word_count and self.wrong_matches == 0)
        
        self.save() # Önce MatchingQuestion objesini kaydet
        
        # 5. İstatistikleri Toplu ve KISMİ Güncelle
        # (update_word_stats() metodunu çağırmıyoruz, çünkü o "ya hep ya hiç" idi)
        if correct_word_ids:
            UserWordLink.objects.filter(
                user=self.attempt.owner, 
                word_id__in=correct_word_ids
            ).update(correctCount=F('correctCount') + 1)
        
        if wrong_word_ids:
             UserWordLink.objects.filter(
                user=self.attempt.owner, 
                word_id__in=wrong_word_ids
            ).update(wrongCount=F('wrongCount') + 1)

        self.user_answer = user_input.strip()
        
        # 1. Doğru cevabı belirle (çok basit, M2M'deki her kelime kendisidir)
        correct_pairs_set = {f"{w.id}:{w.id}" for w in self.words.all()}
        
        # 2. Kullanıcının cevabını parse et
        try:
            user_pairs_set = set(self.user_answer.split(';'))
        except Exception:
            user_pairs_set = set() # Hatalı format

        # 3. İki seti karşılaştır
        if correct_pairs_set == user_pairs_set:
            self.is_correct = True
        else:
            self.is_correct = False

        if time_taken is not None:
            self.time_taken = time_taken # YENİ SATIR
            
        self.save()
        # ÖNEMLİ: Eşleştirmede, update_word_stats tüm 5 kelimeyi de
        # doğru veya yanlış olarak işaretleyecektir.
        self.update_word_stats()

