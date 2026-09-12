# -*- coding: utf-8 -*-
"""
Örnek sözlük verisi.

Amaç eksiksiz bir sözlük değil, YENİ MODELİN HER KARARINI ekranda
görebilmek:

  courage    -> tek ailede 9 türev, en- ve dis- önekleriyle anlam yön değiştiriyor
  progress   -> aynı yazılış iki ayrı kayıt: isim ve fiil
  bank       -> tek kelime, İKİ anlam; her anlamın KENDİ collocation'ları ve cümleleri
  possess    -> "daha basit karşılığı": have (ama daha resmî)
  decision   -> make a decision (do a decision DEĞİL)
  discourage -> discourage sb FROM doing (kalıp), decide TO do (kalıp)
  detrimental-> akademik üslup + olumsuz ton
  sympathetic-> yanlış dost: "sempatik" değil
  sensible   -> sensitive ile karıştırılan çift
  slow       -> sıfatın çekim biçimleri: slower / slowest
  go, have   -> düzensiz fiiller: went/gone, had/had

Gerçek sözlük verisi listelerden + AI ile üretilecek; bu dosya yalnızca
tohum. `python manage.py seed_words` ile yüklenir.

Biçim:
  AILELER = [{"root", "note", "words": [{
      "text", "pos", "cefr", "v2", "v3", "false_friends",
      "meanings": [{"tr", "definition", "sentiment", "register",
                    "categories", "collocations", "patterns", "sentences"}]}]}]

  collocations: (yapı, tür, Türkçesi)      patterns: (kalıp, tür, not)
  false_friends: (benzeyen Türkçe, sanılan anlam, o anlamın doğru karşılığı)
"""

