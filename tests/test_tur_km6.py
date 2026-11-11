"""Tur KM6-7 (12 Kasım 2026, Fransız Devrimine Bakış / Şair ve Patron / Ortaçağ denetimi): Latin harf kalmaz (yabancı kelime
aslının okunuşuyla), Roma rakamı sayı, modern kelime düzeltmeleri, Hayrat ek kalıpları.
Calistirma: docker run --rm -v "$PWD":/k -w /k berzahbey/osmanlica-cevirici:latest python tests/test_tur_km6.py"""
import logging
import os
import re
import sys

logging.disable(50)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app"))
from engine.transliterator import transliterate_text as T  # noqa: E402

D = [
    # devrim ve modern kelimeler
    ("devrim", "دوریم"), ("Devrim'in", "دوریمڭ"), ("devrimcilerin", "دوریمجیلرڭ"), ("olağanüstü", "اولاغان‌اوستی"),
    ("monarşinin", "مونارشینڭ"), ("demokrasinin", "دموقراسینڭ"), ("vâlinin", "والینڭ"), ("kadının", "قادینڭ"),
    ("manastır", "مناستر"), ("teyit", "تأیید"), ("Germen", "كرمن"),
    # Hayrat ek kalıpları
    ("ulaştığımızı", "اولاشدیغمزی"), ("çalıştığı", "چالیشدیغی"), ("saptamamızın", "صاپتامه‌مزڭ"), ("etkileyici", "اتكیله‌ییجی"),
    ("paralellik", "پاراللك"), ("getirememiştir", "كتیره‌مه‌مشدر"), ("getiremedi", "كتیره‌مدی"), ("bitiremeyen", "بیتیره‌مه‌ین"),
    ("monastik", "موناستیك"), ("Helenistik", "هلنیستیك"), ("öğretmen", "اوكرتمن"),
    # Roma rakamı
    ("XIV. yüzyıl", "١٤. یوزییل"), ("IX. yüzyılda", "٩. یوزییلده"),
    # yabancı adlar: Türkçe okunuşla
    ("Robespierre'in", "روبسپیرڭ"), ("Cambridge", "كمبریچ"), ("Napoleon", "ناپولیون"), ("Marx'tan", "مارقسدن"),
    ("Constantinus", "قونستانتینوس"), ("Toscana", "طوسقانه"), ("caritas", "قاریتاس"),
    # Türkçe/Arapça kelimeye dokunulmaz
    ("Cahit", "جاهد"), ("Cum'a", "جمعه"), ("vaz‘iyette", "وضعیتده"), ("hissettirdi", "حسّ ایتدیردی"), ("Ethem", "ادهم"),
    ("on iki gün", "اون ایكی كون"), ("Ali de geldi", "علی ده كلدی"), ("Azerbeycan", "آذربایجان"),
]
LATINSIZ = ["The French Revolution, Cambridge, 1989.", "G. Lefebvre, Etudes sur la Revolution française, Paris 1954.",
            "Geschichte der Französischen Revolution von 1789 bis 1814", "D'Harcourt", "Collected Works, cilt 38",
            "Ecole des Hautes Etudes en Science Sociales", "Earliest Worldly Baltimore"]


def main():
    kalan = 0
    for a, b in D:
        c = T(a).strip()
        if c != b:
            kalan += 1
            print("KALDI", a, "->", c, "(beklenen", b + ")")
    for a in LATINSIZ:
        c = T(a)
        if re.search("[A-Za-zÀ-ÿ]", c):
            kalan += 1
            print("KALDI Latin harf kaldi:", a, "->", c)
    print("SONUC:", "HEPSI GECTI" if not kalan else f"{kalan} TEST KALDI")


main()
