"""Tur KY (23 Kasım 2026, İdeal Devlet denetimi): ad + 'yi ayrı; varolmak ayrı; şapkasız Arapça kök + etmek ayrı; mahsûs محسوس."""
import os, sys, pathlib
os.environ.setdefault("YZ_SOZLUK", "/yok")
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "app"))
from engine.transliterator import transliterate_text as tt

ister = {"Farabî’yi": "فارابی یی", "Efendi’yi": "افندی یی", "varolması": "وار اولمسی", "varolanın": "وار اولانڭ",
         "ifsadetmesi": "افساد ایتمسی", "mahsûsler": "محسوسلر", "mahsus": "مخصوص", "hazretsiz": "حضرتسز", "kontrol": "قونترول"}
for s, o in ister.items():
    c = tt(s)
    assert c == o, (s, c, o)
print("SONUC: HEPSI GECTI")
