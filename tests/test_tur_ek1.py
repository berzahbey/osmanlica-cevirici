"""Tur EK1 (23 Kasım 2026, Hayrat bırak-birini-dışarıda ölçümü): ettirgen -tır د ile; olumsuz ortaç/geçmiş -mAdI elifsiz;
ünlüyle biten fiil kökü + -Iyor kökün ünlüsüyle. Hayrat kelimeleri geçici çıkarılarak denenir (ezber değil kural)."""
import os, sys, pathlib
os.environ.setdefault("YZ_SOZLUK", "/yok")
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "app"))
from engine import dictionary as D
from engine.transliterator import transliterate_text as tt


def loo(w):
    sak = [(m, m.pop(w)) for m in (D.DICTIONARY, D.FLAT, D.HAYRAT_TEK) if w in m]
    an = w in D.HAYRAT_ANAHTAR
    D.HAYRAT_ANAHTAR.discard(w)
    try:
        return tt(w)
    finally:
        for m, v in sak:
            m[w] = v
        if an:
            D.HAYRAT_ANAHTAR.add(w)


ister = {"çarptırdı": "چارپدیردی", "kestirdi": "كسدیردی", "bıraktırılmış": "بیراقدیریلمش", "konuşturur": "قونوشدیرر",
         "yutturdular": "یوتدیردیلر", "çıkaramadıkları": "چیقارامدقلری", "yapamadı": "یاپامدی", "arıyordun": "آرایوردڭ",
         "arıyor": "آرایور", "oluyordun": "اولویوردڭ", "söylüyor": "سویله‌یور", "bağırıyor": "باغیرییور"}
for s, o in ister.items():
    c = loo(s)
    assert c == o, (s, c, o)
print("SONUC: HEPSI GECTI")
