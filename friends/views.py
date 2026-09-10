# Django importları
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q

# Gerekli model importları
from users.models import User

# Kullanıcıların görüntülendiği sayfa
def listFriends(request):
    # Kullanıcı giriş yapmamışsa tüm kullanıcıları al ve bunu friends.html'e gönder
    if not request.user.is_authenticated:
        users = User.objects.all()
        return render(request, "pages/friends.html", {"userAll":users})

    # Kullanıcı giriş yapmışsa
    else:
        # Kullanıcıyı al
        current_user = request.user

        # TÜM KULLANICILARIN GÖRÜNTÜLENMESİNİ SAĞLAYAN KODLAR

        # Tüm kullanıcı sayfasının sorgusunu al
        queryForAll = request.GET.get('queryForAll')

        # Kullanıcının arkadaşlarını, kullanıcıya istek atanları, kullanıcının istek attıklarını al
        friends_list_all_tab = current_user.friends.all()
        sent_to_me_list = current_user.incomingRequests.all()
        sent_by_me_list = User.objects.filter(incomingRequests=current_user)

        # Bu kullanıcıların id'lerini al
        friends_ids = friends_list_all_tab.values_list('id', flat=True)
        sent_to_me_ids = sent_to_me_list.values_list('id', flat=True)
        sent_by_me_ids = sent_by_me_list.values_list('id', flat=True)

        # Bu id sınıflarından birine girmeyen kullanıcıları al (ilişkisi olmayan kullanıcılar)
        no_relation_list = User.objects.exclude(id=current_user.id)\
                                   .exclude(id__in=friends_ids)\
                                   .exclude(id__in=sent_to_me_ids)\
                                   .exclude(id__in=sent_by_me_ids)
        
        # Gönderilen query boş değilse bütün kullanıcı sınıflarını query'e göre filtrele
        if not (queryForAll == "" or queryForAll == None):
            friends_list_all_tab = friends_list_all_tab.filter(
                Q(username__icontains=queryForAll) |  
                Q(first_name__icontains=queryForAll) | 
                Q(last_name__icontains=queryForAll)
            ).distinct()

            sent_to_me_list = sent_to_me_list.filter(
                Q(username__icontains=queryForAll) |  
                Q(first_name__icontains=queryForAll) | 
                Q(last_name__icontains=queryForAll)
            ).distinct()

            sent_by_me_ids = sent_by_me_ids.filter(
                Q(username__icontains=queryForAll) |  
                Q(first_name__icontains=queryForAll) | 
                Q(last_name__icontains=queryForAll)
            ).distinct()

            no_relation_list = no_relation_list.filter(
                Q(username__icontains=queryForAll) |  
                Q(first_name__icontains=queryForAll) | 
                Q(last_name__icontains=queryForAll)
            ).distinct()

        # KULLANICIYA GELEN İSTEKLERİN GÖRÜNTÜLENMESİNİ SAĞLAYAN KODLAR

        # Kullanıcıya gelen istekler için query'yi al
        queryForRequests = request.GET.get("queryForRequests")

        # Kullanıcıya gelen tüm istekleri al
        requests = current_user.incomingRequests.all()

        # Query boş değilse istekleri filtrele
        if not (queryForRequests == "" or queryForRequests == None):
            requests = requests.filter(
                Q(username__icontains=queryForRequests) |  
                Q(first_name__icontains=queryForRequests) | 
                Q(last_name__icontains=queryForRequests)
            ).distinct()
        
        # ARKADAŞLARIN GÖRÜNTÜLENMESİNİ SAĞLAYAN SAYFANIN KODLARI

        # Kullanıcının arkadaşları için query'yi al
        queryForFriends = request.GET.get("queryForFriends")

        # Kullanıcının tüm arkadaşlarını al
        friends = current_user.friends.all()

        # Query boş değilse arkadaşları filtrele
        if not (queryForFriends == "" or queryForFriends == None):
            friends = current_user.friends.filter(
                Q(username__icontains=queryForFriends) |  
                Q(first_name__icontains=queryForFriends) | 
                Q(last_name__icontains=queryForFriends)
            ).distinct()

        # -------------------------------------------------------------

        # Sayfaya tüm bu listeleri gönder
        context = {
            "friends":friends,
            "requests":requests,
            "friends_list_all_tab":friends_list_all_tab,
            "sent_to_me_list":sent_to_me_list,
            "sent_by_me_list":sent_by_me_list,
            "no_relation_list":no_relation_list,
        }

        return render(request, "pages/friends.html", context)

