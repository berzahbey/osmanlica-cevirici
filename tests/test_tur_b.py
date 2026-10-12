"""Tur B (13 Ekim): ek yazımı — ek-fiil -ken/-yse/-yiz (transliterator._ek_fiil), -dıktan, -dığınız, ile + ek ayırması, satın.
Çalıştırma: docker run --rm -v "$PWD":/k -w /k berzahbey/osmanlica-cevirici:latest python tests/test_tur_b.py"""
import logging
import os
import sys

logging.disable(50)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app"))
from engine.transliterator import transliterate_text as T  # noqa: E402

ZW = "‌"
DURUMLAR = [
    # düzelen (Hayrat)
    ("açıklasın", "آچیقلاسین"), ("kaplasın", "قاپلاسین"), ("hatırlasınlar", "خاطرلاسینلر"), ("halindeyken", "حالنده‌یكن"),
    ("beynindeyse", "بیننده‌یسه"), ("buradayız", "بوراده‌ییز"), ("seferdeyiz", "سفرده‌ییز"), ("açıkladıktan", "آچیقلادقدن"),
    ("kılındıktan", "قیلیندقدن"), ("kavuştuğunuzda", "قاووشدیغڭزده"), ("uzaklaştığınızdan", "اوزاقلاشدیغڭزدن"),
    ("olanlarız", "اولانلرز"), ("satın", "صاتین"), ("budalalar", "بودالهلر"),
    # korunan
    ("süsleyici", "سوسله‌ییجی"), ("tedâhülüyledir", "تداخلیله‌در"), ("gelirken", "كلیركن"), ("alamayız", "آلاماییز"),
    ("katmalıyız", "قاتملی ییز"), ("iken", "ایكن"), ("olursa", "اولورسه"),
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
