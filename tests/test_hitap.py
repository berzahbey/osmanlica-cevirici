# -*- coding: utf-8 -*-
"""Senin/onun ve düz dua kısaltmaları. Çalıştırma: python tests/test_hitap.py"""
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))
from engine.transliterator import transliterate_text as t


def n(s):
    return re.sub("[\u064b-\u065f\u0670\u200c]", "", s).replace("\u06d5", "\u0647")


BEKLENEN = [
    ("Senin şuûrun varsa kalbini yakıyor.", "سنڭ شعورڭ وارسه قلبنی یاقییور."),     # "şuûrun" araya girer: onun değil, kural uygulanmaz
    ("senin başına", "سنڭ باشڭه"), ("senin huzûrunda", "سنڭ حضورڭده"), ("senin o nihâyetsiz adâletini", "سنڭ او نهایتسز عدالتڭی"),
    ("senin elini", "سنڭ الڭی"),
    ("Âhiret, senin için ilkinden daha hayırlıdır.", "آخرت، سنڭ ایچون ایلكندن داها خیرلیدر."),
    # dokunulmaması gerekenler
    ("onun başına", "اونڭ باشنه"), ("kalbini yakıyor", "قلبنی یاقییور"), ("senin dalâletin sûretiyle ölümlerin elemlerini", None),
    ("Muhammed’in asm fermânı", None), ("Hazret-i Ali ra dedi", None), ("İmâm-ı Gazâlî’nin ra", None), ("şunu as", None),
    ("Hazret-i Ömer’in", "حضرت عمرڭ"),
]
hata = 0
for latin, osm in BEKLENEN:
    c = t(latin)
    if osm is None:
        if latin.endswith("elemlerini") and "\u0627\u0644\u0645\u0644\u0631\u06cc\u0646\u06cc" not in n(c):
            print("HATA:", latin, "elemlerini 3. kişi kalmalı, çıkan", c); hata += 1
        if "asm" in latin and "علیه الصلاة والسلام" not in c:
            print("HATA:", latin, "asm açılmadı:", c); hata += 1
        if " ra" in latin and "رضی الله عنه" not in c:
            print("HATA:", latin, "ra açılmadı:", c); hata += 1
        if latin == "şunu as" and "علیه" in c:
            print("HATA:", latin, "as açılmamalı:", c); hata += 1
        continue
    if n(c) != n(osm):
        print("HATA:", latin, "beklenen", osm, "çıkan", c)
        hata += 1
print("SONUC: HEPSI GECTI" if not hata else f"SONUC: {hata} HATA")
