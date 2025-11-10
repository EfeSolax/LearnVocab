from django.contrib import admin
from .models import Text

# Text modeli için özel bir ModelAdmin sınıfı tanımlıyoruz
@admin.register(Text)
class TextAdmin(admin.ModelAdmin):
    
    # --- Gelişmiş Görüntüleme Özellikleri (İsteğe bağlı ama önerilir) ---

    # 1. Liste Sayfası Görünümü (list_display)
    # Metinlerin listelendiği ana sayfada hangi sütunların görüneceği.
    list_display = ('owner', 'score', 'createdAt')

    # 2. Arama Alanları (search_fields)
    # Admin panelinde bir arama kutusu ekler. 
    # Kullanıcı adına veya metin içeriğine göre arama yapabilirsiniz.
    search_fields = ('owner__username', 'content')

    # 3. Filtreleme Alanları (list_filter)
    # Sağ tarafa bir filtreleme çubuğu ekler.
    list_filter = ('score', 'createdAt')

    # --- İsteğinizin Karşılanması ---

    # 4. Detay/Düzenleme Sayfası Görünümü (fieldsets)
    # "Tüm field'lar görünsün" isteğiniz için alanları gruplayarak 
    # düzenleme sayfasında net bir şekilde gösteriyoruz.
    fieldsets = (
        ('Genel Bilgiler', {
            'fields': ('owner', 'score', 'scores', 'createdAt')
        }),
        ('Metin İçeriği', {
            'fields': ('content', 'response')
        }),
        ('İlişkili Kelimeler', {
            'fields': ('words',)
        }),
    )

    # 5. ManyToMany Alanı için Gelişmiş Arayüz
    # 'words' alanını çok daha kullanışlı bir arayüze kavuşturur.
    filter_horizontal = ('words',)

    # 6. Salt Okunur Alanlar (readonly_fields)
    # 'createdAt' alanı auto_now_add=True olduğu için her zaman salt okunur olmalıdır.
    readonly_fields = ('createdAt',)

    # 7. TEMEL İSTEK: Yeni Ekleme İznini Kaldırma
    # Bu fonksiyon, admin panelinden "Yeni Text Ekle" butonunu ve 
    # yetkisini tamamen kaldırır.
    def has_add_permission(self, request):
        return False

    # 8. (İsteğe bağlı) Silme İznini de Kaldırma
    # Eğer bu kayıtların admin panelinden silinmesini de istemiyorsanız,
    # aşağıdaki fonksiyonu yorum satırından çıkarabilirsiniz.
    # def has_delete_permission(self, request, obj=None):
    #     return False