from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

    def ready(self):
        from . import sinyaller  # noqa: F401  (Google ile ilk girişte ayar satırı)