AILELER = [   {   'root': 'courage',
        'note': 'Cesaret kökü. en- öneki cesaret verir, dis- öneki cesareti kırar.',
        'words': [   {   'text': 'courage',
                         'pos': 'noun',
                         'cefr': 'B1',
                         'meanings': [   {   'tr': 'cesaret',
                                             'definition': 'the ability to do something that '
                                                           'frightens you',
                                             'sentiment': 'positive',
                                             'register': 'neutral',
                                             'categories': ['Gündelik'],
                                             'collocations': [   (   'take courage',
                                                                     'verb_noun',
                                                                     'cesaret toplamak'),
                                                                 (   'moral courage',
                                                                     'adj_noun',
                                                                     'manevi cesaret')],
                                             'patterns': [   (   'have the courage to do sth',
                                                                 'verb_form',
                                                                 'to + fiil; courage of doing '
                                                                 'DEĞİL')],
                                             'sentences': [   'It takes courage to admit that '
                                                              'you were wrong.',
                                                              'She showed great courage during '
                                                              'the interview.',
                                                              'He did not have the courage to '
                                                              'tell her the truth.',
                                                              'Moral courage is rarer than '
                                                              'physical courage.',
                                                              'The soldiers were praised for '
                                                              'their courage under fire.']}]},
                     {   'text': 'courageous',
                         'pos': 'adjective',
                         'cefr': 'B2',
                         'meanings': [   {   'tr': 'cesur',
                                             'definition': 'showing courage',
                                             'sentiment': 'positive',
                                             'register': 'neutral',
                                             'categories': [],
                                             'collocations': [],
                                             'patterns': [],
                                             'sentences': [   'The courageous decision saved '
                                                              'the whole project.',
                                                              'She was courageous enough to '
                                                              'question her own teacher.',
                                                              'It was a courageous attempt, '
                                                              'even though it failed.',
                                                              'Only a courageous leader would '
                                                              'admit such a mistake.',
                                                              'He made a courageous stand '
                                                              'against the new policy.']}]},
                     {   'text': 'courageously',
                         'pos': 'adverb',
                         'cefr': 'C1',
                         'meanings': [   {   'tr': 'cesurca',
                                             'definition': 'in a courageous way',
                                             'sentiment': 'positive',
                                             'register': 'neutral',
                                             'categories': [],
                                             'collocations': [],
                                             'patterns': [],
                                             'sentences': [   'He courageously defended his '
                                                              'argument in front of the class.',
                                                              'The villagers courageously '
                                                              'refused to leave their homes.',
                                                              'She courageously admitted that '
                                                              'the data were wrong.',
                                                              'They fought courageously until '
                                                              'the very last moment.',
                                                              'The journalist courageously '
                                                              'published the whole story.']}]},
                     {   'text': 'encourage',
                         'pos': 'verb',
                         'cefr': 'A2',
                         'meanings': [   {   'tr': 'cesaretlendirmek, teşvik etmek',
                                             'definition': 'to give someone confidence or '
                                                           'support to do something',
                                             'sentiment': 'positive',
                                             'register': 'neutral',
                                             'categories': [],
                                             'collocations': [   (   'strongly encourage',
                                                                     'adv_verb',
                                                                     'şiddetle teşvik etmek')],
                                             'patterns': [   (   'encourage sb to do sth',
                                                                 'verb_form',
                                                                 'to + fiil; encourage sb '
                                                                 'doing DEĞİL')],
                                             'sentences': [   'My teacher encouraged me to '
                                                              'apply for the scholarship.',
                                                              'Low prices encourage people to '
                                                              'buy more than they need.',
                                                              'We strongly encourage students '
                                                              'to read every day.',
                                                              'Her success encouraged others '
                                                              'to try the same path.',
                                                              'The government encourages '
                                                              'families to save energy.']}]},
                     {   'text': 'encouraging',
                         'pos': 'adjective',
                         'cefr': 'B1',
                         'meanings': [   {   'tr': 'cesaret verici, umut verici',
                                             'definition': 'giving hope or confidence',
                                             'sentiment': 'positive',
                                             'register': 'neutral',
                                             'categories': [],
                                             'collocations': [],
                                             'patterns': [],
                                             'sentences': [   'The first results are '
                                                              'encouraging but not conclusive.',
                                                              'She gave me an encouraging '
                                                              'smile before the exam.',
                                                              'It is encouraging to see so '
                                                              'many young researchers here.',
                                                              'The report ends on an '
                                                              'encouraging note.',
                                                              'There were encouraging signs of '
                                                              'recovery in the economy.']}]},
                     {   'text': 'encouragement',
                         'pos': 'noun',
                         'cefr': 'B2',
                         'meanings': [   {   'tr': 'teşvik, cesaretlendirme',
                                             'definition': 'words or actions that give someone '
                                                           'confidence',
                                             'sentiment': 'positive',
                                             'register': 'neutral',
                                             'categories': [],
                                             'collocations': [],
                                             'patterns': [],
                                             'sentences': [   'With a little encouragement, '
                                                              'she finished the essay.',
                                                              'Children need encouragement far '
                                                              'more than criticism.',
                                                              'His letter was a source of '
                                                              'great encouragement to me.',
                                                              'The prize is meant as an '
                                                              'encouragement to young writers.',
                                                              'She offered quiet encouragement '
                                                              'rather than advice.']}]},
                     {   'text': 'discourage',
                         'pos': 'verb',
                         'cefr': 'B1',
                         'meanings': [   {   'tr': 'cesaretini kırmak, caydırmak',
                                             'definition': 'to make someone less confident or '
                                                           'less willing to do something',
                                             'sentiment': 'negative',
                                             'register': 'neutral',
                                             'categories': [],
                                             'collocations': [],
                                             'patterns': [   (   'discourage sb from doing sth',
                                                                 'preposition',
                                                                 'from + -ing; from to DEĞİL')],
                                             'sentences': [   'Bad grades should not '
                                                              'discourage you from trying '
                                                              'again.',
                                                              'High taxes discourage '
                                                              'investment in the region.',
                                                              'Do not let one failure '
                                                              'discourage you completely.',
                                                              'The weather discouraged us from '
                                                              'going out.',
                                                              'Nothing seemed to discourage '
                                                              'her from her goal.']}]},
                     {   'text': 'discouraging',
                         'pos': 'adjective',
                         'cefr': 'B2',
                         'meanings': [   {   'tr': 'cesaret kırıcı',
                                             'definition': 'making you lose hope or confidence',
                                             'sentiment': 'negative',
                                             'register': 'neutral',
                                             'categories': [],
                                             'collocations': [],
                                             'patterns': [],
                                             'sentences': [   'The early results were rather '
                                                              'discouraging.',
                                                              'It is discouraging to work hard '
                                                              'and see no progress.',
                                                              'She received a discouraging '
                                                              'reply from the committee.',
                                                              'The discouraging news spread '
                                                              'quickly among the staff.',
                                                              'Do not read too much into one '
                                                              'discouraging comment.']}]},
                     {   'text': 'discouragement',
                         'pos': 'noun',
                         'cefr': 'C1',
                         'meanings': [   {   'tr': 'cesaret kırıklığı',
                                             'definition': 'a feeling of having lost '
                                                           'confidence',
                                             'sentiment': 'negative',
                                             'register': 'neutral',
                                             'categories': [],
                                             'collocations': [],
                                             'patterns': [],
                                             'sentences': [   'After months of discouragement, '
                                                              'he finally gave up.',
                                                              'Discouragement is the biggest '
                                                              'danger for a beginner.',
                                                              'She spoke openly about her '
                                                              'periods of discouragement.',
                                                              'A word of praise can undo weeks '
                                                              'of discouragement.',
                                                              'He hid his discouragement '
                                                              'behind a calm face.']}]}]},
    {   'root': 'relate',
        'note': 'İlişki kurmak kökü; isim, sıfat ve zarf türevleri sık sınav konusu.',
        'words': [   {   'text': 'relate',
                         'pos': 'verb',
                         'cefr': 'B1',
                         'meanings': [   {   'tr': 'ilişkilendirmek, bağlantı kurmak',
                                             'definition': 'to show or feel a connection '
                                                           'between two things',
                                             'sentiment': 'neutral',
                                             'register': 'neutral',
                                             'categories': [],
                                             'collocations': [],
                                             'patterns': [   (   'relate to sth',
                                                                 'preposition',
                                                                 'to + isim')],
                                             'sentences': [   'The study relates poverty to '
                                                              'poor health.',
                                                              'I cannot relate these two '
                                                              'results at all.',
                                                              'Students learn better when they '
                                                              'relate new facts to old ones.',
                                                              'Many readers relate strongly to '
                                                              'the main character.',
                                                              'The report relates the increase '
                                                              'to recent policy changes.']}]},
                     {   'text': 'relation',
                         'pos': 'noun',
                         'cefr': 'B1',
                         'meanings': [   {   'tr': 'ilişki, bağlantı',
                                             'definition': 'a connection between two or more '
                                                           'things',
                                             'sentiment': 'neutral',
                                             'register': 'neutral',
                                             'categories': ['Sosyoloji'],
                                             'collocations': [   (   'close relation',
                                                                     'adj_noun',
                                                                     'yakın ilişki')],
                                             'patterns': [],
                                             'sentences': [   'There is a clear relation '
                                                              'between income and education.',
                                                              'The relation between the two '
                                                              'events is not obvious.',
                                                              'Scientists study the relation '
                                                              'of diet to heart disease.',
                                                              'He explained the relation in a '
                                                              'single sentence.',
                                                              'This finding has no relation to '
                                                              'our earlier work.']}]},
                     {   'text': 'relationship',
                         'pos': 'noun',
                         'cefr': 'A2',
                         'meanings': [   {   'tr': 'ilişki',
                                             'definition': 'the way two people or groups '
                                                           'behave towards each other',
                                             'sentiment': 'neutral',
                                             'register': 'neutral',
                                             'categories': ['Sosyoloji', 'Psikoloji'],
                                             'collocations': [   (   'build a relationship',
                                                                     'verb_noun',
                                                                     'ilişki kurmak'),
                                                                 (   'a close relationship',
                                                                     'adj_noun',
                                                                     'yakın ilişki')],
                                             'patterns': [   (   'a relationship between A and '
                                                                 'B',
                                                                 'structure',
                                                                 'between … and …; between … '
                                                                 'to … DEĞİL')],
                                             'sentences': [   'They have a close working '
                                                              'relationship.',
                                                              'The relationship between the '
                                                              'two countries has improved.',
                                                              'A good relationship with your '
                                                              'supervisor matters a lot.',
                                                              'Their relationship changed '
                                                              'after the argument.',
                                                              'She wrote about the '
                                                              'relationship between memory and '
                                                              'emotion.']}]},
                     {   'text': 'relative',
                         'pos': 'adjective',
                         'cefr': 'B2',
                         'meanings': [   {   'tr': 'göreceli, bağıl',
                                             'definition': 'considered in comparison with '
                                                           'something else',
                                             'sentiment': 'neutral',
                                             'register': 'neutral',
                                             'categories': [],
                                             'collocations': [],
                                             'patterns': [],
                                             'sentences': [   'The relative importance of the '
                                                              'two factors is unclear.',
                                                              'They lived in relative comfort '
                                                              'after the move.',
                                                              'Success is a relative term in '
                                                              'this field.',
                                                              'The relative cost of the '
                                                              'project has fallen.',
                                                              'We enjoyed the relative quiet '
                                                              'of the early morning.']}]},
                     {   'text': 'relatively',
                         'pos': 'adverb',
                         'cefr': 'B2',
                         'meanings': [   {   'tr': 'göreceli olarak, nispeten',
                                             'definition': 'to a certain degree, in comparison',
                                             'sentiment': 'neutral',
                                             'register': 'neutral',
                                             'categories': [],
                                             'collocations': [],
                                             'patterns': [],
                                             'sentences': [   'The exam was relatively easy '
                                                              'this year.',
                                                              'Relatively few students chose '
                                                              'the second option.',
                                                              'The process is relatively '
                                                              'simple once you start.',
                                                              'Prices remained relatively '
                                                              'stable last year.',
                                                              'She is relatively new to the '
                                                              'department.']}]}]},
    {   'root': 'progress',
        'note': 'Aynı yazılış, iki ayrı kayıt: progress (isim) ve progress (fiil).',
        'words': [   {   'text': 'progress',
                         'pos': 'noun',
                         'cefr': 'A2',
                         'meanings': [   {   'tr': 'ilerleme, gelişme',
                                             'definition': 'movement towards a better or more '
                                                           'developed state',
                                             'sentiment': 'positive',
                                             'register': 'neutral',
                                             'categories': ['Akademik'],
                                             'collocations': [   (   'make progress',
                                                                     'verb_noun',
                                                                     'ilerleme kaydetmek — do '
                                                                     'progress DEĞİL'),
                                                                 (   'steady progress',
                                                                     'adj_noun',
                                                                     'istikrarlı ilerleme')],
                                             'patterns': [],
                                             'sentences': [   'She has made remarkable '
                                                              'progress this term.',
                                                              'Progress in the field has been '
                                                              'slow but steady.',
                                                              'The teacher keeps a record of '
                                                              "each student's progress.",
                                                              'Little progress was made during '
                                                              'the meeting.',
                                                              'Technological progress changed '
                                                              'the whole industry.']}]},
                     {   'text': 'progress',
                         'pos': 'verb',
                         'cefr': 'B2',
                         'meanings': [   {   'tr': 'ilerlemek',
                                             'definition': 'to move forward or develop over '
                                                           'time',
                                             'sentiment': 'neutral',
                                             'register': 'formal',
                                             'categories': [],
                                             'collocations': [],
                                             'patterns': [],
                                             'sentences': [   'The work progressed more slowly '
                                                              'than expected.',
                                                              'As the disease progresses, '
                                                              'symptoms become clearer.',
                                                              'Students progress at very '
                                                              'different speeds.',
                                                              'The talks progressed well '
                                                              'during the first week.',
                                                              'Her writing has progressed a '
                                                              'great deal this year.']}]}]},
    {   'root': 'bank',
        'note': "Tek kelime, iki farklı anlam. Anlam kelimenin değil, Meaning'in özelliği.",
        'words': [   {   'text': 'bank',
                         'pos': 'noun',
                         'cefr': 'A1',
                         'meanings': [   {   'tr': 'banka',
                                             'definition': 'an organization that keeps and '
                                                           'lends money',
                                             'sentiment': 'neutral',
                                             'register': 'neutral',
                                             'categories': ['Ekonomi'],
                                             'collocations': [   (   'open a bank account',
                                                                     'verb_noun',
                                                                     'banka hesabı açmak'),
                                                                 (   'central bank',
                                                                     'adj_noun',
                                                                     'merkez bankası')],
                                             'patterns': [],
                                             'sentences': [   'I opened a bank account on my '
                                                              'first day at university.',
                                                              'The central bank raised '
                                                              'interest rates again.',
                                                              'Most banks close at five in the '
                                                              'afternoon.',
                                                              'She works for an investment '
                                                              'bank in London.',
                                                              'The bank refused to give him a '
                                                              'loan.']},
                                         {   'tr': 'nehir kıyısı',
                                             'definition': 'the land along the side of a river',
                                             'sentiment': 'neutral',
                                             'register': 'neutral',
                                             'categories': ['Coğrafya'],
                                             'collocations': [   (   'the river bank',
                                                                     'noun_noun',
                                                                     'nehir kıyısı'),
                                                                 (   'the opposite bank',
                                                                     'adj_noun',
                                                                     'karşı kıyı')],
                                             'patterns': [],
                                             'sentences': [   'We sat on the bank and watched '
                                                              'the boats go by.',
                                                              'The river burst its banks after '
                                                              'three days of rain.',
                                                              'Tall trees grow along the '
                                                              'eastern bank.',
                                                              'He swam to the opposite bank in '
                                                              'under a minute.',
                                                              'The northern bank of the river '
                                                              'is protected land.']}]}]},
    {   'root': 'possess',
        'note': 'possess ≈ have. Zor kelimeyi bilinen kelimeyle tanımlama örneği.',
        'words': [   {   'text': 'possess',
                         'pos': 'verb',
                         'cefr': 'C1',
                         'meanings': [   {   'tr': 'sahip olmak',
                                             'definition': 'to own or have something',
                                             'sentiment': 'neutral',
                                             'register': 'formal',
                                             'categories': [],
                                             'collocations': [],
                                             'patterns': [   (   'possess sth',
                                                                 'verb_form',
                                                                 'doğrudan nesne alır; possess '
                                                                 'of DEĞİL')],
                                             'sentences': [   'He possesses a rare talent for '
                                                              'languages.',
                                                              'The suspect was found to '
                                                              'possess false documents.',
                                                              'She possesses the qualities we '
                                                              'are looking for.',
                                                              'Few countries possess such '
                                                              'natural resources.',
                                                              'The building possesses a '
                                                              'certain old-fashioned '
                                                              'charm.']}]},
                     {   'text': 'possession',
                         'pos': 'noun',
                         'cefr': 'B2',
                         'meanings': [   {   'tr': 'sahiplik, mülkiyet',
                                             'definition': 'the state of having or owning '
                                                           'something',
                                             'sentiment': 'neutral',
                                             'register': 'formal',
                                             'categories': [],
                                             'collocations': [],
                                             'patterns': [],
                                             'sentences': [   'The land came into his '
                                                              'possession last year.',
                                                              'All her possessions fitted into '
                                                              'one small bag.',
                                                              'Possession of the document '
                                                              'proved his claim.',
                                                              'The keys are in the possession '
                                                              'of the manager.',
                                                              'They lost possession of the '
                                                              'house after the trial.']}]}]},
    {   'root': 'have',
        'note': 'Düzensiz fiil: had / had.',
        'words': [   {   'text': 'have',
                         'pos': 'verb',
                         'cefr': 'A1',
                         'meanings': [   {   'tr': 'sahip olmak, -si olmak',
                                             'definition': 'to own, hold or contain something',
                                             'sentiment': 'neutral',
                                             'register': 'neutral',
                                             'categories': [],
                                             'collocations': [],
                                             'patterns': [],
                                             'sentences': [   'They have a small house near '
                                                              'the sea.',
                                                              'We had very little time to '
                                                              'prepare.',
                                                              'She has three brothers and one '
                                                              'sister.',
                                                              'The room has two large windows.',
                                                              'I have never had such a strange '
                                                              'experience.']}],
                         'v2': 'had',
                         'v3': 'had'}]},
    {   'root': 'decide',
        'note': 'Karar kökü; in- öneki olumsuzluk katıyor.',
        'words': [   {   'text': 'decide',
                         'pos': 'verb',
                         'cefr': 'A1',
                         'meanings': [   {   'tr': 'karar vermek',
                                             'definition': 'to choose something after thinking '
                                                           'about it',
                                             'sentiment': 'neutral',
                                             'register': 'neutral',
                                             'categories': [],
                                             'collocations': [],
                                             'patterns': [   (   'decide to do sth',
                                                                 'verb_form',
                                                                 'to + fiil; decide doing '
                                                                 'DEĞİL'),
                                                             (   'decide on sth',
                                                                 'preposition',
                                                                 'seçenekler arasından '
                                                                 'seçmek')],
                                             'sentences': [   'They decided to postpone the '
                                                              'meeting.',
                                                              'It took her a week to decide.',
                                                              'The committee will decide on '
                                                              'Friday.',
                                                              'He could not decide between the '
                                                              'two offers.',
                                                              'We decided that the plan was '
                                                              'too risky.']}]},
                     {   'text': 'decision',
                         'pos': 'noun',
                         'cefr': 'A2',
                         'meanings': [   {   'tr': 'karar',
                                             'definition': 'a choice that you make after '
                                                           'thinking',
                                             'sentiment': 'neutral',
                                             'register': 'neutral',
                                             'categories': [],
                                             'collocations': [   (   'make a decision',
                                                                     'verb_noun',
                                                                     'karar vermek — do a '
                                                                     'decision DEĞİL'),
                                                                 (   'a tough decision',
                                                                     'adj_noun',
                                                                     'zor bir karar')],
                                             'patterns': [   (   'the decision to do sth',
                                                                 'verb_form',
                                                                 'to + fiil')],
                                             'sentences': [   'It was the hardest decision of '
                                                              'her life.',
                                                              'The decision was taken without '
                                                              'any discussion.',
                                                              'We must reach a decision before '
                                                              'Monday.',
                                                              'His decision surprised everyone '
                                                              'in the room.',
                                                              'Good decisions rarely come from '
                                                              'tired minds.']}]},
                     {   'text': 'decisive',
                         'pos': 'adjective',
                         'cefr': 'B2',
                         'meanings': [   {   'tr': 'kararlı; belirleyici',
                                             'definition': 'able to make decisions quickly, or '
                                                           'having a major influence',
                                             'sentiment': 'positive',
                                             'register': 'neutral',
                                             'categories': [],
                                             'collocations': [],
                                             'patterns': [],
                                             'sentences': [   'A decisive leader is not always '
                                                              'a popular one.',
                                                              'The final goal was decisive.',
                                                              'She was decisive when everyone '
                                                              'else hesitated.',
                                                              'That meeting proved decisive '
                                                              'for the whole project.',
                                                              'We need a decisive answer, not '
                                                              'another delay.']}]},
                     {   'text': 'indecisive',
                         'pos': 'adjective',
                         'cefr': 'C1',
                         # İki anlam, iki ayrı cümle kümesi: "kararsız" kişi
                         # içindir, "sonuç getirmeyen" oylama/deney içindir.
                         # Eski modelde beşi de tek kelimede duruyordu.
                         'meanings': [   {   'tr': 'kararsız',
                                             'definition': 'not able to make decisions',
                                             'sentiment': 'negative',
                                             'register': 'neutral',
                                             'categories': [],
                                             'collocations': [],
                                             'patterns': [],
                                             'sentences': [   'He is too indecisive to lead a '
                                                              'team.',
                                                              'Her indecisive manner slowed '
                                                              'everything down.',
                                                              'Being indecisive can cost more '
                                                              'than a wrong choice.']},
                                         {   'tr': 'sonuç getirmeyen',
                                             'definition': 'not producing a clear result',
                                             'sentiment': 'neutral',
                                             'register': 'neutral',
                                             'categories': [],
                                             'collocations': [],
                                             'patterns': [],
                                             'sentences': [   'The battle was long and '
                                                              'indecisive.',
                                                              'The vote was indecisive and had '
                                                              'to be repeated.',
                                                              'Two indecisive experiments told '
                                                              'us nothing.']}]}]},
    {   'root': 'slow',
        'note': 'Sıfatın çekim biçimleri: slower / slowest. Çekim yeni kelime değildir.',
        'words': [   {   'text': 'slow',
                         'pos': 'adjective',
                         'cefr': 'A1',
                         'meanings': [   {   'tr': 'yavaş',
                                             'definition': 'moving or happening without much '
                                                           'speed',
                                             'sentiment': 'neutral',
                                             'register': 'neutral',
                                             'categories': [],
                                             'collocations': [   (   'a slow process',
                                                                     'adj_noun',
                                                                     'yavaş bir süreç')],
                                             'patterns': [],
                                             'sentences': [   'Progress was slow but steady.',
                                                              'The train is slower than the '
                                                              'bus.',
                                                              'This is the slowest computer in '
                                                              'the office.',
                                                              'She gave a slow, careful '
                                                              'answer.',
                                                              'Recovery after the illness was '
                                                              'very slow.']}]},
                     {   'text': 'slowly',
                         'pos': 'adverb',
                         'cefr': 'A1',
                         'meanings': [   {   'tr': 'yavaşça',
                                             'definition': 'in a slow way',
                                             'sentiment': 'neutral',
                                             'register': 'neutral',
                                             'categories': [],
                                             'collocations': [],
                                             'patterns': [],
                                             'sentences': [   'He walked slowly towards the '
                                                              'door.',
                                                              'The situation is slowly '
                                                              'improving.',
                                                              'Read the question slowly and '
                                                              'carefully.',
                                                              'Prices rose slowly over the '
                                                              'year.',
                                                              'She slowly began to understand '
                                                              'the problem.']}]}]},
    {   'root': 'harm',
        'note': 'detrimental kelimesinin basit karşılığı bu ailede.',
        'words': [   {   'text': 'harm',
                         'pos': 'noun',
                         'cefr': 'A2',
                         'meanings': [   {   'tr': 'zarar',
                                             'definition': 'physical or other injury or damage',
                                             'sentiment': 'negative',
                                             'register': 'neutral',
                                             'categories': [],
                                             'collocations': [   (   'cause harm',
                                                                     'verb_noun',
                                                                     'zarar vermek'),
                                                                 (   'serious harm',
                                                                     'adj_noun',
                                                                     'ciddi zarar')],
                                             'patterns': [],
                                             'sentences': [   'The storm did little harm to '
                                                              'the building.',
                                                              'There is no harm in asking.',
                                                              'Smoking causes serious harm to '
                                                              'health.',
                                                              'He meant no harm by the remark.',
                                                              'The new rules protect children '
                                                              'from harm.']}]},
                     {   'text': 'harmful',
                         'pos': 'adjective',
                         'cefr': 'B1',
                         'meanings': [   {   'tr': 'zararlı',
                                             'definition': 'causing damage or injury',
                                             'sentiment': 'negative',
                                             'register': 'neutral',
                                             'categories': [],
                                             'collocations': [],
                                             'patterns': [   (   'harmful to sb/sth',
                                                                 'preposition',
                                                                 'to + isim')],
                                             'sentences': [   'Too much sun is harmful to the '
                                                              'skin.',
                                                              'The chemical is harmful if '
                                                              'swallowed.',
                                                              'Harmful effects may appear '
                                                              'years later.',
                                                              'Stress can be as harmful as '
                                                              'poor diet.',
                                                              'They banned the harmful '
                                                              'substance completely.']}]},
                     {   'text': 'harmless',
                         'pos': 'adjective',
                         'cefr': 'B2',
                         'meanings': [   {   'tr': 'zararsız',
                                             'definition': 'not able to cause harm',
                                             'sentiment': 'positive',
                                             'register': 'neutral',
                                             'categories': [],
                                             'collocations': [],
                                             'patterns': [],
                                             'sentences': [   'The snake is completely '
                                                              'harmless.',
                                                              'It was a harmless joke, nothing '
                                                              'more.',
                                                              'The substance is harmless in '
                                                              'small amounts.',
                                                              'He seemed a harmless old man.',
                                                              'Most of these insects are quite '
                                                              'harmless.']}]}]},
    {   'root': 'detriment',
        'note': 'detrimental ≈ harmful, ama daha resmî ve akademik.',
        'words': [   {   'text': 'detrimental',
                         'pos': 'adjective',
                         'cefr': 'C1',
                         'meanings': [   {   'tr': 'zararlı',
                                             'definition': 'causing harm or damage',
                                             'sentiment': 'negative',
                                             'register': 'academic',
                                             'categories': ['Akademik'],
                                             'collocations': [],
                                             'patterns': [   (   'detrimental to sth',
                                                                 'preposition',
                                                                 'to + isim; detrimental for '
                                                                 'DEĞİL')],
                                             'sentences': [   'Late nights are detrimental to '
                                                              'your health.',
                                                              'The policy proved detrimental '
                                                              'to small businesses.',
                                                              'Noise has a detrimental effect '
                                                              'on concentration.',
                                                              'Such delays are detrimental to '
                                                              'the whole project.',
                                                              'The study found no detrimental '
                                                              'consequences.']}]}]},
    {   'root': 'sympathy',
        'note': 'Yunanca sym- (birlikte) + pathos (duygu): birlikte hissetmek.',
        'words': [   {   'text': 'sympathy',
                         'pos': 'noun',
                         'cefr': 'B2',
                         'meanings': [   {   'tr': 'anlayış, şefkat; başsağlığı',
                                             'definition': 'the feeling of being sorry for '
                                                           'someone who is in trouble',
                                             'sentiment': 'positive',
                                             'register': 'neutral',
                                             'categories': ['Psikoloji'],
                                             'collocations': [   (   'express sympathy',
                                                                     'verb_noun',
                                                                     'taziyede bulunmak'),
                                                                 (   'deep sympathy',
                                                                     'adj_noun',
                                                                     'derin bir anlayış')],
                                             'patterns': [   (   'sympathy for sb',
                                                                 'preposition',
                                                                 'for + kişi')],
                                             'sentences': [   'She felt great sympathy for the '
                                                              'families who lost their homes.',
                                                              'The letter expressed the '
                                                              "committee's deepest sympathy.",
                                                              'He listened with sympathy but '
                                                              'offered no advice.',
                                                              'There is little public sympathy '
                                                              'for the new tax.',
                                                              'Her sympathy for the students '
                                                              'was obvious to everyone.']}]},
                     {   'text': 'sympathetic',
                         'pos': 'adjective',
                         'cefr': 'B2',
                         'meanings': [   {   'tr': 'anlayışlı, şefkatli',
                                             'definition': 'showing that you understand and '
                                                           "care about someone's problems",
                                             'sentiment': 'positive',
                                             'register': 'neutral',
                                             'categories': ['Psikoloji'],
                                             'collocations': [],
                                             'patterns': [   (   'sympathetic to/towards sb',
                                                                 'preposition',
                                                                 'to ya da towards + kişi')],
                                             'sentences': [   'My supervisor was sympathetic '
                                                              'when I explained the delay.',
                                                              'She gave me a sympathetic look '
                                                              'and said nothing.',
                                                              'The committee was sympathetic '
                                                              'to our request.',
                                                              'A sympathetic doctor makes a '
                                                              'difficult diagnosis easier to '
                                                              'hear.',
                                                              'He is not a sympathetic '
                                                              'character in the novel.']}],
                         'false_friends': [   (   'sempatik',
                                                  'cana yakın, hoş',
                                                  'likeable, friendly, charming')]},
                     {   'text': 'sympathize',
                         'pos': 'verb',
                         'cefr': 'C1',
                         'meanings': [   {   'tr': 'anlayışla karşılamak, empati kurmak',
                                             'definition': 'to feel sorry for someone and show '
                                                           'you understand',
                                             'sentiment': 'positive',
                                             'register': 'neutral',
                                             'categories': [],
                                             'collocations': [],
                                             'patterns': [   (   'sympathize with sb',
                                                                 'preposition',
                                                                 'with + kişi')],
                                             'sentences': [   'I sympathize with students who '
                                                              'work while studying.',
                                                              'It is easy to sympathize with '
                                                              'her position.',
                                                              'He sympathized but did not '
                                                              'change his decision.',
                                                              'Readers sympathize with the '
                                                              'narrator from the first page.',
                                                              'We all sympathized with the '
                                                              "family's loss."]}]}]},
    {   'root': 'sense',
        'note': 'sensible ve sensitive aynı kökten gelir ama zıt yönlere gider.',
        'words': [   {   'text': 'sense',
                         'pos': 'noun',
                         'cefr': 'A2',
                         'meanings': [   {   'tr': 'duyu; anlam; sağduyu',
                                             'definition': 'an ability to understand or feel '
                                                           'something',
                                             'sentiment': 'neutral',
                                             'register': 'neutral',
                                             'categories': [],
                                             'collocations': [   (   'common sense',
                                                                     'adj_noun',
                                                                     'sağduyu'),
                                                                 (   'make sense',
                                                                     'verb_noun',
                                                                     'anlam ifade etmek — have '
                                                                     'sense DEĞİL')],
                                             'patterns': [],
                                             'sentences': [   'Her explanation finally made '
                                                              'sense to me.',
                                                              'Common sense tells us to check '
                                                              'the data twice.',
                                                              'He has a good sense of '
                                                              'direction.',
                                                              'The word has three different '
                                                              'senses in this dictionary.',
                                                              'There is no sense in arguing '
                                                              'about it now.']}]},
                     {   'text': 'sensible',
                         'pos': 'adjective',
                         'cefr': 'B1',
                         'meanings': [   {   'tr': 'mantıklı, makul',
                                             'definition': 'reasonable and showing good '
                                                           'judgement',
                                             'sentiment': 'positive',
                                             'register': 'neutral',
                                             'categories': [],
                                             'collocations': [],
                                             'patterns': [],
                                             'sentences': [   'Taking the early train was a '
                                                              'sensible decision.',
                                                              'She is far too sensible to '
                                                              'believe that story.',
                                                              'A sensible diet is better than '
                                                              'a strict one.',
                                                              'It would be sensible to ask '
                                                              'before you start.',
                                                              'He gave me sensible advice '
                                                              'about the exam.']}],
                         'false_friends': [   (   'hassas',
                                                  'kolay etkilenen, duyarlı',
                                                  'sensitive')]},
                     {   'text': 'sensitive',
                         'pos': 'adjective',
                         'cefr': 'B2',
                         'meanings': [   {   'tr': 'duyarlı, hassas',
                                             'definition': 'easily affected, hurt or '
                                                           'influenced',
                                             'sentiment': 'neutral',
                                             'register': 'neutral',
                                             'categories': ['Psikoloji'],
                                             'collocations': [],
                                             'patterns': [   (   'sensitive to sth',
                                                                 'preposition',
                                                                 'to + isim')],
                                             'sentences': [   'Children are especially '
                                                              'sensitive to criticism.',
                                                              'This is a sensitive topic in '
                                                              'the classroom.',
                                                              'The instrument is sensitive to '
                                                              'very small changes.',
                                                              'She is sensitive about her '
                                                              'accent.',
                                                              'Sensitive data must never leave '
                                                              'the building.']}],
                         'false_friends': [   (   'sansasyonel',
                                                  'çarpıcı, ses getiren',
                                                  'sensational')]}]},
    {   'root': 'actual',
        'note': "Türkçedeki 'aktüel' ile hiçbir ilgisi yok.",
        'words': [   {   'text': 'actual',
                         'pos': 'adjective',
                         'cefr': 'B1',
                         'meanings': [   {   'tr': 'gerçek, asıl',
                                             'definition': 'real, as opposed to what people '
                                                           'think or say',
                                             'sentiment': 'neutral',
                                             'register': 'neutral',
                                             'categories': [],
                                             'collocations': [],
                                             'patterns': [],
                                             'sentences': [   'The actual cost was twice the '
                                                              'estimate.',
                                                              'Nobody knows the actual number '
                                                              'of speakers.',
                                                              'In actual fact, the experiment '
                                                              'was never repeated.',
                                                              'Her actual words were rather '
                                                              'different.',
                                                              'The actual building is smaller '
                                                              'than it looks in photos.']}],
                         'false_friends': [   (   'aktüel',
                                                  'güncel, şu anki',
                                                  'current, up-to-date')]},
                     {   'text': 'actually',
                         'pos': 'adverb',
                         'cefr': 'B1',
                         'meanings': [   {   'tr': 'aslında, gerçekte',
                                             'definition': 'in fact, in reality',
                                             'sentiment': 'neutral',
                                             'register': 'neutral',
                                             'categories': [],
                                             'collocations': [],
                                             'patterns': [],
                                             'sentences': [   'I thought it was easy, but it '
                                                              'was actually quite hard.',
                                                              'Did you actually read the whole '
                                                              'article?',
                                                              'She actually apologized, which '
                                                              'surprised everyone.',
                                                              'It is not actually a rule, only '
                                                              'a habit.',
                                                              'Actually, the meeting was moved '
                                                              'to Friday.']}],
                         'false_friends': [   (   'aktüel olarak',
                                                  'şu anda, güncel olarak',
                                                  'currently, at present')]}]}]

