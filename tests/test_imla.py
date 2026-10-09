"""Osmanlıca imlâ gerileme testi (k/g harfleri, Arapça/Farsça kelimelerin aslî yazımı, tırnak ekleri, yabancı dil). Kod klasöründe:
  docker run --rm -v "$PWD":/k -w /k berzahbey/osmanlica-cevirici:latest python tests/test_imla.py"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app"))
from engine.transliterator import transliterate_text as cevir   # gerçek çıktı (g sesi ك، işaretler silinmiş)

BEKLENEN = {
    # Türkçe kelime, sözlükteki başka kelimeyle çakışıyordu
    "iki": "ایكی", "ikinci": "ایكنجی", "ikisi": "ایكیسی", "bak": "باق", "bakmak": "باقمق", "kuşkusuz": "قوشقوسز",
    "Hak'dan": "حقّدن", "kez": "كز", "ergen": "اركن",
    # sözlükteki asıl (şapkalı) kelimeler korunur
    "bâk": "باك", "köşk": "كوشك", "hâkdan": "خاكدان",
    # kural motoru: k/g yanındaki ünlüye göre (kalın: ق غ, ince: ك ك)
    "bugün": "بوكون", "herhangi": "هر هانكی", "çıkabilir": "چیقابیلیر", "gidiyor": "كیدییور", "dergâh": "دركاه",
    # g sesi gaf, k sesi kef (sözlük düzeltmesi)
    "hângâh": "خانكاه", "tengdil": None, "kedûret": "كدورت", "mürekkib": "مركّب",
    # Arapça/Farsça kelimeler aslî imlâsıyla
    "Mustafa": "مصطفی", "yani": "یعنی", "fiil": "فعل", "fiilleri": "فعللری", "mümkün": "ممكن", "maksat": "مقصد",
    "galip": "غالب", "istidat": "استعداد", "tesir": "تأثیر", "cevap": "جواب", "talep": "طلب", "heyet": "هیئت",
    "miktar": "مقدار", "mükâşefe": "مكاشفه", "mükaşefe": "مكاشفه", "takip": "تعقیب", "Hz": "حضرت",
    # değişmemesi gerekenler
    "günah": "كناه", "kitap": "كتاب", "zevk": "ذوق", "teşvik": "تشویق", "kâr": "كار", "kâğıt": "كاغد",
    "gelmek": "كلمك", "gece": "كیجه", "değil": "دكل", "doğru": "طوغری", "yirmi": "یكرمی", "bir": "بر",
    "karargâh": "قراركاه", "tebliğ": "تبلیغ", "Kur'an": "قرآن", "Allah": "الله", "evet": "اوت", "yap": "یاپ",
    # imlâ turu 2: sözlük denetleyicisinin bulduğu bozuk kayıtlar
    "mal": "مال", "malları": "ماللری", "dakika": "دقیقه", "mahlukat": "مخلوقات", "vehm": "وهم", "kabr": "قبر",
    "felsefe": "فلسفه", "irşad": "ارشاد", "oysa": "اویسه", "celal": "جلال", "zemin": "زمین", "elif": "الف",
    "Hakk'a": "حقّه", "Rabb'e": "ربّه", "Âdem'i": "آدمی", "nev'i": "نوع", "O'nun": "اونڭ", "Kur'an'ın": "قرآنڭ",
    "Ali'lerdir": "علیلردر",
    # Türkçe fiillerin tarihî yazımı, kelime başında medli elif
    "ettiği": "ایتدیكی", "edilmiştir": "ایدیلمشدر", "verdiği": "ویردیكی", "demiştir": "دیمشدر", "dediğimiz": "دیدیكمز",
    "anlam": "آڭلام", "açık": "آچیق", "almak": "آلمق",
    # sık kelimeler ve özel adlar
    "nitekim": "نیته‌كیم", "buna": "بوڭا", "birşey": "بر شی", "Ali": "علی", "Hasan": "حسن", "Mısır": "مصر",
    # derin ek ayırma (Arapça kök + iyelik/hâl ekleri)
    "âyetlerimizi": "آیتلرمزی", "kalbiniz": "قلبڭز", "şeklindeki": "شكلندهكی",
    # imlâ turu 3: OpenITI sıklık listesiyle gözden geçirilen kelimeler
    "tevilat": "تأویلات", "istidadı": "استعدادی", "münezzehtir": "منزّهدر", "rububiyet": "ربوبیت", "muvahhid": "موحّد",
    "mübiyn": "مبین", "risalet": "رسالت", "bizzat": "بالذّات",
}

# Cümle düzeyi (tırnak, yabancı dil, "Hak Teâlâ")
CUMLE = {
    "Hak Teâlâ buyurdu.": "حقّ تعالی بویوردی.",
    "“O”dur.": "\"او\"در.",
    "“Hak”tan geldi.": "\"حقّ\"دن كلدی.",
    "Bkz. Essai de Chronologie des oeuvres de al-Ghazali, Paris 1959.":
        "بقز. Essai de Chronologie des oeuvres de al-Ghazali, Paris 1959.",
    "Sokrates “Know thyself, said Socrates.” demiştir.": "سقراط \"Know thyself, said Socrates.\" دیمشدر.",
    "ne zarar ne fayda, her an": "نه ضرر نه فائده، هر آن",
    "Hz. Muhammed (s.a.v)'in sözü": "حضرت محمّد (صلّی الله علیه وسلّم)ڭ سوزی",
    "İsa (a.s) ve Ali (r.a.) geldi.": "عیسی (علیه السلام) و علی (رضی الله عنه) كلدی.",
    "Adem'e secde edin.": "آدمه سجده ایدڭ.",
    "vardır ki öyle": "واردركه اویله",
    # imlâ turu 4: Arapça harf-i tarif ve tamlamalar
    "Kitâbü’t-Tevhîd": "كتاب التوحید",
    "Ebü’l-Hasan el-Eş’arî": "ابو الحسن الاشعری",
    "Ebû Mansûr el-Mâtürîdî": "ابو منصور الماتریدی",
    "Ehli’s-sünne": "اهل السنّه",
    "el-Bakara": "البقره",
    "et-Tevbe": "التوبه",
    "el-En‘âm": "الانعام",
    "Âl-i İmrân": "آل عمران",
    "Te’vîlâtü’l-Kur’ân": "تأویلات القرآن",
    "Muhyiddin İbnü’l-Arabî": "محیی الدین ابن العربی",
    # imlâ turu 5 (Mesnevî-i Nûriye)
    "İ’lem eyyühel-aziz!": "اعلم ایّها العزیز!",
    "Vâcib-ül Vücud": "واجب الوجود",
    "MESNEVÎ-İ NURİYE": "مثنوی نوریه",
    "zikredilen": "ذكر ایدیلن",
    "hissedilir": "حسّ ایدیلیر",
    "zannettiğin": "ظن ایتدیكڭ",
    "âhirette": "آخرتده",
    "rahmettir": "رحمتدر",
    "etmez": "ایتمز",
    "kādir": "قادر",
    "in’am": "انعام",
    "maahâza": "مع هذا",
    # imlâ turu 6 (Mesnevî-i Nûriye Osmanlıca nüshasıyla karşılaştırma)
    "hükmünde": "حكمنده", "hükmündedir": "حكمندهدر", "arkasından": "آرقهسندن", "vazifesinde": "وظیفهسنده", "sikkesini": "سكّهسنی", "birinin": "برینڭ",
    "ediyor": "ایدییور", "bakınız": "باقیڭز", "edemez": "ایده‌مز", "sayısız": "صاییسز", "yalnız": "یالڭز", "şeyi": "شیئی",
    "olarak": "اولارق", "olacak": "اولاجق", "olacaktır": "اولاجقدر", "bırakacağım": "بیراقاجغم", "görecekti": "كوره‌جكدی",
    "onun": "اونڭ", "bundan": "بوندن", "şundan": "شوندن", "onlar": "اونلر", "ona": "اوڭا", "onları": "اونلری",
    # imlâ turu 8 (Sözler Osmanlıca nüshası)
    "istiyor": "ایستهیور", "saklıyor": "صاقلایور", "görüyor": "كورویور", "okuyorlar": "اوقویورلر", "yürüyor": "یورویور",
    "istersen": "ایسترسهڭ", "nefsim": "نفسم", "anlamak": "آڭلامق", "anlıyor": "آڭلایور", "benzer": "بڭزر",
    "etmemek": "ایتمهمك", "vermeyip": "ویرمهیوب", "olmakla": "اولمقله", "yolu": "یولی", "matemhane": "ماتمخانه",
    "Allâh": "الله", "der": "دیر", "dört": "درت", "dokuz": "طقوز", "kalsın": "قالسین", "oluyor": "اولویور", "durumda": "دورومده", "kuru": "قورو",
    # imlâ turu 9 (Şuâlar Osmanlıca nüshası)
    "verir": "ویرر", "çevirir": "چویرر", "gösterir": "كوستریر", "getirir": "كتیریر", "gelir": "كلیر", "ederek": "ایدرك", "İlahiye": "الهیّه", "uzaktan": "اوزاقدن",
    "yetiştirmek": "یتیشدیرمك", "ölüm": "ئولوم", "olacağını": "اولاجغنی", "şifa": "شفا", "mahiyeti": "ماهیّتی",
    "manasıyla": "معناسیله", "meyvesi": "میوهسی", "karanlık": "قراڭلق", "içindeki": "ایچندهكی",
    # imlâ turu 10 (Emirdağ Lâhikası Osmanlıca nüshası)
    "dedim": "دیدم", "verdiler": "ویردیلر", "kalmadı": "قالمدی", "etmedi": "ایتمدی", "kurtarmaya": "قورتارمغه",
    "etsem": "ایتسهم", "olsam": "اولسهم", "bilmiyor": "بیلمییور", "işimizle": "ایشمزله", "eserlerimi": "اثرلریمی",
    "kardeşlerim": "قرداشلرم", "hizmetçi": "خدمتجی", "adliye": "عدلیه", "kişiye": "كیشی یه", "Ankara": "آنقره",
    # imlâ turu 11 (Gençlik Rehberi Osmanlıca nüshası)
    "istemez": "ایستهمز", "gelebiliyor": "كلهبیلییور", "bilemez": "بیلهمز", "gelmez": "كلمز", "düşersin": "دوشرسڭ",
    "nuruyla": "نوریله", "kızdan": "قیزدن", "kazanmak": "قزانمق", "önündeki": "اوڭندهكی", "gençlik": "كنچلك",
    "dinsizler": "دینسزلر", "yine": "یینه", "altında": "آلتنده", "kişi": "كیشی",
    # Şefkat Tokatları
    "yedim": "ییدم", "yemiş": "ییمش", "bilirim": "بیلیرم", "olabiliriz": "اولابیلیرز", "gelmesin": "كلمهسین",
    "geçirsin": "كچیرسین", "yazsın": "یازسین", "kalmıyordu": "قالمایوردی", "çavuş": "چاووش", "arkadaş": "آرقداش",
    "küçük": "كوچك", "karşı": "قارشو", "yeni": "یڭی", "üçüncü": "اوچنجی", "içinde": "ایچنده", "işte": "ایشته",
}

kalan = 0
for latin, osm in BEKLENEN.items():
    if osm is None:
        continue
    sonuc = cevir(latin)
    if sonuc.replace("\u200c", "") == osm.replace("\u200c", ""):   # ara boşluk (ZWNJ) yalnız görünüş
        print("GECTI", latin, sonuc)
    else:
        kalan += 1
        print("KALDI", latin, "beklenen", osm, "çıkan", sonuc)
from engine.transliterator import transliterate_text
for latin, osm in CUMLE.items():
    sonuc = transliterate_text(latin)
    if sonuc.replace("\u200c", "") == osm.replace("\u200c", ""):   # ara boşluk (ZWNJ) yalnız görünüş
        print("GECTI", latin, sonuc)
    else:
        kalan += 1
        print("KALDI", latin, "beklenen", osm, "çıkan", sonuc)
print("SONUC:", "HEPSI GECTI" if not kalan else f"{kalan} TEST KALDI")
sys.exit(1 if kalan else 0)
