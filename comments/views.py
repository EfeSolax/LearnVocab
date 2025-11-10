# Django importları
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Exists, OuterRef, Value, BooleanField

# Gerekli model importları
from comments.models import Comment

# Yorumları gösterme sayfası
def showComments(request):
    # Eğer kullanıcı giriş yapmışsa ve yorum eklemişse
    if request.method == "POST" and request.user.is_authenticated:
        # Yeni yorumun içeriğini al
        newCommentContent = request.POST.get("comment_content")

        # Yeni yorumu oluştur ve kaydet, başarı mesajı yayınla
        newComment = Comment.objects.create(
            owner = request.user,
            content = newCommentContent,
        )
        newComment.save()
        messages.success(request, "Yorumunuz başarılı bir şekilde kaydedildi.")

        # Tekrar yorumları göster sayfasına dön
        return redirect("show_comments_page")

    else:
        # GET için tüm yorumları al
        allComments = Comment.objects.all()

        # Arama kriterini ve arama içeriğini al
        searchType = request.GET.get("search_by")
        q = request.GET.get("search_query")

        # Arama içeriğine göre ve query'e göre filtreleme yap
        if searchType == "author":
            allComments = allComments.filter(owner__username__icontains=q)
        elif searchType == "content":
            allComments = allComments.filter(content__icontains=q)

        # Eğer kullanıcı giriş yapmışsa, kullanıcının yorumlara like atıp atmadığının
        # bilgisini al
        if request.user.is_authenticated:
            user_likes = Comment.objects.filter(pk=OuterRef('pk'), liked_by=request.user)
            user_dislikes = Comment.objects.filter(pk=OuterRef('pk'), disliked_by=request.user)
            
            allComments = allComments.annotate(
                is_liked_by_user=Exists(user_likes),
                is_disliked_by_user=Exists(user_dislikes)
            )
        else:
            # Kullanıcı giriş yapmamışsa hiçbiri işaretli olmasın
            allComments = allComments.annotate(
                is_liked_by_user=Value(False, output_field=BooleanField()),
                is_disliked_by_user=Value(False, output_field=BooleanField())
            )

        # Yorumların tamamını al ve comments.html'e yolla
        context = {
            "comments":allComments,
        }
    
        return render(request, "pages/comments.html", context)
    
# Yorum silme sayfası (giriş yapmış olmak gerekiyor)
@login_required
def removeComment(request, id):
    # Verilen id'ye göre yorumu al
    comment = Comment.objects.filter(id = id).first()

    # Bu id'ye sahip yorumun sahibi ile kullanıcı aynı kişiyse yorumu sil ve başarı mesajı yayınla
    if request.user.username == comment.owner.username:
        comment.delete()
        messages.success(request, "Yorumunuz başarılı bir şekilde silindi.")

    # Kullanıcı yorumun sahibi değilse hata mesajı yayınla
    else:
        messages.error(request, "Bu sizin yorumunuz değil, bu yorumu silemezsiniz.")

    # Tekrar yorumlar sayfasına yönlendir
    return redirect("show_comments_page")

# Yoruma like atma fonksiyonu
def likeComment(request, id):
    # Eğer kullanıcı giriş yapmışsa 
    if request.user.is_authenticated:
        # ID'si verilen yorumu al
        comment = Comment.objects.filter(id = id).first()

        # Eğer yorumun like atanlar field'ında kullanıcı varsa like'ı kaldır, başarı mesajı yayınla
        if comment.liked_by.filter(pk = request.user.pk).exists():
            messages.success(request, "Bu yoruma attığınız like kaldırıldı.")
            comment.liked_by.remove(request.user)

        # Eğer yoruma like atanlarda yoksa
        else:
            # Ve yoruma dislike atanlar field'ındaysa kullanıcıyı oradan kaldır
            if comment.disliked_by.filter(pk = request.user.pk).exists():
                comment.disliked_by.remove(request.user)
            
            # Yoruma like atanlar field'ına kullanıcıyı ekle ve başarı mesajı yayınla
            comment.liked_by.add(request.user)
            messages.success(request, "Bu yoruma like attınız.")
            
        # Tekrar yorumlar sayfasına dön
        return redirect("show_comments_page")
    
    # Eğer kullanıcı giriş yapmamışsa hata mesajı yayınla ve yorumlar sayfasına geri dön
    else:
        messages.error(request, "Yoruma like atmak için giriş yapmış olmanız gerekmektedir.")
        return redirect("show_comments_page")
    
# Yoruma dislike atma fonksiyonu
def dislikeComment(request, id):
    # Eğer kullanıcı giriş yapmışsa 
    if request.user.is_authenticated:
        # ID'si verilen yorumu al
        comment = Comment.objects.filter(id = id).first()

        # Eğer kullanıcı yoruma dislike atmışsa dislike'ı kaldır ve başarı mesajı yayınla
        if comment.disliked_by.filter(pk = request.user.pk).exists():
            comment.disliked_by.remove(request.user)
            messages.success(request, "Bu yorumdan attığınız dislike kaldırıldı.")
        
        # Eğer kullanıcı yoruma dislike atmamışsa
        else:
            # Eğer kullanıcı yoruma like atmışsa kaldır
            if comment.liked_by.filter(pk = request.user.pk).exists():
                comment.liked_by.remove(request.user)

            # Yoruma dislike at ve başarı mesajı yayınla
            comment.disliked_by.add(request.user)
            messages.success(request, "Bu yoruma dislike attınız.")

        # Yorumlar sayfasına geri dön
        return redirect("show_comments_page")
    
    # Eğer giriş yapılmamışsa hata mesajı yayınla ve yorumlar sayfasına dön
    else:
        messages.error(request, "Yoruma dislike atmak için giriş yapmış olmanız gerekmektedir.")
        return redirect("show_comments_page")
    