# Konu alanları; anlamlara etiket olarak takılıyor.
KATEGORILER = ['Akademik', 'Coğrafya', 'Ekonomi', 'Gündelik', 'Psikoloji', 'Sosyoloji']

# Deyimler ve kalıp ifadeler. Kelime değiller, ama öğrenilen birimler.
IFADELER = [   {   'text': 'in the long run',
        'tr': 'uzun vadede',
        'definition': 'over a long period of time in the future',
        'kind': 'fixed',
        'cefr': 'B2',
        'register': 'neutral',
        'categories': ['Akademik', 'Ekonomi'],
        'words': [],
        'sentences': [   'Learning the grammar properly pays off in the long run.',
                         'In the long run, the cheaper option cost us more.']},
    {   'text': 'on the other hand',
        'tr': 'öte yandan, diğer taraftan',
        'definition': 'used to introduce the second of two contrasting points',
        'kind': 'linker',
        'cefr': 'B1',
        'register': 'academic',
        'categories': ['Akademik'],
        'words': [],
        'sentences': [   'The method is slow; on the other hand, it is very accurate.',
                         'On the other hand, some researchers disagree completely.']},
    {   'text': 'to make matters worse',
        'tr': 'üstüne üstlük, işi daha da kötüleştiren şey',
        'definition': 'used before mentioning something that makes a bad situation worse',
        'kind': 'linker',
        'cefr': 'B2',
        'register': 'neutral',
        'sentiment': 'negative',
        'words': [],
        'sentences': [   'We missed the train, and to make matters worse, it started raining.',
                         'To make matters worse, the backup file was also corrupted.']},
    {   'text': 'come to a decision',
        'tr': 'bir karara varmak',
        'definition': 'to finally decide something after thinking about it',
        'kind': 'fixed',
        'cefr': 'B1',
        'register': 'neutral',
        'categories': [],
        'words': ['decision/noun', 'decide/verb'],
        'sentences': [   'The committee came to a decision after three hours.',
                         'They could not come to a decision before the deadline.']},
    {   'text': 'do more harm than good',
        'tr': 'yarardan çok zarar getirmek',
        'definition': 'to have a worse effect than the good it was meant to do',
        'kind': 'idiom',
        'cefr': 'B2',
        'register': 'neutral',
        'sentiment': 'negative',
        'words': ['harm/noun'],
        'sentences': [   'Studying all night usually does more harm than good.',
                         'The new rule did more harm than good to small businesses.']},
    {   'text': 'by and large',
        'tr': 'genel olarak, büyük ölçüde',
        'definition': 'in general, when everything is considered',
        'kind': 'fixed',
        'cefr': 'C1',
        'register': 'formal',
        'categories': ['Akademik'],
        'words': [],
        'sentences': [   'By and large, the results support the original theory.',
                         'The students were, by and large, satisfied with the course.']}]

