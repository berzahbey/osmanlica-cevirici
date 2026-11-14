"""Tur IY: -iye Arapça nisbe müennesi. Farsça tamlamanın sıfatında (X-i Y-iye) عربیه، فعلیه (Hayrat yazımı); tek başına yönelme
hâli dokunulmaz (Arabiye gitti عربی یه، veliye ولی یه)."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "app"))
from engine.transliterator import transliterate_text as tt

ister = {"belâgat-i Arabiyenin": "عربیه‌نڭ", "cümle-i fi‘liye": "فعلیه", "kavâid-i külliyeden": "كلّیه‌دن",
         "umûr-u i‘tibâriyeden": "اعتباریه‌دن", "sene-i arabiyeyi": "عربیه‌یی", "himemât-ı reşâdiyeleriyle": "رشادیه‌لریله",
         "duâ-yı irşâdiyelerini": "ارشادیه‌لرینی", "lem‘a-i i‘câziye": "اعجازیه", "nûriyye": "نوریه", "maksad-ı hakîkîye": "حقیقی یه", "ciddiye": "جدّی یه",
         "Arabiye gitti": "عربی یه", "veliye": "ولی یه", "hediye": "هدیّه", "saniye": "ثانیه"}
for s, o in ister.items():
    c = tt(s)
    assert o in c, (s, c, o)
print("SONUC: HEPSI GECTI")
