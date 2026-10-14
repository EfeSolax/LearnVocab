"""manage.py elle_kelime_yukle (rapor 18.16: eksik Oxford kelimeleri, elle)."""

import json
import tempfile
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from words.models import Word, WordForm
from words.testing import make_word


class ElleKelimeTests(TestCase):
    def _dosya(self, *kayitlar):
        f = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8")
        f.write("\n".join(json.dumps(k, ensure_ascii=False) for k in kayitlar))
        f.close()
        return f.name

    def test_ekler_atlar_ve_bicim_yazar(self):
        make_word("good", pos="adjective", level="A1")
        yol = self._dosya(
            {"text": "banana", "pos": "noun", "cefr": "A1",
             "anlamlar": [{"tr": "muz", "en": "a yellow fruit", "ornekler": ["I like bananas.", "A banana, please."]}]},
            {"text": "best", "pos": "adjective", "cefr": "A1", "aile": "good",
             "anlamlar": [{"tr": "en iyi", "en": "superlative of good", "ornekler": ["She is my best friend."]}]},
            {"text": "be", "pos": "verb", "cefr": "A1", "v2": "was/were", "v3": "been",
             "bicimler": [["am", "other"], ["is", "third_person"], ["was", "past"], ["was", "past"]],
             "anlamlar": [{"tr": "olmak", "en": "to exist", "ornekler": ["I am here."]}]},
            {"text": "good", "pos": "adjective", "cefr": "A1",
             "anlamlar": [{"tr": "iyi", "en": "x", "ornekler": ["x"]}]},
        )
        cikti = StringIO()
        call_command("elle_kelime_yukle", yol, stdout=cikti)
        self.assertIn("3 eklendi, 1 zaten vardı", cikti.getvalue())
        muz = Word.objects.get(text="banana")
        self.assertEqual((muz.cefr_kaynak, muz.isBaseWord, muz.visibility, muz.slug), ("oxford", True, "public", "banana"))
        self.assertEqual(muz.meanings.first().examples.count(), 2)
        self.assertEqual(Word.objects.get(text="best").family, Word.objects.get(text="good").family)
        self.assertEqual(set(WordForm.objects.filter(word__text="be").values_list("surface", flat=True)),
                         {"am", "is", "was"})

    def test_eksik_alan_hata(self):
        yol = self._dosya({"text": "x", "pos": "noun", "cefr": "A1", "anlamlar": [{"tr": "x"}]})
        with self.assertRaises(CommandError):
            call_command("elle_kelime_yukle", yol, stdout=StringIO())

    def test_phrasal_verb_fiile_baglanir_cekim_ve_benzer(self):
        give = make_word("give", pos="verb", level="A1")
        quit = make_word("quit", pos="verb", level="B1")
        yol = self._dosya(
            {"text": "give up", "pos": "phrasal_verb", "cefr": "B1", "cefr_kaynak": "learnvocab",
             "anlamlar": [{"tr": "vazgeçmek", "en": "to stop trying", "ornekler": ["Don't give up."],
                           "benzer": ["quit", "olmayan"]}]},
        )
        cikti = StringIO()
        call_command("elle_kelime_yukle", yol, stdout=cikti)
        self.assertIn("give up = olmayan", cikti.getvalue())
        w = Word.objects.get(text="give up")
        self.assertEqual((w.cefr_kaynak, w.base_verb, w.family), ("learnvocab", give, give.family))
        self.assertEqual((w.v2Form, w.v3Form), ("gave up", "given up"))
        self.assertTrue(WordForm.objects.filter(word=w, surface="gave up").exists())
        m = w.meanings.get()
        self.assertEqual(list(m.relations.values_list("to_word", "type")), [(quit.pk, "synonym")])

    def test_bilinmeyen_seviye_kaynagi_hata(self):
        yol = self._dosya({"text": "x", "pos": "noun", "cefr": "A1", "cefr_kaynak": "uydurma",
                           "anlamlar": [{"tr": "x", "en": "x", "ornekler": ["x"]}]})
        with self.assertRaises(CommandError):
            call_command("elle_kelime_yukle", yol, stdout=StringIO())
