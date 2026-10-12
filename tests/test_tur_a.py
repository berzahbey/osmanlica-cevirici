"""Tur A (13 Ekim): sözlük kayıtları (duzeltmeler.tsv, data/sozluk_cikar.txt), Arapça/Farsça isim + -la/-lan/-landır fiil kökü (kok._turev),
ile + başka ek ayırması yok (dictionary.lookup_with_suffix), Arapça kelimede -abil- ek değil (kabile).
Çalıştırma: docker run --rm -v "$PWD":/k -w /k berzahbey/osmanlica-cevirici:latest python tests/test_tur_a.py"""
import logging
import os
import sys

logging.disable(50)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app"))
from engine.transliterator import transliterate_text as T  # noqa: E402

ZW = "‌"
DURUMLAR = [
    # düzelen
    ("katil", "قاتل"), ("hilal", "هلال"), ("kabile", "قبیله"), ("ilaha", "الهه"), ("tespih", "تسبیح"), ("mehir", "مهر"),
    ("usul", "اصول"), ("katından", "قاتندن"), ("hamda", "حمده"), ("kısar", "قیصار"), ("lanetledi", "لعنتله‌دی"),
    ("hoşlanmadığınız", "خوشلانمدیغڭز"), ("hatırladılar", "خاطرلادیلر"), ("hafifleştirmek", "خفیفلشدیرمك"),
    ("hayatlandırmak", "حیاتلاندیرمق"), ("feyizlendirmek", "فیضلندیرمك"), ("fâidelendiren", "فائده‌لندیرن"),
    # korunan
    ("gelebilir", "كله‌بیلیر"), ("yapabilir", "یاپابیلیر"), ("tedâhülüyledir", "تداخلیله‌در"), ("katl", "قتل"),
    ("ehemmiyetleştirir", "اهمّیتلشدیرر"), ("zıplasa", "زیپلاسه"), ("hilâl", "هلال"), ("dinlendiriniz", "دیڭلندیریڭز"), ("ısmarladık", "ایصمارلادق"), ("süsleyici", "سوسله‌ییجی"),
]


def main():
    kalan = 0
    for w, beklenen in DURUMLAR:
        c = T(w).strip()
        if c.replace(ZW, "") != beklenen.replace(ZW, ""):
            kalan += 1
            print(f"KALDI {w} -> {c} (beklenen {beklenen})")
    print(f"{len(DURUMLAR)} durum")
    print("SONUC: HEPSI GECTI" if not kalan else f"SONUC: {kalan} TEST KALDI")


if __name__ == "__main__":
    main()
