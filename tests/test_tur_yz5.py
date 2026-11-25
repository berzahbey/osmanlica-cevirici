"""Tur YZ5 (25 Kasım 2026): köken kaydının Arapça/Farsça kökü, kayıt bozuksa sözlüğe kök olarak girmez (kayıt saklanır).
Ölçüm (Hayrat sözlüğü kapalı = Hayrat'ta olmayan kelime gibi): Muhâkemât köken açık HATA 1746 -> 1696, İşârât 3638 -> 3289
(köken kapalı 1805 / 3467)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.environ.setdefault("YZ_SOZLUK", "/yok")
from app.engine import yz_kayit as Y
B = []
def ok(kelime, kok, yazilis, beklenen):
    r = {"kelime": kelime, "kok": kok, "yazilis": yazilis, "koken": "ar", "durum": "onayli", "model": "nvidia/nemotron-3-ultra-550b-a55b"}
    c = Y.yz5_red(r); B.append(c == beklenen)
    print(("GECTI " if c == beklenen else "KALDI ") + f"{kelime} / {kok} {yazilis} -> {c}" + ("" if c == beklenen else f"  (beklenen {beklenen})"))
ok("bulri", "bulur", "بلور", "turkce")          # OCR çöpüne yaygın Türkçe kelime kök verilmiş (bul+ur)
ok("nondan", "neden", "ندن", "turkce")         # Hayrat kökü neden نه‌دن
ok("Bedhem", "bedhn", "بدهن", "kayma")
ok("Aras", "aras", "ارس", "ozel")               # özel ad genel köke girmez (arasında ارسنده olmasın)
ok("Anas", "anas", "انس", "ozel")
ok("kahramanları", "kahraman", "قهرمان", None)  # doğru kayıtlar kalır
ok("Sevâbu", "sevap", "ثواب", None)
ok("kitabını", "kitap", "كتاب", None)
ok("el-Mülûk", "el-mülûk", "الملوك", None)
ok("müçtehit", "müçtehid", "مجتهد", None)
print("SONUC:", "HEPSI GECTI" if all(B) else f"{B.count(False)} KALDI")
sys.exit(0 if all(B) else 1)
