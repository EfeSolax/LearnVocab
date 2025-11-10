"""
URL configuration for LearnVocab project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

"""
Merhaba ben django ile bir web sitesi geliştirmek istiyorum. Bu sene üniversiteyi kazandım fakat şu anda hazırlık okuyorum ve ingilizce öğrenmeye çalışıyorum. Fakat ingilizce'de kelime öğrenme işi beni zorluyor. Bu sorunu çözmek içinse bir web sitesi geliştirmek istiyorum. Fakat tabii ki kendine müslüman biri olmadığım için bunu olabildiğince insanların efektif bir şekilde kullanabileceği ve sevebileceği bir şekilde tasarlamak istiyorum. Daha önceden django ile bir web sitesi geliştirme tecrübem oldu fakat o web sitesiyle ilgili yakındığım en büyük durum web sitesine sadece tablet veya bilgisayar gibi yanlamasına görünen bir yerden giriş yapılabilmesiydi. Fakat şimdi tasarlayacağım sitenin telefondan da kullanılabilmesi için dik bir şekilde de yan bir şekilde de görünse görünümünün düzgün olmasını ve kaymamasını istiyorum. Bunun için ve tabii ki sitenin gerek frontend gerekse backend kısmında bana yardımcı olur musun?

Şimdi ilk başta projenin bir taslağını oluşturmak isterim. Elimde bir sürü kelimenin, ingilizce bir şekilde açıklamalarının ve örnek hazır cümlelerin olduğu bir veri seti var. Bunları da siteye yüklemek ve insanların kullanımına açmak isterim fakat benim yapmak istediğim şey aslında kullanıcılara kendi kelimelerini (ingilizce hali, fiilse V2 ve V3 hallerini, türkçe farklı anlamlarını, tercihe bağlı olarak ingilizce açıklamalarını, kendi kurdukları örnek cümleleri, ekledikleri kelimenin diğer insanlar tarafından veya kimler tarafından görülebileceğini) eklemelerini isterim. Ve bunu yaparken de dediğin gibi django'nun halihazırda olan veritabanı alt yapısını kullanmak isterim. Kafamda temel olarak var olan şeyler:

1. Kişinin Profili: Kişi bu sayfada kendi kelime listesini ve quiz sonuçlarını, kelime öğrenme başarısını ve örnek oluşturduğu metinleri görebilecek. Arkadaş olarak seçtiği kullanıcılarını yönetebilecek. Ve tabii ki kelimeleri bu sayfa üzerinden bir linke tıklayarak ekleyecek. Ki zaten eklenen kelimeleri de "Herkese Açık", "Arkadaşlarıma Açık" veya "Gizli" olarak seçebilmesini istiyorum. 

2. Kelime Ekleme Sayfası: Kelime ekleme sayfasında bir kullanıcı ingilizce kelimenin kendisini, eğer bir fiilse V2 ve V3 hallerini, türkçe anlamını, isteğe bağlı olarak ingilizce açıklamasını, ve son olarak kendi kurduğu ingilizce örnek cümleleri ekleyebilecek ve daha sonra bu kelimenin kimlere açık olduğunu seçebilecek. 

3. Quiz ve Text sayfası: Burada kullanıcıya kendi girdiği veya "kelime listeme ekle" diye seçtiği (bu eklenen kelimeler başkasının kelimeleri veya sayfaya halihazırda yüklenen kelimeler olabilir) kelimelerden küçük bir quiz sistemi eklemek istiyorum. Bu sayfada kullanıcı sadece kelime anlam eşleştirmesi yapmaktan ziyade daha geniş kapsamlı bir test hazırlamak istiyorum. Daha tam bir fikir yok aklımda fakat senin varsa söyleyebilirsin mesela işte fiilse v2 ve v3. halinin çekimi falan olabilir. Bir de kullanıcının text'leri olacak. Aslında bu zorunlu olmayan fakat o hafta boyunca listesine eklediği kelimelerin olabildiğince çoğunu içeren bir metin yazmaya çalışacak. Fakat bu metnin değerlendirmesi nasıl yapılır, hiçbir fikrim yok, bunun için bir yapay zeka kullanmak güzel olabilir fakat yapay zeka ile ilgili hiçbir fikrim yok, eğer yapabileceğimizi düşünürsen ya da internette bununla ilgili yapılmış hazır kütüphaneler varsa bahsedebilirsin. 

4. Arkadaşlarım sayfası: Buradan kullanıcı arkadaş olmak istediği kişilere istek atabilecek veya onların profillerine (eğer arkadaşlık izni onaylanmışsa) tıklayarak gidebilecek. Ve tabii ki kendisine gelen istekleri cevaplayabilecek. 

5. Genel kelimeler listesi: Burada zaten elimde olan veri setindeki kelimeleri buraya eklemeyi düşünüyorum ve insanların public'e açtığı kelimeleri burada yayınlamayı düşünüyorum. Tabi ki bir kelime daha sonradan da public'e açılabilir bu yüzden kelimelerim sayfasında (bkz:2.başlık) kelimeleri düzenle menüsü üzerinden bu ayarı değiştirebilmeyi isterim. Ve tabii ki kullanıcı beğendiği kelimeleri "add my wordlist" diyerek kendi listesine ekleyebilmeli. 

6. Hakkımda sayfası: Tabii ki burada kullanıcılara kendimi ve siteyi, sitenin kullanımını gibi şeyleri anlatacak bir sayfa eklemek isterim. 

7. Genel Sayfa: Bu genel sayfada sitenin amacından ve işleyişinden bahsedebiliriz ve siteye insanların yorum ve eleştiri eklemesini sağlayabiliriz. Böylece alınan geri dönüşlerle siteyi geliştirebiliriz. 

8. Yorumlar Sayfası: Burada kullanıcılardan gelen site için yapılmış bir yorumlar sayfası yapabiliriz. Aynı zamanda yorumlara yorum atma veya like, dislike atma gibi yollar üzerinden geri dönüt alabiliriz. 

9. Ve tabii ki giriş yap, kayıt ol seçenekleri, burayı anlatmama gerek yok zaten biliyorsun.

Projemi LearnVocab kurdum ve startapp olarak başlattığım uygulamalar: users, words, quizzer, progress, frontend, texts şeklinde. Ve templates klasörünün altında base ve pages klasörlerinin altında sayfa tasarımlarını ayarlıyorum. Şu ana kadar navbar.html ve layout.html'i base'in altına tanımladım. 
Pages'in altında da mevcut olarak
index.html'i 
register.html'i
login.html'i
about.html'i
allWords.html'i
wordDetail.html'i
hazırladım.

Kelimelerin modelini ve users'ın modelini, views'ını, admin sayfasını hazırladım. 



"""

from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from friends import views

# Diğer app'lerin altındaki urls.py 'leri dahil edebilmesi için include'u dahil ediyoruz.
from django.urls import include

# Bunlar profile_pics kısmını görüntülemek için gerekli import'lar
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import messages

def showIndex(request):
    return render(request, "pages/index.html")

def showAbout(request):
    return render(request, "pages/about.html")


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', showIndex, name='index'),
    path('users/', include('users.urls')),
    path("about/", showAbout, name = "about"),
    path("words/", include('words.urls')),
    path("friends/", include('friends.urls')),
    path("profile/",include('userprofile.urls')),
    path("quizzes/",include('quizzes.urls')),
    path("comments/",include('comments.urls')),
    path("texts/",include('texts.urls')),
    path("settings/",include('usersettings.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


