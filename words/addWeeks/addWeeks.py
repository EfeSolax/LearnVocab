from ..models import Word, UserWordLink

def add401Weeks(user, week_no, delete = False):

    starterWord = None
    finisherWord = None

    if week_no == 1:
        starterWord = "alter"
        finisherWord = "remain"
    elif week_no == 2:
        starterWord = "remain"
        finisherWord = "boast"
    elif week_no == 3:
        starterWord = "boast"
        finisherWord = "exploit"
    elif week_no == 4:
        starterWord = "exploit"
        finisherWord = "disorder"
    elif week_no == 5:
        starterWord = "disorder"
        finisherWord = "generate"
    elif week_no == 6:
        starterWord = "generate"
        finisherWord = "prevention"
    elif week_no == 7:
        starterWord = "prevention"
        finisherWord = "look like"

    
    if starterWord == None or finisherWord == None:
        return "ERROR" 


    words = Word.objects.filter(wordLevel = "401")

    start = False
    for word in words:
        if word.englishWord == finisherWord:
            if word.englishWord == "look like":
                if delete:
                    UserWordLink.objects.filter(user = user, word = word).delete()
                else:
                    UserWordLink.objects.create(user = user, word = word)

            break
        if word.englishWord == starterWord:
            start = True
        
        if start:
            if delete:
                UserWordLink.objects.filter(user = user, word = word).delete()
            else:
                UserWordLink.objects.create(user = user, word = word)

def add201Weeks(user, week_no, delete = False):
    starterWord = None
    finisherWord = None

    if week_no == 1:
        starterWord = "work for a company"
        finisherWord = "teach"
    elif week_no == 2:
        starterWord = "teach"
        finisherWord = "attend"
    elif week_no == 3:
        starterWord = "attend"
        finisherWord = "make a film"
    elif week_no == 4:
        starterWord = "make a film"
        finisherWord = "freedom"
    elif week_no == 5:
        starterWord = "freedom"
        finisherWord = "take off"
    elif week_no == 6:
        starterWord = "take off"
        finisherWord = "increase"
    elif week_no == 7:
        starterWord = "increase"
        finisherWord = "go through"
    elif week_no == 8:
        starterWord = "go through"
        finisherWord = "talent"

    if starterWord == None or finisherWord == None:
        return "ERROR" 


    words = Word.objects.filter(wordLevel = "201")

    start = False
    for word in words:
        if word.englishWord == finisherWord:
            if word.englishWord == "talent":
                if delete:
                    UserWordLink.objects.filter(user = user, word = word).delete()
                else:
                    UserWordLink.objects.create(user = user, word = word)
            break
        if word.englishWord == starterWord:
            start = True
        
        if start:
            if delete:
                UserWordLink.objects.filter(user = user, word = word).delete()
            else:
                UserWordLink.objects.create(user = user, word = word)

def add501Weeks(user, week_no):
    starterWord = None
    finisherWord = None

    if week_no == 1:
        starterWord = "absent-minded"
        finisherWord = "backpedal"
    elif week_no == 2:
        starterWord = "backpedal"
        finisherWord = "attend"
    elif week_no == 3:
        starterWord = "attend"
        finisherWord = "make a film"
    elif week_no == 4:
        starterWord = "make a film"
        finisherWord = "freedom"
    elif week_no == 5:
        starterWord = "freedom"
        finisherWord = "take off"
    elif week_no == 6:
        starterWord = "take off"
        finisherWord = "increase"
    elif week_no == 7:
        starterWord = "increase"
        finisherWord = "go through"
    elif week_no == 8:
        starterWord = "go through"
        finisherWord = "talent"

    if starterWord == None or finisherWord == None:
        return "ERROR" 


    words = Word.objects.filter(wordLevel = "201")

    start = False
    for word in words:
        if word.englishWord == finisherWord:
            if word.englishWord == "talent":
                UserWordLink.objects.create(user = user, word = word)
            break
        if word.englishWord == starterWord:
            start = True
        
        if start:
            UserWordLink.objects.create(user = user, word = word)
 
def add301Weeks(user, week_no, delete = False):
    starterWord = None
    finisherWord = None

    if week_no == 0:
        starterWord = "nutrition"
        finisherWord = "gap"
    elif week_no == 1:
        starterWord = "gap"
        finisherWord = "inherit"
    elif week_no == 2:
        starterWord = "inherit"
        finisherWord = "be worth"
    elif week_no == 3:
        starterWord = "be worth"
        finisherWord = "naturally"
    elif week_no == 4:
        starterWord = "naturally"
        finisherWord = "survive"
    elif week_no == 5:
        starterWord = "survive"
        finisherWord = "evidence"
    elif week_no == 6:
        starterWord = "evidence"
        finisherWord = "ancient"
    elif week_no == 7:
        starterWord = "ancient"
        finisherWord = "taste"

    if starterWord == None or finisherWord == None:
        return "ERROR" 


    words = Word.objects.filter(wordLevel = "301")

    start = False
    for word in words:
        if word.englishWord == finisherWord:
            if word.englishWord == "taste":
                if delete:
                    UserWordLink.objects.filter(user = user, word = word).delete()
                else:
                    UserWordLink.objects.create(user = user, word = word)
            break
        if word.englishWord == starterWord:
            start = True
        
        if start:
            if delete:
                UserWordLink.objects.filter(user = user, word = word).delete()
            else:
                UserWordLink.objects.create(user = user, word = word)
 
def add101Weeks(user, week_no, delete = False):
    starterWord = None
    finisherWord = None

    if week_no == 0:
        starterWord = "bus"
        finisherWord = "famous"
    elif week_no == 1:
        starterWord = "famous"
        finisherWord = "transportation"
    elif week_no == 2:
        starterWord = "transportation"
        finisherWord = "chef"
    elif week_no == 3:
        starterWord = "chef"
        finisherWord = "attend"
    elif week_no == 4:
        starterWord = "attend"
        finisherWord = "tribe"
    elif week_no == 5:
        starterWord = "tribe"
        finisherWord = "village"
    elif week_no == 6:
        starterWord = "village"
        finisherWord = "stage"
    elif week_no == 7:
        starterWord = "stage"
        finisherWord = "mixture"
    elif week_no == 8:
        starterWord = "mixture"
        finisherWord = "root"

    if starterWord == None or finisherWord == None:
        return "ERROR" 


    words = Word.objects.filter(wordLevel = "101")

    start = False
    for word in words:
        if word.englishWord == finisherWord:
            if word.englishWord == "root":
                if delete:
                    UserWordLink.objects.filter(user = user, word = word).delete()
                else:
                    UserWordLink.objects.create(user = user, word = word)
            break
        if word.englishWord == starterWord:
            start = True
        
        if start:
            if delete:
                UserWordLink.objects.filter(user = user, word = word).delete()
            else:
                UserWordLink.objects.create(user = user, word = word)
 