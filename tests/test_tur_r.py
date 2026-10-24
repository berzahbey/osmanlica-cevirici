"""Tur R (25 Ekim): kitap sozlugu (app/data/kitap_sozlugu.tsv). Her kayit kendi yazimiyla cikmali (sozluk yuklenirken eklenen
sedde haric: ukiyye); ekli bicimler ve korunan Turkce kelimeler de sinanir.
Calistirma: docker run --rm -v "$PWD":/k -w /k berzahbey/osmanlica-cevirici:latest python tests/test_tur_r.py"""
import logging
import os
import sys

logging.disable(50)
KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app")
sys.path.insert(0, KOK)
from engine.transliterator import transliterate_text as T  # noqa: E402

SEDDE_EKLENEN = {"ukiyye": "\u0627\u0648\u0642\u06cc\u0651\u0647"}
EKLI = [
    ("Ras\u00fblullah'a", "\u0631\u0633\u0648\u0644 \u0627\u0644\u0644\u0651\u0647\u0647"),
    ("Allah\u2019ta", "\u0627\u0644\u0644\u0651\u0647\u062f\u0647"),
    ("Haccac'\u0131n", "\u062d\u062c\u0651\u0627\u062c\u06ad"),
    ("Gatafanlar\u0131n", "\u063a\u0637\u0641\u0627\u0646\u0644\u0631\u06ad"),
    ("Hudeybiye'de", "\u062d\u062f\u06cc\u0628\u06cc\u0647\u200c\u062f\u0647"),
    ("Abd\u00fclmelik'in", "\u0639\u0628\u062f \u0627\u0644\u0645\u0644\u0643\u06ad"),
]
KORUNAN = [("raf", "\u0631\u0627\u0641"), ("raf\u0131", "\u0631\u0627\u0641\u06cc"), ("seyir", "\u0633\u06cc\u0631"),
           ("olgun", "\u0627\u0648\u0644\u063a\u0648\u0646"), ("rebia", "\u0631\u0628\u06cc\u0639\u0647")]


def main():
    kalan = 0
    yol = os.path.join(KOK, "data", "kitap_sozlugu.tsv")
    for satir in open(yol, encoding="utf-8"):
        if satir.startswith("#") or not satir.strip():
            continue
        w, b = satir.rstrip("\n").split("\t")[:2]
        b = SEDDE_EKLENEN.get(w, b)
        c = T(w).strip()
        if c != b:
            kalan += 1
            print(f"KALDI {w} -> {c} (beklenen {b})")
    for w, b in EKLI + KORUNAN:
        c = T(w).strip()
        if c != b:
            kalan += 1
            print(f"KALDI {w} -> {c} (beklenen {b})")
    print("SONUC: HEPSI GECTI" if not kalan else f"SONUC: {kalan} TEST KALDI")


if __name__ == "__main__":
    main()
