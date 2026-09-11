"""
Gemini API anahtarının erişebildiği modelleri listeler.

Model adları zamanla değişiyor ve eskiler kapatılıyor ("gemini-pro-latest",
"gemini-2.0-flash" gibi). Ayarlardaki GEMINI_MODEL geçersiz hâle geldiğinde
metin değerlendirme sessizce çalışmaz olur. Bu komut, hangi adların GERÇEKTEN
kullanılabilir olduğunu doğrudan API'den sorar:

    python manage.py list_gemini_models
"""

from django.conf import settings
from django.core.management.base import BaseCommand

from LearnVocab.gemini import get_client


class Command(BaseCommand):
    help = "Gemini API anahtarınızın erişebildiği modelleri listeler."

    def add_arguments(self, parser):
        parser.add_argument(
            "--all",
            action="store_true",
            help="Sadece metin üretenleri değil, tüm modelleri göster.",
        )

    def handle(self, *args, **options):
        client = get_client()
        if client is None:
            self.stderr.write(self.style.ERROR(
                "Gemini istemcisi oluşturulamadı. GEMINI_API_TOKEN tanımlı mı ve "
                "google-genai kurulu mu kontrol edin."
            ))
            return

        configured = getattr(settings, "GEMINI_MODEL", None)
        self.stdout.write(f"Ayarlardaki model (GEMINI_MODEL): {configured}\n")

        try:
            models = list(client.models.list())
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"Model listesi alınamadı: {exc}"))
            return

        show_all = options["all"]
        names = []
        for model in models:
            actions = getattr(model, "supported_actions", None) or []
            if show_all or "generateContent" in actions:
                names.append(model.name)

        if not names:
            self.stderr.write(self.style.WARNING("Kullanılabilir model bulunamadı."))
            return

        baslik = "Tüm modeller" if show_all else "Metin üretebilen modeller"
        self.stdout.write(f"\n{baslik} ({len(names)} adet):\n")

        # API "models/gemini-x" döner; ayarlarda her iki yazım da çalışır.
        configured_short = (configured or "").removeprefix("models/")

        for name in sorted(names):
            short = name.removeprefix("models/")
            if short == configured_short:
                self.stdout.write(self.style.SUCCESS(f"  * {short}   <-- şu an kullanılan"))
            else:
                self.stdout.write(f"    {short}")

        if configured_short and configured_short not in {n.removeprefix("models/") for n in names}:
            self.stdout.write("")
            self.stderr.write(self.style.ERROR(
                f"DİKKAT: Ayarlardaki '{configured_short}' bu listede yok. "
                ".env dosyanızdaki GEMINI_MODEL değerini yukarıdakilerden biriyle değiştirin."
            ))
