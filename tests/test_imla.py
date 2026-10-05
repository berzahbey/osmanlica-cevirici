"""Osmanlıca imlâ gerileme testi (k/g harfleri, Arapça/Farsça kelimelerin aslî yazımı). Kod klasöründe:
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
    "bugün": "بوگون", "herhangi": "هرهانگی", "çıkabilir": "چیقابیلیر", "gidiyor": "گیدیور", "dergâh": "درگاه",
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
print("SONUC:", "HEPSI GECTI" if not kalan else f"{kalan} TEST KALDI")
sys.exit(1 if kalan else 0)
