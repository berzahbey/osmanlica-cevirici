"""Tur ÇY (25 Kasım 2026, Zahir kararı): Hayrat'ın aynı kelimeyi iki türlü yazdığı, kurala dayanmayan ikiliklerde kurala uyan yazım.
Kurala dayanan ikilikler (senin/onun ڭ/ن, yedi/ye-di, arz ارض/عرض) değişmez."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.environ.setdefault("YZ_SOZLUK", "/yok")
from app.engine.transliterator import transliterate_text as T
B = []
def ok(a, b):
    c = T(a); B.append(c == b); print(("GECTI " if c == b else "KALDI ") + f"{a} -> {c}" + ("" if c == b else f"  (beklenen {b})"))
for lat, osm in [("kezâlik", "كذلك"), ("takvâ", "تقوی"), ("takvâsı", "تقواسی"), ("menşei", "منشئی"), ("numara", "نومره"),
                 ("numarası", "نومره‌سی"), ("İlâhiye", "الهیّه"), ("İlâhiyenin", "الهیّه‌نڭ"), ("mâhiyeti", "ماهیّتی"), ("hediye", "هدیّه"),
                 ("rubûbiyet", "ربوبیّت"), ("terbiye", "تربیه"), ("âliye", "عالیه"), ("tavsiye", "توصیه"),
                 # dokunulmayanlar (Hayrat kelime düzeyinde tutarlı)
                 ("dokuz", "طقوز"), ("Rahmân", "رحمان"), ("olması", "اولمسی"), ("yedi", "یدی")]:
    ok(lat, osm)
print("SONUC:", "HEPSI GECTI" if all(B) else f"{B.count(False)} KALDI")
sys.exit(0 if all(B) else 1)
