"""Tur D (14 Ekim): Bakara okuma listesinden — ünlü he bitişmez (ZWNJ), ek ortasında fazla elif (-lar-, -acak-, -mış-, -sa+lar), -nız + ek,
mastar + -nız, yalın fiil kökü (vur), -yenden, istek -esiniz, kök sözlüğüne -yıp kanıtıyla giren fiiller (harca-). "korunan"lar bozulmamalı.
Çalıştırma: docker run --rm -v "$PWD":/k -w /k berzahbey/osmanlica-cevirici:latest python tests/test_tur_d.py"""
import logging
import os
import sys

logging.disable(50)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app"))
from engine.transliterator import transliterate_text as T  # noqa: E402

ZW = "‌"
DURUMLAR = [
    ("sınırlarıdır", "صینیرلریدر"), ("bozguncuların", "بوزغونجیلرڭ"), ("harcayacaklarını", "خرجایاجقلرینی"), ("olacağın", "اولاجغڭ"),
    ("sarsılmışlardı", "صارصیلمشلردی"), ("hepinizi", "هپڭزی"), ("erkeklerinizden", "ارككلریڭزدن"), ("düzeltmenize", "دوزلتمه‌ڭزه"),
    ("düşmemeniz", "دوشمه‌مه‌ڭز"), ("almanızı", "آلمه‌ڭزی"), ("dursalardı", "طورسه‌لردی"), ("harcarsanız", "خرجارسه‌ڭز"), ("vur", "اور"),
    ("gizleyenden", "كیزله‌یندن"), ("düşünesiniz", "دوشونه‌سڭز"), ("yapmayacaklardı", "یاپمایاجقلردی"), ("dururlarken", "طورورلركن"),
    # korunan
    ("başlarsa", "باشلارسه"), ("kılarız", "قیلارز"), ("bacakları", "باجاقلری"), ("bacağına", "باجاغنه"), ("basılarak", "باصیلارق"),
    ("komünizme", "قومونیزمه"), ("olanlarız", "اولانلرز"), ("hepiniz", "هپڭز"), ("kasaları", "قاصه‌لری"), ("Allah'ın", "اللّهڭ"),
    ("fıkhı", "فقهی"), ("günahlarınızdan", "كناهلریڭزدن"), ("şehirde", "شهرده"),
    ("eleştirmek", "الشدیرمك"), ("duyumlanan", "دویوملانان"), ("duyarlı", "دویارلی"), ("arayıp", "آرایوب"), ("gayene", "غایه‌نه"),
    ("boynuzdur", "بوینوزدر"), ("benizleri", "بنیزلری"),
]
# ünlü he + harf: ZWNJ olmalı; ünsüz h: olmamalı
ZWNJ = [("tövbeleri", "توبه‌لری"), ("kıblesine", "قبله‌سنه"), ("sadakadan", "صدقه‌دن"), ("bağışlaması", "باغیشلامه‌سی"),
        ("istiyorlardı", "ایسته‌یور"), ("şüphedeyseniz", "شبهه‌ده")]
ZWNJ_YOK = [("günahlarınızdan", "كناهلر"), ("fıkhı", "فقهی"), ("şehirde", "شهرده"), ("mühürlemiştir", "مهرله")]


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
