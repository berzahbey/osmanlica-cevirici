"""Tur W (2 Kasım 2026): sözlükte olmayan Arapça görünümlü kelime OpenITI sıklık listesindeki yazımla (engine/openiti.py).
Korumalar: Türkçe/yabancı kelime, bağlama bağlı kelime (havâs), -iye/-iyet, uzun ünlü, baştan elif/ayın, kısa kök.
Calistirma: docker run --rm -v "$PWD":/k -w /k berzahbey/osmanlica-cevirici:latest python tests/test_tur_w.py"""
import logging
import os
import sys

logging.disable(50)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app"))
from engine.transliterator import transliterate_text as T  # noqa: E402

DOGRU = [("nübüvve", "نبوه"), ("kayyım", "قیم"), ("musannef", "مصنف"), ("Suyûtî", "سیوطی"), ("Mevâhib", "مواهب"),
         ("mübhem", "مبهم"), ("kaziyeyi", "قضیه‌یی"), ("mevsûle", "موصوله"), ("Zürkânî", "زرقانی"),
         ("musannefinde", "مصنفنده"), ("müstakarrı", "مستقری"), ("neyyir", "نیر")]
DOKUNMA = ["diyalog", "vida", "yüzyıllar", "ummadıkları", "elma", "havâs", "daß", "saadet-âverdir", "haşmet-nümâ"]


def main():
    kalan = 0
    for latin, beklenen in DOGRU:
        c = T(latin).strip()
        if c != beklenen:
            kalan += 1
            print("KALDI", latin, "->", c, "(beklenen", beklenen + ")")
    os.environ["OSM_TUR_W"] = "0"
    eski = {w: T(w).strip() for w in DOKUNMA}
    os.environ["OSM_TUR_W"] = "1"
    for w in DOKUNMA:
        c = T(w).strip()
        if c != eski[w]:
            kalan += 1
            print("KALDI (dokunulmamalı)", w, "->", c, "(önce", eski[w] + ")")
    print("SONUC:", "HEPSI GECTI" if not kalan else f"{kalan} TEST KALDI")


main()
