"""Tur X (2 Kasım 2026): kaynak kısaltmaları (bkz. باقكز، vb./vs. الخ، vd. و مابعدی، s. ص، c. ج).
Calistirma: docker run --rm -v "$PWD":/k -w /k berzahbey/osmanlica-cevirici:latest python tests/test_tur_x.py"""
import logging
import os
import sys

logging.disable(50)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app"))
from engine.transliterator import transliterate_text as T  # noqa: E402

DURUMLAR = [("(bkz. s. 12, vd.)", "(باقكز ص ١٢، و مابعدی)"), ("Bkz. c. 2, s. 45.", "باقكز ج ٢، ص ٤٥."),
            ("kitaplar vb. şeyler", "كتابلر الخ شیلر"), ("ev, bağ vs. var", "او، باغ الخ وار"), ("C. II, ss. 10-15", "ج ٢، ص ١٠-١٥"),
            ("bk. Taberî", "باقكز طبری")]
DOKUNMA = ["Hz. Muhammed (s.a.v.) dedi.", "Ahmed b. Hanbel", "vb ile", "c harfi", "s harfi"]


def main():
    kalan = 0
    for latin, beklenen in DURUMLAR:
        c = T(latin).strip()
        if c != beklenen:
            kalan += 1
            print("KALDI", latin, "->", c, "(beklenen", beklenen + ")")
    for w in DOKUNMA:
        print("bilgi:", w, "->", T(w).strip())
    print("SONUC:", "HEPSI GECTI" if not kalan else f"{kalan} TEST KALDI")


main()
