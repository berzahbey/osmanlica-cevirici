"""Tur K (18 Ekim, Bakara denetimi 3): -le fiilleri (belirle-, destekle-), -dIklAr-, -dIğIm-, -umuz, ğ/t + -InIn, iplik.
"korunan"lar (gözünün, elçinin, yerinin, kitaplarının: Hayrat ینڭ) bozulmamalı. Birebir (ZWNJ dahil) karşılaştırılır.
Çalıştırma: docker run --rm -v "$PWD":/k -w /k berzahbey/osmanlica-cevirici:latest python tests/test_tur_k.py"""
import logging
import os
import sys

logging.disable(50)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app"))
from engine.transliterator import transliterate_text as T  # noqa: E402

DURUMLAR = [
    ('belirlemi\u015f', '\u0628\u0644\u06cc\u0631\u0644\u0647\u200c\u0645\u0634'),
    ('belirlenmi\u015f', '\u0628\u0644\u06cc\u0631\u0644\u0647\u200c\u0646\u0645\u0634'),
    ('belirlemeden', '\u0628\u0644\u06cc\u0631\u0644\u0647\u200c\u0645\u0647\u200c\u062f\u0646'),
    ('belirledi\u011finizin', '\u0628\u0644\u06cc\u0631\u0644\u0647\u200c\u062f\u06cc\u0643\u06ad\u0632\u06ad'),
    ('destekledik', '\u062f\u0633\u062a\u0643\u0644\u0647\u200c\u062f\u0643'),
    ('harcad\u0131klar\u0131n\u0131n', '\u062e\u0631\u062c\u0627\u062f\u0642\u0644\u0631\u06cc\u0646\u06ad'),
    ('indirdi\u011fime', '\u0627\u06cc\u0646\u062f\u06cc\u0631\u062f\u06cc\u0643\u0645\u0647'),
    ('kulumuza', '\u0642\u0648\u0644\u0645\u0632\u0647'),
    ('krall\u0131\u011f\u0131n\u0131n', '\u0642\u0631\u0627\u0644\u0644\u063a\u0646\u06ad'),
    ('kal\u0131nt\u0131n\u0131n', '\u0642\u0627\u0644\u06cc\u0646\u062a\u0646\u06ad'),
    ('ipli\u011fi', '\u0627\u06cc\u067e\u0644\u0643\u06cc'),
    ('ipli\u011finden', '\u0627\u06cc\u067e\u0644\u0643\u0646\u062f\u0646'),
    ('\xe7a\u011f\u0131rd\u0131\u011f\u0131mda', '\u0686\u0627\u063a\u06cc\u0631\u062f\u06cc\u063a\u0645\u062f\u0647'),
    ('at\u0131ld\u0131klar\u0131nda', '\u0622\u062a\u06cc\u0644\u062f\u0642\u0644\u0631\u0646\u062f\u0647'),
    ('oldu\u011fumuz', '\u0627\u0648\u0644\u062f\u06cc\u063a\u0645\u0632'),
    ('kitaplar\u0131n\u0131n', '\u0643\u062a\u0627\u0628\u0644\u0631\u06cc\u0646\u06ad'),
    ('g\xf6z\xfcn\xfcn', '\u0643\u0648\u0632\u06cc\u0646\u06ad'),
    ('el\xe7inin', '\u0627\u06cc\u0644\u0686\u06cc\u0646\u06ad'),
    ('yerinin', '\u06cc\u0631\u06cc\u0646\u06ad'),
    ('ad\u0131n\u0131n', '\u0622\u062f\u06cc\u0646\u06ad'),
    ('peygamberinin', '\u067e\u06cc\u063a\u0645\u0628\u0631\u06cc\u0646\u06ad'),
    ('hayat\u0131n\u0131n', '\u062d\u06cc\u0627\u062a\u0646\u06ad'),
    ('s\xf6ylemi\u015f', '\u0633\u0648\u06cc\u0644\u0647\u200c\u0645\u0634'),
    ('temizleyin', '\u062a\u0645\u06cc\u0632\u0644\u0647\u200c\u06cc\u06ad'),
]


def main():
    kalan = 0
    for w, beklenen in DURUMLAR:
        c = T(w).strip()
        if c != beklenen:
            kalan += 1
            print(f"KALDI {w} -> {c} (beklenen {beklenen})")
    print("SONUC: HEPSI GECTI" if not kalan else f"SONUC: {kalan} TEST KALDI")


if __name__ == "__main__":
    main()
