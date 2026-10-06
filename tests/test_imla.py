"""Osmanlıca imlâ gerileme testi (k/g harfleri, Arapça/Farsça kelimelerin aslî yazımı, tırnak ekleri, yabancı dil). Kod klasöründe:
  docker run --rm -v "$PWD":/k -w /k berzahbey/osmanlica-cevirici:latest python tests/test_imla.py"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app"))
from engine.transliterator import draft_transliterate_sentence as cevir

BEKLENEN = {
    # Türkçe kelime, sözlükteki başka kelimeyle çakışıyordu
    "iki": "ایكی", "ikinci": "ایكنجی", "ikisi": "ایكیسی", "bak": "باق", "bakmak": "باقمق", "kuşkusuz": "قوشقوسز",
    "Hak'dan": "حقّدن", "kez": "كز", "ergen": "ارگن",
    # sözlükteki asıl (şapkalı) kelimeler korunur
    "bâk": "باك", "köşk": "كوشك", "hâkdan": "خاكدان",
    # kural motoru: k/g yanındaki ünlüye göre (kalın: ق غ, ince: ك گ)
    "bugün": "بوگون", "herhangi": "هرهانگی", "çıkabilir": "چیقابیلیر", "gidiyor": "گیدییور", "dergâh": "درگاه",
    # g sesi gaf, k sesi kef (sözlük düzeltmesi)
    "hângâh": "خانگاه", "tengdil": None, "kedûret": "كدورت", "mürekkib": "مركّب",
    # Arapça/Farsça kelimeler aslî imlâsıyla
    "Mustafa": "مصطفی", "yani": "یعنی", "fiil": "فعل", "fiilleri": "فعللری", "mümkün": "ممكن", "maksat": "مقصد",
    "galip": "غالب", "istidat": "استعداد", "tesir": "تأثیر", "cevap": "جواب", "talep": "طلب", "heyet": "هیئت",
    "miktar": "مقدار", "mükâşefe": "مكاشفه", "mükaşefe": "مكاشفه", "takip": "تعقیب", "Hz": "حضرت",
    # değişmemesi gerekenler
    "günah": "گناه", "kitap": "كتاب", "zevk": "ذوق", "teşvik": "تشویق", "kâr": "كار", "kâğıt": "كاغد",
    "gelmek": "گلمك", "gece": "گیجه", "değil": "دگل", "doğru": "طوغری", "yirmi": "یگرمی", "bir": "بر",
    "karargâh": "قرارگاه", "tebliğ": "تبلیغ", "Kur'an": "قرآن", "Allah": "الله", "evet": "اوت", "yap": "یاپ",
    # imlâ turu 2: sözlük denetleyicisinin bulduğu bozuk kayıtlar
    "mal": "مال", "malları": "ماللری", "dakika": "دقیقه", "mahlukat": "مخلوقات", "vehm": "وهم", "kabr": "قبر",
    "felsefe": "فلسفه", "irşad": "ارشاد", "oysa": "اویسه", "celal": "جلال", "zemin": "زمین", "elif": "الف",
    "Hakk'a": "حقّه", "Rabb'e": "ربّه", "Âdem'i": "آدمی", "nev'i": "نوع", "O'nun": "اونڭ", "Kur'an'ın": "قرآنڭ",
    "Ali'lerdir": "علیلردر",
    # Türkçe fiillerin tarihî yazımı, kelime başında medli elif
    "ettiği": "ایتدیگی", "edilmiştir": "ایدیلمشدر", "verdiği": "ویردیگی", "demiştir": "دیمشدر", "dediğimiz": "دیدیگمز",
    "anlam": "آنلام", "açık": "آچیق", "almak": "آلمق",
    # sık kelimeler ve özel adlar
    "nitekim": "نته‌كیم", "buna": "بوڭا", "birşey": "بر شی", "Ali": "علی", "Hasan": "حسن", "Mısır": "مصر",
    # derin ek ayırma (Arapça kök + iyelik/hâl ekleri)
    "âyetlerimizi": "آیتلرمزی", "kalbiniz": "قلبڭز", "şeklindeki": "شكلندكی",
    # imlâ turu 3: OpenITI sıklık listesiyle gözden geçirilen kelimeler
    "tevilat": "تأویلات", "istidadı": "استعدادی", "münezzehtir": "منزّهدر", "rububiyet": "ربوبیت", "muvahhid": "موحّد",
    "mübiyn": "مبین", "risalet": "رسالت", "bizzat": "بالذّات",
}

# Cümle düzeyi (tırnak, yabancı dil, "Hak Teâlâ")
CUMLE = {
    "Hak Teâlâ buyurdu.": "حقّ تعالی بویوردی.",
    "“O”dur.": "“او”در.",
    "“Hak”tan geldi.": "“حقّ”دن گلدی.",
    "Bkz. Essai de Chronologie des oeuvres de al-Ghazali, Paris 1959.":
        "بقز. Essai de Chronologie des oeuvres de al-Ghazali, Paris 1959.",
    "Sokrates “Know thyself, said Socrates.” demiştir.": "سقراط “Know thyself, said Socrates.” دیمشدر.",
    "ne zarar ne fayda, her an": "نه ضرر نه فایده، هر آن",
    "Hz. Muhammed (s.a.v)'in sözü": "حضرت محمّد (صلّی الله علیه وسلّم)ڭ سوزی",
    "İsa (a.s) ve Ali (r.a.) geldi.": "عیسی (علیه السلام) و علی (رضی الله عنه) گلدی.",
    "Adem'e secde edin.": "آدمه سجده ایدیڭ.",
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
    "zannettiğin": "ظنّ ایتدیگڭ",
    "âhirette": "آخرتده",
    "rahmettir": "رحمتدر",
    "etmez": "ایتمز",
    "kādir": "قادر",
    "in’am": "انعام",
    "maahâza": "مع هذا",
    # imlâ turu 6 (Mesnevî-i Nûriye Osmanlıca nüshasıyla karşılaştırma)
    "hükmünde": "حكمنده", "hükmündedir": "حكمندهدر", "arkasından": "آرقهسندن", "vazifesinde": "وظیفهسنده", "sikkesini": "سكّهسنی", "birinin": "برینڭ",
    "ediyor": "ایدییور", "bakınız": "باقیڭز", "edemez": "ایده‌مز", "sayısız": "صاییسز", "yalnız": "یالڭز", "şeyi": "شیئی",
    "olarak": "اولارق", "olacak": "اولاجق", "olacaktır": "اولاجقدر", "bırakacağım": "بیراقاجغم", "görecekti": "گوره‌جكدی",
    "onun": "اونڭ", "bundan": "بوندن", "şundan": "شوندن", "onlar": "اونلر", "ona": "اوڭا", "onları": "اونلری",
    "küçük": "كوچك", "karşı": "قارشو", "yeni": "یڭی", "üçüncü": "اوچنجی", "içinde": "ایچنده", "işte": "ایشته",
}

kalan = 0
for latin, osm in BEKLENEN.items():
    if osm is None:
        continue
    sonuc = cevir(latin)
    if sonuc == osm:
        print("GECTI", latin, sonuc)
    else:
        kalan += 1
        print("KALDI", latin, "beklenen", osm, "çıkan", sonuc)
from engine.transliterator import transliterate_text
for latin, osm in CUMLE.items():
    sonuc = transliterate_text(latin, use_ollama_refine=False)
    if sonuc == osm:
        print("GECTI", latin, sonuc)
    else:
        kalan += 1
        print("KALDI", latin, "beklenen", osm, "çıkan", sonuc)
print("SONUC:", "HEPSI GECTI" if not kalan else f"{kalan} TEST KALDI")
sys.exit(1 if kalan else 0)
