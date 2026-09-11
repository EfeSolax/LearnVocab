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
    SYNONYM_ANTONYM = 'synonym_antonym', 'Eş/Zıt Anlamlı'
    FILL_BLANK = 'fill_blank', 'Boşluk Doldurma'

# ---------------------------------------------------------------------------
# Bir QuizAttempt'e bağlı TÜM soru tiplerinin related_name'leri.
#
# Puanlama, süre toplama ve soru listeleme artık bu tek listeyi dolaşır.
# Yeni bir soru tipi eklerken SADECE buraya bir satır eklemek yeterli;
# eskiden aynı dört satır dört ayrı yerde elle tekrarlandığı için bir tipi
# güncellemeyi unutmak puanlamayı sessizce bozuyordu.
# ---------------------------------------------------------------------------
QUESTION_RELATED_NAMES = (
    "multiplechoicequestion_questions",
    "writingquestion_questions",
    "matchingquestion_questions",
    "synonymantonymquestion_questions",
    "fillintheblankquestion_questions",
)


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

    # Bu attempt'e ait tüm soruları oluşturulma sırasına göre döndürür
    def all_questions(self):
        """
        Quiz'deki bütün soruları (tipi ne olursa olsun) id sırasıyla döner.
        quizPage ve quizComplete bu metodu kullanır.
        """
        questions = []
        for related_name in QUESTION_RELATED_NAMES:
            questions.extend(getattr(self, related_name).all())
        questions.sort(key=lambda q: q.id)
        return questions

    # Doğru/yanlış sayısını hesaplayan fonksiyon
    def calculateScore(self):
        """
        Quiz'in toplam doğru ve yanlış sayısını hesaplar.

        Her soru kendi katkısını `correct_score` / `wrong_score` ile bildirir.
        Böylece eşleştirme gibi kısmi puanlanan tipler de aynı döngüde çalışır.
        """
        total_correct = 0
        total_wrong = 0

        for related_name in QUESTION_RELATED_NAMES:
            for question in getattr(self, related_name).all():
                total_correct += question.correct_score
                total_wrong += question.wrong_score

        self.totalCorrect = total_correct
        self.totalWrong = total_wrong

        # Quiz bitirildi olarak işaretle ve kaydet
        self.isCompleted = True
        self.save()

    # Toplam geçen süreyi alan fonksiyon
    @property
    def total_time_taken(self):
        """Tüm soru tiplerinde harcanan sürenin toplamı (saniye)."""
        total = 0
        for related_name in QUESTION_RELATED_NAMES:
            agg = getattr(self, related_name).all().aggregate(Sum('time_taken'))
            total += agg['time_taken__sum'] or 0
        return total

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

    # Template'lerin hangi partial'ı include edeceğini bilmesi için.
    # Eskiden bu değer view içinde elle atanıyordu.
    @property
    def template_name(self):
        return self.__class__.__name__

    # Bu sorunun quiz toplamına kattığı doğru/yanlış sayısı.
    # Çoğu soru tipi için 1 veya 0; MatchingQuestion bunları override eder.
    @property
    def correct_score(self):
        return 1 if self.is_correct else 0

    @property
    def wrong_score(self):
        return 0 if self.is_correct else 1

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
        #Cevabı düzenle ve eğer ki doğru cevapla kullanıcınınki aynı ise doğru de
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
    #Soru metni ve doğru cevaplar
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

        #Geçen zaman none değilse geçen zamanı ata
        if time_taken is not None:
            self.time_taken = time_taken
        
        # Cevabı kaydet ve abstract class'taki kelimeleri güncelle
        self.save()
        self.update_word_stats()
    
#Eşleştirme sorularının modeli (Question abstract class'ını extend ediyor)
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

    # Eşleştirme kısmi puanlanır: 5 çiftin 3'ü doğruysa 3 doğru + 2 yanlış sayılır
    @property
    def correct_score(self):
        return self.correct_matches

    @property
    def wrong_score(self):
        return self.wrong_matches

    # quizComplete'teki inceleme tablosu için sol/kullanıcı/doğru üçlüsü.
    # Eskiden view içinde zip'leniyordu.
    @property
    def combined_items(self):
        left = self.left_column_items
        user_ordered = self.right_column_items_user_ordered
        correct = self.correct_column_items

        # Hiç cevaplanmamışsa (süre doldu vb.) inceleme boş kalmasın
        if not user_ordered:
            user_ordered = [{'id': None, 'text': '—'} for _ in left]

        return list(zip(left, user_ordered, correct))

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
        words = self.words.all().order_by(RawSQL(f'{table_name}.id', []))
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
            clauses.append(f'WHEN {table_name}.id=%s THEN %s')
            params.append(pk)
            params.append(i)
            
        ordering = 'CASE %s END' % ' '.join(clauses)
        words = self.words.all().order_by().order_by(RawSQL(ordering, params)) 
        
        return self._get_items_for_column(words, self.right_col_field)
    
    # Doğru cevapları sıralı bir şekilde dön
    @property
    def correct_column_items(self):
        table_name = self.words.model._meta.db_table
        words = self.words.all().order_by(RawSQL(f'{table_name}.id', []))
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

    #Cevapları kontrol et metodu
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


