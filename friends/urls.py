# Django importları
from django.urls import path
from . import views

urlpatterns = [
    # Temel arkadaşlar sayfasının render url'i
    path('', views.listFriends, name='friends'),

    # İstek atma fonksiyonu 
    path("send-request/<int:user_id>", views.sendRequest, name = "send_request"),

    # İsteği kabul etme ve reddetme fonksiyonları (url'leri)
    path("accept-request/<int:user_id>", views.acceptRequest, name = "accept_request"),
    path("decline-request/<int:user_id>", views.declineRequest, name = "decline_request"),

    # Arkadaşı kaldırma fonksiyonu
    path("remove-friend/<int:user_id>", views.removeFriend, name = "remove_friend"),

    # İsteği geri çekme fonksiyonu
    path("cancel-request/<int:user_id>", views.cancelRequest, name = "cancel_request"),
]
