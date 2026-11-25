"""25 Kasım: yalın -daki eki sözlükteki köke bağlanır (anlamındaki آڭلامنده‌كی; El Camiul 684 kez آنلامنده‌كی idi);
(sav), (s.a.v.), (sas) Hayrat'taki (a.s.m.) gibi (علیه الصلاة والسلام) yazılır (صاو değil)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.environ.setdefault("YZ_SOZLUK", "/yok")
from app.engine.transliterator import transliterate_text as T
B = []
def ok(a, b):
    c = T(a); B.append(c == b); print(("GECTI " if c == b else "KALDI ") + f"{a} -> {c}" + ("" if c == b else f"  (beklenen {b})"))
ok("anlamındaki söz", "آڭلامنده‌كی سوز")
ok("anlamında", "آڭلامنده")
ok("kitabındaki", "كتابنده‌كی")
ok("önlerindekini", "اوڭلرنده‌كینی")
ok("Peygamber (sav) dedi.", "پیغمبر (علیه الصلاة والسلام) دیدی.")
ok("Peygamber (s.a.v.) dedi.", "پیغمبر (علیه الصلاة والسلام) دیدی.")
ok("Peygamber (a.s.m.) dedi.", "پیغمبر (علیه الصلاة والسلام) دیدی.")
print("SONUC:", "HEPSI GECTI" if all(B) else f"{B.count(False)} KALDI")
sys.exit(0 if all(B) else 1)
