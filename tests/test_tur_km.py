"""Tur KM (11 Kasım 2026, Hayrat Kur'an meali karşılaştırması, Bakara 6-83): Hayrat meali Osmanlıca baskısıyla Latin baskısı
karşılaştırıldı; çeviricinin kitaptan ayrıldığı ve Hayrat Risale verisiyle de doğrulanan yazımlar.
Calistirma: docker run --rm -v "$PWD":/k -w /k berzahbey/osmanlica-cevirici:latest python tests/test_tur_km.py"""
import logging
import os
import sys

logging.disable(50)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app"))
from engine.transliterator import transliterate_text as T  # noqa: E402

D = [
    # 1) yeterlik olumsuz + gelecek/-erek (ince): kitap بیله‌میه‌جكڭز، Hayrat göremeyeceğim كوره‌میه‌جگم، erdiremeyerek
    ("bilemeyeceğiniz", "بیله‌میه‌جكڭز"), ("göremeyecek", "كوره‌میه‌جك"), ("gelemeyecek", "كله‌میه‌جك"),
    ("bilemeyerek", "بیله‌میه‌رك"), ("ödeyemeyeceği", "اوده‌یه‌مه‌یه‌جكی"), ("yapamayacak", "یاپامایاجق"),
    ("bilmeyecek", "بیلمه‌یه‌جك"),
    # 2) ettirgen + edilgen: Hayrat دیریل (133'e 7): kitap döndürüleceksiniz دوندیریله‌جكسڭز
    ("döndürüleceksiniz", "دوندیریله‌جكسڭز"), ("döndürülür", "دوندیریلیر"), ("güldürüldü", "كولدیریلدی"),
    ("gördürülüyor", "كوردیریلییور"), ("öldürülecek", "ئولدیریله‌جك"), ("sürülür", "سورولور"),
    # 3) ط ile başlayan kalın kelimede içteki s -> س (Hayrat taslamamıştır طاسلامامشدر، doksan طقسان)
    ("tasladı", "طاسلادی"), ("taslamak", "طاسلامق"), ("basmak", "باصمق"), ("tastamam", "طاصتامام"),
    # 4) Arapça kök + etmek: -edip ve yalnız Hayrat birleşik fiillerinde geçen kök (lütf)
    ("kasdedip", "قصد ایدوب"), ("lütfettiği", "لطف ایتدیكی"), ("lütfeder", "لطف ایدر"), ("affedip", "عفو ایدوب"),
    ("edip", "ایدوب"), ("kaybetmişlerdir", "غیب ایتمشلردر"),
    # 5) erdir- (Hayrat erdiremeyerek ایردیره‌میه‌رك) ve açıkla- fiil kökleri (kok_elle.tsv)
    ("erdirir", "ایردیرر"), ("erdirmez", "ایردیرمز"), ("açıklarsanız", "آچیقلارسه‌ڭز"), ("açıkladı", "آچیقلادی"),
    # 6) parantezle ayrılmış ilgi eki (Tur ek parçası kararı gibi (ڭ)
    ("onları(n ayaklarını)", "اونلری(ڭ آیاقلرینی)"),
    # 7) Bakara 84-105 testi: pınar (Hayrat pınarlar پیڭارلر)، ard arda، idiyseniz، Arapça kök + ettikleri، ince olumsuz emir
    ("pınar", "پیڭار"), ("ard arda", "آرد آرده"), ("idiyseniz", "ایدیسه‌ڭز"),
    ("emrettiklerimizi", "امر ایتدكلریمزی"), ("demeyin", "دیمه‌یڭ"), ("gelmeyin", "كلمه‌یڭ"), ("söylemeyin", "سویله‌مه‌یڭ"),
    ("demeyiniz", "دیمه‌ییڭز"), ("etmeyin", "ایتمه‌یڭ"), ("yapmayın", "یاپمایڭ"),
    # 8) Nahl 1-42 testi (kitap + Hayrat: sabahleyin صباحلین، atalara آتالره، ermelerini ایرمه‌لرینی، itâatkârâne، diriltilecektir)
    ("akşamleyin", "آقشاملین"), ("itâatkâr", "اطاعتكار"), ("atalarımız", "آتالریمز"), ("ataların", "آتالرڭ"), ("ata", "آته"),
    ("ermelerine", "ایرمه‌لرینه"), ("erler", "ارلر"), ("yiyesiniz", "ییه‌سڭز"), ("saptırdıkları", "صاپدیردقلری"),
    ("kuşatıverdi", "قوشاتیویردی"), ("onda yara yara giden", "اونده یارا یارا كیدن"), ("yara", "یاره"),
    ("diriltileceklerini", "دیریلتیله‌جكلرینی"), ("öldürülecekleri", "ئولدیریله‌جكلری"), ("yapılacakları", "یاپیلاجقلری"),
]


def main():
    kalan = 0
    for a, b in D:
        c = T(a).strip()
        if c != b:
            kalan += 1
            print("KALDI", a, "->", c, "(beklenen", b + ")")
    print("SONUC:", "HEPSI GECTI" if not kalan else f"{kalan} TEST KALDI")


main()
