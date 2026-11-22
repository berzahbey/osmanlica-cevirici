"""Tur YB (22 Kasım 2026, 41 kitap denetimi): sözlükte bulunan Türkçe/Arapça kelime th/sh/ph/ea/ae izi yüzünden yabancı dizisine
katılmaz (fethi Hayber'i fethettirmek -> فتی خیبری فتتیرمك oluyordu). Gerçek yabancı diziler (İngilizce, Latince) yine yabancı sayılır.
Calistirma: docker run --rm -v "$PWD":/k -w /k berzahbey/osmanlica-cevirici:latest python tests/test_tur_yb.py"""
import logging
import os
import sys

logging.disable(50)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app"))
from engine import transliterator as TR  # noqa: E402

D = [
    ("vaad buyurduğu fethi Hayber'i fethettirmek suretiyle", "وعد بویوردیغی فتحی خیبری فتح ایتدیرمك صورتیله"),
    ("Binaenaleyh bu tearuz feshe sebep olur.", "بناءً علیه بو تعارض فسخه سبب اولور."),
]
TURKCE = ["fethi", "Feth", "Fethi'nin", "tearuz", "methiyesi", "cephesine", "mesh", "nesh", "feshi", "Binaenaleyh", "Bahaeddin",
          "tashihiyle", "fethetmekle"]
YABANCI = ["the", "and", "Tableau", "animae", "saecula", "divinae", "timouride", "revelee", "geheaden", "Ethics"]


def main():
    kalan = 0
    for a, b in D:
        c = TR.transliterate_text(a).strip()
        if c != b:
            kalan += 1
            print("KALDI", a, "->", c, "(beklenen", b + ")")
    for w in TURKCE:
        if TR._yabanci_mi(w):
            kalan += 1
            print("KALDI yabanci sayildi:", w)
    for w in YABANCI:
        if not TR._yabanci_mi(w):
            kalan += 1
            print("KALDI Turkce sayildi:", w)
    print("SONUC:", "HEPSI GECTI" if not kalan else f"{kalan} TEST KALDI")


main()
