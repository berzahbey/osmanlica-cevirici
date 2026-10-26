"""Tur T2 (27 Ekim): -sA ek-fiil korumasi (lisansa), hersey- ayri ve sey Hayrat yazimiyla, -lUk + ek Hayrat kalibiyla (sorumlulugu),
Cem ozel ad / cem terim, ornegin zarf, kitap sozlugu Tur T2 bolumu.
Calistirma: docker run --rm -v "$PWD":/k -w /k berzahbey/osmanlica-cevirici:latest python tests/test_tur_t2.py"""
import logging
import os
import sys

logging.disable(50)
KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app")
sys.path.insert(0, KOK)
from engine.transliterator import transliterate_text as T  # noqa: E402

DURUMLAR = [('lisansa', '\u0644\u06cc\u0633\u0627\u0646\u0633\u0647'), ('dansa', '\u062f\u0627\u0646\u0633\u0647'), ('sahipse', '\u0635\u0627\u062d\u0628\u0633\u0647'), ('cahildi', '\u062c\u0627\u0647\u0644\u062f\u06cc'), ('her\u015fey', '\u0647\u0631 \u0634\u06cc'), ('her\u015feyi', '\u0647\u0631 \u0634\u06cc\u0626\u06cc'), ('her\u015feye', '\u0647\u0631 \u0634\u06cc\u0626\u0647'), ('her\u015feyin', '\u0647\u0631 \u0634\u06cc\u0626\u06ad'), ('Cem', '\u062c\u0645'), ('cem', '\u062c\u0645\u0639'), ('\xd6rne\u011fin', '\u0627\u0648\u0631\u0646\u0643\u06cc\u0646'), ('\xf6rne\u011fin', '\u0627\u0648\u0631\u0646\u0643\u06cc\u0646'), ('nesnel', '\u0646\u0633\u0646\u0647\u200c\u0644'), ('nesnellik', '\u0646\u0633\u0646\u0647\u200c\u0644\u0644\u0643'), ('sorumlulu\u011fu', '\u0635\u0648\u0631\u0648\u0645\u0644\u06cc\u0644\u063a\u06cc'), ('sorumlulu\u011funu', '\u0635\u0648\u0631\u0648\u0645\u0644\u06cc\u0644\u063a\u0646\u06cc'), ('\xf6zg\xfcrl\xfc\u011f\xfcn\xfc', '\u0627\u0648\u0632\u0643\u0648\u0631\u0644\u0643\u0646\u06cc'), ('b\xfct\xfcnl\xfc\u011f\xfcne', '\u0628\u062a\u0648\u0646\u0644\u0643\u0646\u0647'), ('yoklu\u011fu', '\u06cc\u0648\u0642\u0644\u063a\u06cc'), ('solu\u011funu', '\u0635\u0648\u0644\u0648\u063a\u0648\u0646\u06cc'), ('\xe7o\u011funlu\u011funun', '\u0686\u0648\u063a\u0646\u0644\u0648\u063a\u0648\u0646\u06ad'), ('sa\u011flar', '\u0635\u0627\u063a\u0644\u0627\u0631'), ('tamamla', '\u062a\u0645\u0627\u0645\u0644\u0627'), ('besin', '\u0628\u0633\u06cc\u0646'), ('vadisinde', '\u0648\u0627\u062f\u06cc\u0633\u0646\u062f\u0647'), ('vadide', '\u0648\u0627\u062f\u06cc\u062f\u0647'), ('adamd\u0131', '\u0622\u062f\u0645\u062f\u06cc'), ('y\xf6nelik', '\u06cc\u0648\u06ad\u0644\u06cc\u0643'), ('\xf6nemli', '\u0627\u0648\u06ad\u0645\u0644\u06cc')]


def main():
    kalan = 0
    for latin, beklenen in DURUMLAR:
        cikan = T(latin).strip()
        if cikan != beklenen:
            kalan += 1
            print("KALDI", ascii(latin), "->", ascii(cikan), "(beklenen", ascii(beklenen) + ")")
    yol = os.path.join(KOK, "data", "kitap_sozlugu.tsv")
    bolum = False
    for satir in open(yol, encoding="utf-8"):
        if satir.startswith("# Tur T2"):
            bolum = True
            continue
        if not bolum or satir.startswith("#") or not satir.strip():
            continue
        latin, yazim = satir.rstrip("\n").split("\t")[:2]
        cikan = T(latin).strip()
        if cikan.replace("\u0651", "") != yazim.replace("\u0651", ""):
            kalan += 1
            print("KALDI (sozluk)", ascii(latin), "->", ascii(cikan), "(beklenen", ascii(yazim) + ")")
    print("SONUC: HEPSI GECTI" if not kalan else "SONUC: %d TEST KALDI" % kalan)


if __name__ == "__main__":
    main()