# Arkadaşı kaldır fonksiyonu (login gerekiyor)
@login_required
def removeFriend(request, user_id):
    if user_id == request.user.id:
        messages.error(request, "Kendinizi arkadaş olarak kaldıramazsınız.")
        return redirect("friends")

    friend = get_object_or_404(User, id=user_id)

    if not request.user.friends.filter(id=friend.id).exists():
        messages.error(request, "Bu kullanıcı zaten arkadaş listenizde değil.")
        return redirect("friends")

    # friends symmetrical=True olduğu için tek tarafta remove yeterli
    request.user.friends.remove(friend)

    messages.success(request, f"{friend.username} başarılı bir şekilde arkadaş listenizden kaldırıldı.")
    return redirect("friends")


# İstek kabul etme fonksiyonu (login gerekiyor)
@login_required
def acceptRequest(request, user_id):
    if user_id == request.user.id:
        messages.error(request, "Geçersiz istek.")
        return redirect("friends")

    user = get_object_or_404(User, id=user_id)

    if not request.user.incomingRequests.filter(id=user.id).exists():
        messages.error(request, "Bu kullanıcının size gönderilmiş bir arkadaşlık isteği yok.")
        return redirect("friends")

    request.user.incomingRequests.remove(user)
    # friends symmetrical=True olduğu için tek tarafta add yeterli
    request.user.friends.add(user)

    messages.success(request, f"{user.username} artık sizin arkadaşınız!")
    return redirect("friends")


# İstek reddetme fonksiyonu (login gerekiyor)
@login_required
def declineRequest(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if not request.user.incomingRequests.filter(id=user.id).exists():
        messages.error(request, "Bu kullanıcıdan bir arkadaşlık isteğiniz yok.")
        return redirect("friends")

    request.user.incomingRequests.remove(user)
    messages.success(request, f"{user.username} kullanıcısının arkadaşlık isteğini reddettiniz.")
    return redirect("friends")


# İsteği geri çekme fonksiyonu (login gerekiyor)
@login_required
def cancelRequest(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if not user.incomingRequests.filter(id=request.user.id).exists():
        messages.error(request, "Bu kullanıcıya gönderilmiş bekleyen bir isteğiniz yok.")
        return redirect("friends")

    user.incomingRequests.remove(request.user)
    messages.success(request, f"{user.username} kullanıcısına göndermiş olduğunuz arkadaşlık isteğini geri çektiniz.")
    return redirect("friends")


# İstek gönderme fonksiyonu (login gerekiyor)
@login_required
def sendRequest(request, user_id):
    if user_id == request.user.id:
        messages.error(request, "Kendinize arkadaşlık isteği gönderemezsiniz.")
        return redirect("friends")

    user = get_object_or_404(User, id=user_id)

    if request.user.friends.filter(id=user.id).exists():
        messages.error(request, "Bu kullanıcı zaten arkadaş listenizde.")
        return redirect("friends")

    if user.incomingRequests.filter(id=request.user.id).exists():
        messages.info(request, "Bu kullanıcıya zaten bir istek göndermişsiniz.")
        return redirect("friends")

    # Karşı taraf bize istek atmışsa otomatik kabul olarak ele al
    if request.user.incomingRequests.filter(id=user.id).exists():
        request.user.incomingRequests.remove(user)
        request.user.friends.add(user)
        messages.success(request, f"{user.username} kullanıcısı zaten size istek atmıştı, artık arkadaşsınız!")
        return redirect("friends")

    user.incomingRequests.add(request.user)
    messages.success(request, f"{user.username} kullanıcısına bir arkadaşlık isteği gönderdiniz.")
    return redirect("friends")
