from ..models import Word, UserWordLink

# bu metot 1,2,3,4,5 şeklinde kur seviyesi alır. Ve 1,2,3,4 şeklinde span 
# alır ve bu duruma uyan kelimeleri verilen kullanıcının listesine ekler veya
# kullanıcının listesinden siler.

def wordsAddDelete(user, delete, level, span):
    span = int(span)
    wordLevel = level + "01"
    words = Word.objects.filter(wordLevel=wordLevel, span=span, isBaseWord=True)

    for word in words:
        if delete:
            UserWordLink.objects.filter(user=user, word=word).delete()
        else:
            if not UserWordLink.objects.filter(user=user, word=word).exists():
                UserWordLink.objects.create(user=user, word=word)

def allWordsAddDelete(user, delete, level):
    
    wordLevel = level + "01"
    
    words = Word.objects.filter(wordLevel = wordLevel, isBaseWord = True).order_by('id')

    for word in words:
        if delete:
            UserWordLink.objects.filter(user = user, word = word).delete()
        else:
            if not UserWordLink.objects.filter(user = user, word = word).exists():
                UserWordLink.objects.create(user = user, word = word)

