from django.apps import AppConfig


class WordsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'words'

    def ready(self):
        # Arama dizininin sinyalleri: kelime/anlam değişince dizin yenilenir.
        from . import arama  # noqa: F401