# Eş/Zıt anlamlı test sorularının modeli (QuizQuestion abstract class'ını extend ediyor)
class SynonymAntonymQuestion(QuizQuestion):
    """
    Bir kelimenin eş veya zıt anlamlısını soran çoktan seçmeli soru.
    Soru tipi (eş/zıt) question_text içinde belirtilir.
    Şık formatı MultipleChoiceQuestion ile aynıdır: "A:obtain_#_B:lose_#_C:run_#_D:eat"
    """

    question_text = models.CharField(max_length=400)
    options_data = models.TextField(max_length=500)
    correct_option = models.CharField(max_length=1)

    # "A:obtain_#_B:lose" → [('A', 'obtain'), ('B', 'lose')]
    @property
    def options_as_list(self):
        safe_delimiter = "_#_"
        try:
            return [tuple(pair.split(':', 1)) for pair in self.options_data.split(safe_delimiter)]
        except Exception as e:
            print(f"SynonymAntonymQuestion options_as_list HATA: {e}, Data: {self.options_data}")
            return []

    def check_answer(self, user_input, time_taken=None):
        self.user_answer = user_input.strip()
        self.is_correct = (self.user_answer == self.correct_option)

        if time_taken is not None:
            self.time_taken = time_taken

        self.save()
        self.update_word_stats()


# Boşluk doldurma sorularının modeli (QuizQuestion abstract class'ını extend ediyor)
class FillInTheBlankQuestion(QuizQuestion):
    """
    Kelimenin geçtiği bir örnek cümlede o kelime boşluğa çevrilir ve kullanıcıdan
    boşluğu doldurması istenir.

    Çoktan seçmeliden farkı: kullanıcı kelimeyi TANIMIYOR, ÜRETİYOR. Pasif
    kelime bilgisini aktif kullanıma taşıyan asıl soru tipi budur.

    Cümlede kelimenin çekimli hâli geçebildiği için (örn. "retain" ->
    "retained"), `correct_answer` maskelenen yüzey biçimi tutar;
    `accepted_answers` ise kabul edilecek diğer yazımları (kök hâl gibi)
    virgülle ayrılmış olarak tutar.
    """

    BLANK = "____"

    # Boşluğu içeren cümle: "The company managed to ____ most of its customers."
    sentence_with_blank = models.CharField(max_length=400)

    # Cümlede maskelenen yüzey biçim: "retain" ya da "retained"
    correct_answer = models.CharField(max_length=100)

    # Ek olarak kabul edilecek yazımlar (kök hâl, v2/v3 vb.), virgülle ayrılmış
    accepted_answers = models.CharField(max_length=300, blank=True, null=True)

    # Kullanıcıya ipucu olarak gösterilecek Türkçe anlam (opsiyonel)
    hint = models.CharField(max_length=200, blank=True, null=True)

    # Diğer soru tiplerinde question_text bir veritabanı alanı; burada sabit
    # olduğu için property olarak veriliyor. Böylece template'ler her soru
    # tipinde aynı şekilde {{ question.question_text }} kullanabiliyor.
    @property
    def question_text(self):
        return "Boşluğa uygun kelimeyi yazınız:"

    @property
    def accepted_answers_list(self):
        """Kabul edilen tüm cevapların küçük harfli, tekilleştirilmiş listesi."""
        candidates = [self.correct_answer]
        if self.accepted_answers:
            candidates += self.accepted_answers.split(',')

        seen = set()
        result = []
        for candidate in candidates:
            cleaned = (candidate or "").strip().lower()
            if cleaned and cleaned not in seen:
                seen.add(cleaned)
                result.append(cleaned)
        return result

    def check_answer(self, user_input, time_taken=None):
        """
        Cevabı kontrol eder.

        NOT: Burada WritingQuestion'daki gibi benzerlik toleransı UYGULANMAZ.
        Boşluğa tek bir kelime yazılıyor ve "retain" ile "retail" arasındaki
        benzerlik oranı, gerçek bir yazım hatasınınkiyle aynı seviyede çıkıyor.
        Yani tolerans, yazım hatasını affetmekten çok yanlış kelimeyi doğru
        saymaya yarardı. Bunun yerine kabul edilen biçimlerin listesi geniş
        tutuluyor (kök hâl + çekimli hâl).
        """
        self.user_answer = (user_input or "").strip()

        # Baştaki/sondaki noktalama işaretlerini yok say
        cleaned = self.user_answer.lower().strip(" .,!?;:'\"")

        self.is_correct = cleaned in self.accepted_answers_list if cleaned else False

        if time_taken is not None:
            self.time_taken = time_taken

        self.save()
        self.update_word_stats()
