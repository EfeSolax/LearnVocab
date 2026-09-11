"""
Passenger WSGI giriş noktası.

Eski sürüm `imp` modülünü kullanıyordu; bu modül Python 3.12'de tamamen
kaldırıldı. Standart Django WSGI import'u her sürümle uyumludur.
"""
import os
import sys

# Proje kökünü Python path'ine ekle
sys.path.insert(0, os.path.dirname(__file__))

# Django settings modülünü ayarla (manage.py'de zaten ayarlı ama
# Passenger üzerinden çalışırken garanti altına alıyoruz)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'LearnVocab.settings')

from LearnVocab.wsgi import application  # noqa: E402
