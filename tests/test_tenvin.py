# -*- coding: utf-8 -*-
"""Arapça -en zarfları (tenvin), Hayrat'a göre. Çalıştırma: python tests/test_tenvin.py"""
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))
from engine.transliterator import transliterate_text as t


def n(s):
    return re.sub("[\u064b-\u065f\u0670\u200c]", "", s)


BEKLENEN = [
    ("zahiren", "ظاهرا"), ("esasen", "اساسا"), ("daimen", "دائما"), ("ferden", "فردا"), ("tafsilen", "تفصیلا"),
    ("acilen", "عاجلا"), ("ağleben", "اغلبا"), ("adeten", "عادتا"), ("delaleten", "دلالتا"),
    # dokunulmaması gerekenler (Türkçe ek, fiil)
    ("birden", "بردن"), ("seneden", "سنه‌دن"), ("şeyden", "شیدن"), ("yükselen", "یوكسلن"), ("ekilen", "اكیلن"),
    ("öğreten", "اوكرتن"), ("derken", "دیركن"), ("gelen", "كلن"), ("beden", "بدن"),
]
hata = 0
for latin, osm in BEKLENEN:
    c = t(latin)
    if n(c) != n(osm):
        print("HATA:", latin, "beklenen", osm, "çıkan", c)
        hata += 1
print("SONUC: HEPSI GECTI" if not hata else f"SONUC: {hata} HATA")
