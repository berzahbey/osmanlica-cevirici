"""Tur EL (23 Kasım 2026, İdeal Devlet künyesi): tiresiz "El X" ve "X-ü'l Y" Arapça tarif olarak okunur; Türkçe "El ele" dokunulmaz."""
import os, sys, pathlib
os.environ.setdefault("YZ_SOZLUK", "/yok")
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "app"))
from engine.transliterator import transliterate_text as tt

ister = {"İdeal Devlet (El Medinetü'l Fazıla)": "(المدینت الفاضله)", "Ehli'l Beyt": "اهل البیت", "Dâru'l Harb": "دار الحرب",
         "El Kanun": "القانون", "El ele verdiler.": "ال اله"}
for s, o in ister.items():
    c = tt(s)
    assert o in c, (s, c, o)
print("SONUC: HEPSI GECTI")
