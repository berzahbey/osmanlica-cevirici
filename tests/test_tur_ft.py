"""Tur FT (22 Kasım 2026): Arapça/Farsça isim + -la/-laş/-lan fiili sözlük yazımıyla; Türkçe kelimeye dokunulmaz."""
import os, sys, pathlib
os.environ.setdefault("YZ_SOZLUK", "/yok")
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "app"))
from engine.transliterator import transliterate_text as tt

ister = {"silahlandılar": "سلاحلاندیلر", "sanayileşmiş": "صنایعلشمش", "Yahudileşmiş": "یهودیلشمش", "yağmaladılar": "یغمالادیلر",
         "vedalaştık": "وداعلاشدق", "umumileşmesi": "عمومیلشمسی", "tamamlandı": "تماملاندی",
         # Türkçe kelimeler değişmez
         "kanıtladı": "قانیتلادی", "isteklendirmek": "ایسته", "daralan": "طارالان", "dinlemek": "دیڭله", "ısmarladı": "ایصمارلادی",
         "yakalandı": "یاقه‌لاندی", "karşılaştı": "قارشیلاشدی"}
for s, o in ister.items():
    c = tt(s)
    assert o in c, (s, c, o)
print("SONUC: HEPSI GECTI")
