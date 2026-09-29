from django.urls import path
from . import views

urlpatterns = [
    path("profile/", views.showProfile, name="user_profile"),
    # Arkadaşlık özelliği (kapalı) için kullanıcı profili görüntüleme
    path("profile/show-user-profile/<int:user_id>", views.showUserProfile, name="show_user_profile"),
]
