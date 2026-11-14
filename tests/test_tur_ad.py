"""Tur AD: hep büyük harfle geçen ad, sözlük yazımı ad için güvenilmezse (şapkasız eşleşme ya da birden çok yazım) yapay zekâya sorulur;
ad kaydı cümle ortasında ve kesmeli hâlde kullanılır, cümle başındaki kesmesiz kelimede sözlük yazar (Emir verdi)."""
import os, sys, pathlib, tempfile
os.environ["YZ_SOZLUK"] = os.path.join(tempfile.mkdtemp(), "yz.tsv")
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "app"))
from engine import yz_kayit as Y
from engine.transliterator import transliterate_text as tt

m = "Naim kaleye çıktı. Sonra Naim ile Emir konuştu. Bunu gören Emir, Hasan Sabbah'a gitti. Kemal de geldi, Kemal güldü."
b = Y.bilinmeyenler(m)
assert "Naim" in b and "Emir" in b and "Kemal" not in b, b
assert not Y.ad_belirsiz("kemal") and Y.ad_belirsiz("naim") and Y.ad_belirsiz("emir")
Y.ekle([{"kelime": "Naim", "koken": "ar", "kok": "Naim", "yazilis": "نعیم", "anlam": "kişi adı", "model": "gemini-4-hydrogen"},
        {"kelime": "Emir", "koken": "ar", "kok": "Emir", "yazilis": "امیر", "anlam": "unvan", "model": "gemini-4-hydrogen"}])
c = {"Sonra Naim ile Emir konuştu.": ["نعیم", "امیر"], "Naim'in atı geldi.": ["نعیمڭ"], "Emir verdi ve gitti.": ["امر"],
     "Bu bir emir idi.": ["امر"]}
for s, ister in c.items():
    o = tt(s)
    for x in ister:
        assert x in o.split(), (s, o, x)
print("SONUC: HEPSI GECTI")