# (kaynak, hedef, tür, nüans notu) — "kelime/tür" biçiminde
BAGLAR = [   ('possess/verb', 'have/verb', 'simpler', 'Aynı anlam, ama daha resmî ve akademik.'),
    ('detrimental/adjective', 'harmful/adjective', 'simpler', 'Aynı anlam, daha ağır bir dil.'),
    ('encourage/verb', 'discourage/verb', 'antonym', 'en- / dis- önekleri'),
    ('encouraging/adjective', 'discouraging/adjective', 'antonym', None),
    ('harmful/adjective', 'harmless/adjective', 'antonym', None),
    ('detrimental/adjective', 'harmful/adjective', 'synonym', None),
    ('relation/noun', 'relationship/noun', 'synonym', 'relationship daha çok insanlar arası.'),
    ('decisive/adjective', 'indecisive/adjective', 'antonym', 'in- öneki'),
    ('courageous/adjective', 'courage/noun', 'synonym', None),
    (   'sensible/adjective',
        'sensitive/adjective',
        'confused_with',
        'sensible = mantıklı, sensitive = duyarlı. Aynı kökten, zıt yönlere.'),
    (   'sensitive/adjective',
        'sensible/adjective',
        'confused_with',
        'sensitive = duyarlı, sensible = mantıklı.'),
    ('sympathetic/adjective', 'sympathy/noun', 'synonym', None)]
