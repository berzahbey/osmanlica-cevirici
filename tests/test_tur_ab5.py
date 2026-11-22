"""Tur AB5 (22 Kasım 2026, İlimlerin Sayımı / Nemotron denemesi): kesmeyle Türkçe ek almış ad yabancı dizisine katılmaz;
yapay zekânın -iye nisbe yazılışı köke verilmez."""
import os, sys, pathlib, tempfile
_t = tempfile.NamedTemporaryFile("w", suffix=".tsv", delete=False, encoding="utf-8")
_t.write("# kelime\tkoken\tkok\tyazilis\tokunus\tanlam\tdurum\tmodel\ttarih\n"
         "Eflâtun\tel\tPlaton\tافلاطون\tPlaton\tkişi adı\tonayli\tgemini-3.5-flash\t\n"
         "Eflâtuniye\tar\teflâtunî\tافلاطونیه\t\tPlatoncu\tonayli\tgemini-3.5-flash\t\n")
_t.close()
os.environ["YZ_SOZLUK"] = _t.name
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "app"))
from engine.transliterator import transliterate_text as tt

ister = {"Ve bu tercüme 1638'de Paris'te Alpharabi philosophi opusculum adı ile basıldı.": "پاریسده",
         "Paris'te Alpharabi philosophi": "پاریسده",
         "Kitâb-ül-elfâz - il - Eflâtuniye": "افلاطونیه",
         "Eflâtuni okudu": "افلاطونی ",
         "Arabiye gitti": "عربی یه"}
yasak = {"Kitâb-ül-elfâz - il - Eflâtuniye": "افلاطونیه‌یه", "Paris'te Alpharabi philosophi": "پاریست "}
for s, o in ister.items():
    c = tt(s)
    assert o in c, (s, c, o)
for s, o in yasak.items():
    c = tt(s)
    assert o not in c, (s, c, o)
print("SONUC: HEPSI GECTI")
