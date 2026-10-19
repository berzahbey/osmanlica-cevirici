"""Tur P (18 Ekim): sozlukte kesmesiz yazim (mukatta'at -> mukattaat), alt elif (U+0656) artigi, Hayrat ifadesi + ek ZWNJ
(hakaik-i imaniyeyi), Kur'an-i Mu'ciz-ul Beyan, ad (isim), Sahabeddin, Joseph Schacht. Yazim birebir (ZWNJ dahil).
Calistirma: docker run --rm -v "$PWD":/k -w /k berzahbey/osmanlica-cevirici:latest python tests/test_tur_p.py"""
import logging
import os
import sys

logging.disable(50)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app"))
from engine.transliterator import transliterate_text as T  # noqa: E402

DURUMLAR = [
    ("mukattaat", "\u0645\u0642\u0637\u0651\u0639\u0627\u062a"),
    ("hakaik-i imaniyeyi", "\u062d\u0642\u0627\u0626\u0642 \u0627\u06cc\u0645\u0627\u0646\u06cc\u0647\u200c\u06cc\u06cc"),
    ("Kudret-i \u0130lahiyenin", "\u0642\u062f\u0631\u062a \u0627\u0644\u0647\u06cc\u0651\u0647\u200c\u0646\u06ad"),
    ("Kur\u2019an-\u0131 Mu\u2019ciz-\u00fcl Beyan\u2019\u0131n", "\u0642\u0631\u0622\u0646 \u0645\u0639\u062c\u0632 \u0627\u0644\u0628\u06cc\u0627\u0646\u06ad"),
    ("ad koydu", "\u0622\u062f \u0642\u0648\u06cc\u062f\u06cc"),
    ("adlar\u0131", "\u0622\u062f\u0644\u0631\u06cc"),
    ("\u015eahabeddin", "\u0634\u0647\u0627\u0628 \u0627\u0644\u062f\u0651\u06cc\u0646"),
    ("Joseph Schacht", "\u0698\u0648\u0632\u0641 \u0634\u0627\u062e\u062a"),
    ("cemiyyet", "\u062c\u0645\u0639\u06cc\u062a"),
]
YOK = ["Anadolu", "al\u0131n", "avc\u0131", "alacakl\u0131"]   # ciktida U+0656 olmamali
KORUNAN = [("aras\u0131", "\u0622\u0631\u0627\u0633\u06cc"), ("tan", "\u0637\u0627\u0646"), ("ada", "\u0622\u0637\u0647")]


def main():
    kalan = 0
    for w, b in DURUMLAR + KORUNAN:
        c = T(w).strip()
        if c != b:
            kalan += 1
            print(f"KALDI {w} -> {c} (beklenen {b})")
    for w in YOK:
        if "\u0656" in T(w):
            kalan += 1
            print(f"KALDI {w}: alt elif var")
    print("SONUC: HEPSI GECTI" if not kalan else f"SONUC: {kalan} TEST KALDI")


if __name__ == "__main__":
    main()
