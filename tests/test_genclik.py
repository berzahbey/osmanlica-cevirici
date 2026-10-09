# -*- coding: utf-8 -*-
"""Gençlik Rehberi (Hayrat) karşılaştırmasında bulunan hatalar. Çalıştırma: python tests/test_genclik.py"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))
from engine.transliterator import transliterate_text as t


def n(s):
    return s.replace("\u200c", "").replace("\u0651", "").replace("\u0670", "")


BEKLENEN = [
    ("Bu da‘vâ doğrudur.", "بو دعوا طوغریدر."), ("da‘vâyı", "دعوایی"), ("tab‘", "طبع"), ("men‘", "منع"),
    ("mâni‘", "مانع"), ("nev‘in", "نوعڭ"), ("vukū‘u", "وقوعی"), ("Onu tab‘ ettiler.", "اونی طبع ایتدیلر."),
    ("iskāt", "اسقاط"), ("mahlûkāt", "مخلوقات"), ("asma", "آصما"), ("Elhamdülillâh", "الحمد لله"),
    ("binâen", "بناءً"), ("Muhammed (asm)", "محمد (علیه الصلاة والسلام)"), ("Mûsâ (as)", "موسی (علیه السلام)"),
    # dokunulmaması gerekenler
    ("el-En‘âm", "الانعام"), ("meşher-i a‘zam-ı", "مشهر اعظم"), ("Bu da doğrudur.", "بو ده طوغریدر."),
    ("dava", "دعوا"), ("Kur’an’ın", "قرآنڭ"), ("âdâtullâh", "عادات الله"), ("(s.a.v)", "(صلی الله علیه وسلم)"),
]
hata = 0
for latin, osm in BEKLENEN:
    c = t(latin)
    if n(c) != n(osm):
        print("HATA:", latin, "beklenen", osm, "çıkan", c)
        hata += 1
print("SONUC: HEPSI GECTI" if not hata else f"SONUC: {hata} HATA")
