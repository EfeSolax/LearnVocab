"""
Test çalıştırıcısı: her istek bitince dil varsayılana döner.

Django dili iş parçacığında etkin bırakır. Bir test /en/ sayfasını açınca sonraki testin
reverse("…") çağrısı /en/… adresi üretir ve sayfa İngilizce gelir (paralel çalışmada arada bir
düşen words.test_gunun testlerinin sebebi buydu). Canlıda sorun yok: her istekte LocaleMiddleware
dili adresten yeniden seçer. Paralel çalışmada sinyal her işçi süreçte de bağlanır (macOS'ta
işçiler sıfırdan başlar, ana süreçteki bağlantı geçmez).
"""
from django.core.signals import request_finished
from django.test.runner import DiscoverRunner, ParallelTestSuite, _init_worker
from django.utils import translation


def _dili_sifirla(**_):
    translation.deactivate()


def _baglan():
    request_finished.connect(_dili_sifirla, dispatch_uid="testte-dili-sifirla")


def _isci_baslat(*args, **kwargs):
    _init_worker(*args, **kwargs)
    _baglan()


class _DilSifirlayanParalel(ParallelTestSuite):
    init_worker = _isci_baslat


class DilSifirlayanRunner(DiscoverRunner):
    parallel_test_suite = _DilSifirlayanParalel

    def setup_test_environment(self, **kwargs):
        super().setup_test_environment(**kwargs)
        _baglan()
