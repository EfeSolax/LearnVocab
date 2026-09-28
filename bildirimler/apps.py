from django.apps import AppConfig


class BildirimlerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "bildirimler"
    verbose_name = "Bildirimler"

    def ready(self):
        # "Yazın değerlendirildi" bildirimi: texts.sinyaller'e bağlanıyoruz.
        from . import alicilar  # noqa: F401
