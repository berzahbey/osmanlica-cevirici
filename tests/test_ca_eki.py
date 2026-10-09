# -*- coding: utf-8 -*-
"""-ca/-ce eki (Hayrat'a göre جه). Çalıştırma: python tests/test_ca_eki.py"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))
from engine.transliterator import transliterate_text as t

ZW = "\u200c"
BEKLENEN = [
    ("Osmanlıca", "عثمانلیجه"), ("Osmanlıcası", "عثمانلیجه‌سی"), ("Osmanlıcaya", "عثمانلیجه‌یه"),
    ("Osmanlıcadan", "عثمانلیجه‌دن"), ("Osmanlıcanın", "عثمانلیجه‌نڭ"),
    ("hakça", "حقجه"), ("devletçe", "دولتجه"), ("adaletçe", "عدالتجه"), ("sabırca", "صبرجه"),
    ("hükümetçe", "حكومتجه"),
    ("ailece", "عائله‌جه"), ("yapışırcasına", "یاپیشیرجه‌سنه"),
    # dokunulmaması gerekenler (Hayrat'taki kelimeler, Türkçe kökler)
    ("Türkçe", "توركجه"), ("insanca", "انسانجه"), ("bahçe", "باغچه"), ("derecesi", "درجه‌سی"),
    ("tarihçe", "تاریخچه"), ("ilmince", "علمنجه"), ("hükmünce", "حكمنجه"), ("Osmanlı", "عثمانلی"),
    ("aldıkça", "آلدقجه"), ("görünce", "كورنجه"),
]
hata = 0
for latin, osm in BEKLENEN:
    c = t(latin)
    if c.replace(ZW, "").replace("\u0651", "") != osm.replace(ZW, "").replace("\u0651", ""):
        print("HATA:", latin, "beklenen", osm, "çıkan", c)
        hata += 1
print("SONUC: HEPSI GECTI" if not hata else f"SONUC: {hata} HATA")
