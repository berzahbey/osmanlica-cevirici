# -*- coding: utf-8 -*-
"""Arapça dişil sıfat izafetten sonra (Hayrat). Çalıştırma: python tests/test_disil.py"""
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))
from engine.transliterator import transliterate_text as t


def n(s):
    return re.sub("[\u064b-\u065f\u0670\u200c\u0654]", "", s).replace("\u06d5", "\u0647")


BEKLENEN = [
    ("nübüvvet-i mutlaka", "نبوت مطلقه"), ("nübüvvet-i mutlakanın", "نبوت مطلقهنڭ"), ("ulûm-u âdiye", "علوم عادیه"),
    ("suver-i müteaddidede", "صور متعددهده"), ("hakāik-i esâsiyesi", "حقائق اساسیهسی"),
    ("kavânîn-i amîka-i dakîka-i İlâhiyyeyi", "قوانین عمیقه دقیقه الهیهیی"),
    # dokunulmaması gerekenler
    ("nev‘-i insanın", "نوع انسانڭ"), ("şerîat-ı garrâ", "شریعت غرا"), ("bahr-i semâda", "بحر سماده"),
    ("Adem-i sırfa", "عدم صرفه"), ("Risâle-i Nûr", "رساله نور"), ("mutlaka gelir", "مطلقا كلیر"), ("kuvve-i vâhimenin", None),
]
hata = 0
for latin, osm in BEKLENEN:
    c = t(latin)
    if osm is None:
        if "\u0648\u062e\u06cc\u0645" in c:
            print("HATA:", latin, "vâhime vahîme olmamalı:", c); hata += 1
        continue
    if n(c) != n(osm):
        print("HATA:", latin, "beklenen", osm, "çıkan", c)
        hata += 1
print("SONUC: HEPSI GECTI" if not hata else f"SONUC: {hata} HATA")
