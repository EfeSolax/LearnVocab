from django.contrib import admin

from .models import (
    Category, Collocation, ExampleSentence, Expression, ExpressionExample,
    FalseFriend, Meaning, UsagePattern, UserWordLink, Word, WordFamily, WordForm,
    WordRelation, BulunamayanArama, HazirListe, HazirListeKelimesi, HazirListeSecimi,
)


class MeaningInline(admin.TabularInline):
    model = Meaning
    extra = 1


class ExampleInline(admin.TabularInline):
    # Cümleler artık kelimeye değil ANLAMA bağlı: bank'ın iki anlamının
    # cümleleri birbirine karışmasın diye.
    model = ExampleSentence
    extra = 1


class CollocationInline(admin.TabularInline):
    model = Collocation
    extra = 1


class PatternInline(admin.TabularInline):
    model = UsagePattern
    extra = 1


class FalseFriendInline(admin.TabularInline):
    model = FalseFriend
    extra = 0


class ExpressionExampleInline(admin.TabularInline):
    model = ExpressionExample
    extra = 1


class FormInline(admin.TabularInline):
    model = WordForm
    extra = 0


class RelationInline(admin.TabularInline):
    model = WordRelation
    fk_name = "from_word"
    extra = 0
    autocomplete_fields = ("to_word",)
    raw_id_fields = ("meaning",)   # 20 bin anlamlık açılır liste olmasın


class WordInline(admin.TabularInline):
    model = Word
    extra = 0
    fields = ("text", "pos", "cefr")
    show_change_link = True


@admin.register(WordFamily)
class WordFamilyAdmin(admin.ModelAdmin):
    list_display = ("root", "member_count", "note")
    search_fields = ("root",)
    inlines = (WordInline,)

    @admin.display(description="kelime")
    def member_count(self, obj):
        return obj.words.count()


@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    list_display = ("text", "pos", "family", "meaning_preview", "cefr", "isBaseWord")
    list_filter = ("pos", "cefr", "isBaseWord", "visibility")
    search_fields = ("text", "meanings__meaning_tr")
    autocomplete_fields = ("family", "base_verb")
    inlines = (MeaningInline, FormInline, RelationInline, FalseFriendInline)

    @admin.display(description="anlamı")
    def meaning_preview(self, obj):
        return obj.meaningTr


@admin.register(WordRelation)
class WordRelationAdmin(admin.ModelAdmin):
    list_display = ("from_word", "type", "to_word", "meaning", "note")
    list_filter = ("type",)
    search_fields = ("from_word__text", "to_word__text")
    raw_id_fields = ("from_word", "to_word", "meaning")
    list_select_related = ("from_word", "to_word", "meaning__word")


@admin.register(WordForm)
class WordFormAdmin(admin.ModelAdmin):
    list_display = ("surface", "word", "kind")
    list_filter = ("kind",)
    search_fields = ("surface", "word__text")


@admin.register(Meaning)
class MeaningAdmin(admin.ModelAdmin):
    """Anlam artık kendi başına bir kayıt: cümleleri, collocation'ları,
    kalıpları ve alanları onun üzerinde duruyor."""

    list_display = ("word", "meaning_tr", "sentiment", "register")
    list_filter = ("sentiment", "register", "categories")
    search_fields = ("word__text", "meaning_tr", "definition")
    autocomplete_fields = ("word",)
    filter_horizontal = ("categories",)
    inlines = (ExampleInline, CollocationInline, PatternInline)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(Expression)
class ExpressionAdmin(admin.ModelAdmin):
    list_display = ("text", "meaning_tr", "kind", "cefr", "register")
    list_filter = ("kind", "cefr", "register", "sentiment")
    search_fields = ("text", "meaning_tr")
    filter_horizontal = ("categories", "words")
    inlines = (ExpressionExampleInline,)


@admin.register(FalseFriend)
class FalseFriendAdmin(admin.ModelAdmin):
    list_display = ("word", "turkish_lookalike", "assumed_meaning", "correct_english")
    search_fields = ("word__text", "turkish_lookalike")


admin.site.register(UserWordLink)


# --- Sözlük: hazır listeler ve bulunamayan aramalar (rapor 4.1, 4.2) ---

class HazirListeKelimesiInline(admin.TabularInline):
    model = HazirListeKelimesi
    extra = 0
    raw_id_fields = ("word",)
    ordering = ("sira", "id")


@admin.register(HazirListe)
class HazirListeAdmin(admin.ModelAdmin):
    list_display = ("ad", "kurum", "slug", "sira", "yayinda", "kelime_sayisi")
    list_editable = ("sira", "yayinda")
    prepopulated_fields = {"slug": ("ad",)}
    search_fields = ("ad", "kurum")
    inlines = (HazirListeKelimesiInline,)

    @admin.display(description="kelime")
    def kelime_sayisi(self, obj):
        return obj.uyelikler.count()


@admin.register(HazirListeSecimi)
class HazirListeSecimiAdmin(admin.ModelAdmin):
    list_display = ("user", "liste", "secildi")
    raw_id_fields = ("user",)


@admin.register(BulunamayanArama)
class BulunamayanAramaAdmin(admin.ModelAdmin):
    list_display = ("sorgu", "sayi", "kaynak", "oneri_vardi", "ilk", "son")
    list_filter = ("kaynak", "oneri_vardi")
    search_fields = ("sorgu",)
    ordering = ("-sayi", "-son")
