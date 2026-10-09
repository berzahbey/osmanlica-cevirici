# -*- coding: utf-8 -*-
"""Bağlam sözlüğü (Hayrat). Çalıştırma: python tests/test_baglam.py"""
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))
from engine.transliterator import transliterate_text as t, _BAGLAM


def n(s):
    return re.sub("[\u064b-\u065f\u0670\u200c]", "", s).replace("\u06d5", "\u0647")


hata = 0
if not _BAGLAM:
    print("HATA: bağlam tablosu yüklenmedi (app/data/hayrat_baglam.tsv)"); hata += 1
BEKLENEN = [("Kızarmış et yedi.", "قیزارمش ات یدی."), ("Buna dikkat et ve tefekkür et.", None)]
for latin, osm in BEKLENEN:
    c = t(latin)
    if osm and n(c) != n(osm):
        print("HATA:", latin, "beklenen", osm, "çıkan", c); hata += 1
    if osm is None and "ایت" not in c:
        print("HATA:", latin, "et (yap) ایت olmalı:", c); hata += 1
# dokunulmaması gerekenler: tablo dışı kelimeler ve bağlamsız tek kelime aynı kalmalı
for latin in ["Bu da‘vâ doğrudur.", "senin başına", "nübüvvet-i mutlaka", "zahiren", "Risâle-i Nûr"]:
    import engine.transliterator as T
    if t(latin) != T._transliterate_text_baglamsiz(latin):
        print("HATA: bağlam katmanı tablo dışı metni değiştirdi:", latin); hata += 1
print("SONUC: HEPSI GECTI" if not hata else f"SONUC: {hata} HATA")
