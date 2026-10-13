"""Tur C (13 Ekim): bileşik fiil (et-/ol-), emir -ın ڭ, ek yazımı kalanları (-ki + ek, -nız + hâl, geniş zaman -ar, isim + -ız),
-deki'de ZWNJ, bağlam (kadir, tan). Hayrat'a göre beklenen yazımlar; "korunan"lar eskiden doğru olup bozulmaması gerekenler.
Çalıştırma: docker run --rm -v "$PWD":/k -w /k berzahbey/osmanlica-cevirici:latest python tests/test_tur_c.py"""
import logging
import os
import sys

logging.disable(50)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app"))
from engine.transliterator import transliterate_text as T  # noqa: E402

ZW = "‌"
DURUMLAR = [
    # düzelen: emir -ın (Hayrat girin كیرڭ)
    ("inin", "اینڭ"), ("uyun", "اویڭ"), ("faydalanın", "فائده‌لانڭ"),
    # ek yazımı
    ("elçinizi", "ایلچیڭزی"), ("yıla", "ییله"), ("önlerindekini", "اوڭلرنده‌كینی"), ("yanlarındakini", "یانلرنده‌كینی"),
    ("kılarsa", "قیلارسه"), ("anlarsa", "آڭلارسه"), ("orduyla", "اوردویله"), ("arzuyla", "آرزویله"), ("korkutur", "قورقوتور"),
    ("rızıklandır", "رزقلاندیر"), ("akdine", "عقدینه"), ("aitiz", "عائدز"), ("muhtacız", "محتاجز"), ("ölçülmek", "اولچولمك"),
    # bileşik fiil
    ("ümmetti", "امّتدی"), ("demedikçe", "دیمه‌دكجه"), ("hacceder", "حجّ ایدر"), ("kastetti", "قصد ایتدی"),
    ("emrolunduğunuz", "امر اولوندیغڭز"), ("arzolunur", "عرض اولونور"), ("mahvolur", "محو اولور"), ("zikredecek", "ذكر ایده‌جك"),
    # korunan
    ("zulmederim", "ظلم ایدرم"), ("reddederim", "رد ایدرم"), ("zulmetti", "ظلم ایتدی"), ("hükmetti", "حكم ایتدی"),
    ("halkeden", "خلق ایدن"), ("tepeden", "تپه‌دن"), ("evinde", "اونده"), ("demir", "دمیر"), ("kapısında", "قاپوسنده"),
    ("yüzünde", "یوزنده"), ("büyüdür", "بویودر"), ("irin", "ایرین"), ("muhtaçlarız", "محتاجلرز"), ("okursak", "اوقورسه‌ق"),
    ("adâletinizden", "عدالتڭزدن"), ("oğlunuzu", "اوغلڭزی"), ("almanızı", "آلمه‌ڭزی"), ("kuvvetiyle", "قوّتیله"),
    ("yoluyla", "یولیله"), ("şevketti", "شوق ایتدی"), ("hitabetti", "خطاب ایتدی"), ("gözettiniz", "كوزتدیڭز"), ("Asın", "آصین"), ("girin", "كیرڭ"), ("bakın", "باقڭ"), ("başlarız", "باشلارز"), ("olanlarız", "اولانلرز"),
    # cümle (bağlam kuralları)
    ("Allah her şeye kadir.", "الله هر شیئه قادر."), ("O buna kadir olandır.", "او بوڭا قادر اولاندر."),
    ("Kadir gecesi", "قدر كیجه‌سی"), ("kadir ve kıymet", "قدر و قیمت"), ("Tan yeri ağarıncaya kadar", "طاڭ یری آغارینجهیه قدر"),
    ("Allah'tan korkun", "اللّهدن قورقڭ"),
]
# -deki ve kök sözlüğündeki bitişmez he: ZWNJ olmalı (eskiden دهكی / یاقهلا bitişik basılıyordu)
ZWNJ = [("önlerindekini", "ده‌كی"), ("evindeki", "اونده‌كی"), ("kabirlerdekiler", "ده‌كیلر"), ("yakalarız", "یاقه‌لا"),
        ("gelecek", "كله‌جك"), ("kastediyorsanız", "سه‌ڭز")]
# ünsüz he (Allah, padişah) ZWNJ almaz
ZWNJ_YOK = [("Allah'ın", "اللّهڭ"), ("padişahın", "هڭ")]


def main():
    kalan = 0
    for w, beklenen in DURUMLAR:
        c = T(w).strip()
        if c.replace(ZW, "") != beklenen.replace(ZW, ""):
            kalan += 1
            print(f"KALDI {w} -> {c} (beklenen {beklenen})")
    for w, parca in ZWNJ:
        c = T(w).strip()
        if parca not in c:
            kalan += 1
            print(f"KALDI (ZWNJ) {w} -> {c!r} (içermeli {parca!r})")
    for w, parca in ZWNJ_YOK:
        c = T(w).strip()
        if parca not in c:
            kalan += 1
            print(f"KALDI (ZWNJ yok) {w} -> {c!r} (içermeli {parca!r})")
    print("SONUC: HEPSI GECTI" if not kalan else f"SONUC: {kalan} TEST KALDI")


if __name__ == "__main__":
    main()
