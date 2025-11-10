from django.contrib import admin
# Django'nun varsayılan UserAdmin sayfasının import ediyoruz.
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
# Kendi özel User modelimizi import ediyoruz
from .models import User

# =======================================================================
# 1. ADIM: Diğer uygulamanın (usersettings) admininden Inline'ı import et
# =======================================================================
try:
    # 'usersettings' uygulamanızın adının bu olduğunu varsayıyorum
    from usersettings.admin import UserSettingsInline
except ImportError:
    # usersettings uygulaması yoksa veya hata verirse
    UserSettingsInline = None


class UserAdmin(BaseUserAdmin):
    # Varsayılan UserAdmin sayfasında görünmesini istediğimiz özellikler
    list_display = ('username', 'email', 'first_name', 'last_name', 'level')

    # UserAdmin sayfasında hangi özellikler görünecek. Detayları göster:
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Kişisel Bilgiler', {'fields': ('first_name', 'last_name', 'email', 'level')}),
        ('Arkadaşlıklar', {'fields': ('friends', 'incomingRequests')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    # ManyToMany alanlarını arayüzde daha kolay seçmek için bu komut yazılıyor.
    filter_horizontal = ('friends', 'incomingRequests', 'groups', 'user_permissions',)
    
    # =======================================================================
    # 2. ADIM: Import ettiğimiz Inline'ı buraya ekliyoruz
    # =======================================================================
    # 'inlines' bir tuple (demet) olmalıdır, bu yüzden sonunda virgül var
    inlines = (UserSettingsInline,) if UserSettingsInline else ()


# Admin panelin'de kullanıcı modeli ile oluşturulmuş objeleri göster.
# Not: Özel kullanıcı modelinde, Django zaten eski UserAdmin'i 
# kayıttan kaldırmamızı bekler, bu yüzden güvenli bir kontrol ekleyelim:
if admin.site.is_registered(User):
    admin.site.unregister(User)

admin.site.register(User, UserAdmin)