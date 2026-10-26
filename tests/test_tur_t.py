"""Tur T (26 Ekim): on/yon ailesi kaf-i nuni (Zahir), ek-fiil (cahildi, sahipse), -dAydI, -mIyor, -mAktAydI, kitap sozlugu Tur T bolumu.
Hayrat'taki kelimelere (olmuyor, sandi, giydi, sirti) dokunulmaz; on/onu/onda/ondan, yont-, yonca etkilenmez.
Calistirma: docker run --rm -v "$PWD":/k -w /k berzahbey/osmanlica-cevirici:latest python tests/test_tur_t.py"""
import logging
import os
import sys

logging.disable(50)
KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app")
sys.path.insert(0, KOK)
from engine.transliterator import transliterate_text as T  # noqa: E402

DURUMLAR = [('\xf6nce', '\u0627\u0648\u06ad\u062c\u0647'), ('\xf6nemli', '\u0627\u0648\u06ad\u0645\u0644\u06cc'), ('\xf6nemi', '\u0627\u0648\u06ad\u0645\u06cc'), ('\xf6nder', '\u0627\u0648\u06ad\u062f\u0631'), ('\xf6nc\xfcl', '\u0627\u0648\u06ad\u062c\u0648\u0644'), ('\xf6nlem', '\u0627\u0648\u06ad\u0644\u0645'), ('y\xf6n', '\u06cc\u0648\u06ad'), ('y\xf6n\xfc', '\u06cc\u0648\u06ad\u06cc'), ('y\xf6n\xfcnden', '\u06cc\u0648\u06ad\u0646\u062f\u0646'), ('y\xf6nelik', '\u06cc\u0648\u06ad\u0644\u06cc\u0643'), ('y\xf6nelim', '\u06cc\u0648\u06ad\u0644\u0645'), ('y\xf6netim', '\u06cc\u0648\u06ad\u062a\u06cc\u0645'), ('y\xf6ntem', '\u06cc\u0648\u06ad\u062a\u0645'), ('\xd6ng\xfct', '\u0627\u0648\u0646\u0643\u0648\u062a'), ('ona', '\u0627\u0648\u06ad\u0627'), ('onu', '\u0627\u0648\u0646\u06cc'), ('onda', '\u0627\u0648\u0646\u062f\u0647'), ('ondan', '\u0627\u0648\u0646\u062f\u0646'), ('onun', '\u0627\u0648\u0646\u06ad'), ('onunla', '\u0627\u0648\u0646\u06ad\u0644\u0647'), ('on', '\u0627\u0648\u0646'), ('yontulmu\u015f', '\u06cc\u0648\u0646\u062a\u0648\u0644\u0645\u0634'), ('yonca', '\u06cc\u0648\u0646\u062c\u0647'), ('cahildi', '\u062c\u0627\u0647\u0644\u062f\u06cc'), ('m\xfcthi\u015fti', '\u0645\u062f\u0647\u0634\u062f\u06cc'), ('zalimdi', '\u0638\u0627\u0644\u0645\u062f\u06cc'), ('kitapt\u0131', '\u0643\u062a\u0627\u0628\u062f\u06cc'), ('sahipse', '\u0635\u0627\u062d\u0628\u0633\u0647'), ('sarho\u015ftum', '\u0633\u0631\u062e\u0648\u0634\u062f\u0645'), ('hakikiydi', '\u062d\u0642\u06cc\u0642\u06cc\u062f\u06cc'), ('fazlayd\u0131', '\u0641\u0636\u0644\u0647\u200c\u06cc\u062f\u06cc'), ('aras\u0131ndayd\u0131', '\u0622\u0631\u0627\u0633\u0646\u062f\u0647\u200c\u06cc\u062f\u06cc'), ('zorundayd\u0131', '\u0632\u0648\u0631\u0646\u062f\u0647\u200c\u06cc\u062f\u06cc'), ('i\xe7indeydim', '\u0627\u06cc\u0686\u0646\u062f\u0647\u200c\u06cc\u062f\u0645'), ('korkmuyor', '\u0642\u0648\u0631\u0642\u0645\u06cc\u06cc\u0648\u0631'), ('yapm\u0131yordu', '\u06cc\u0627\u067e\u0645\u06cc\u06cc\u0648\u0631\u062f\u06cc'), ('bulunmaktayd\u0131', '\u0628\u0648\u0644\u0648\u0646\u0645\u0642\u062f\u0647\u200c\u06cc\u062f\u06cc'), ('etmekteydi', '\u0627\u06cc\u062a\u0645\u0643\u062f\u0647\u200c\u06cc\u062f\u06cc'), ('kendisiydi', '\u0643\u0646\u062f\u06cc\u0633\u06cc\u062f\u06cc'), ('olmuyor', '\u0627\u0648\u0644\u0645\u0627\u06cc\u0648\u0631'), ('sand\u0131', '\u0635\u0627\u0646\u062f\u06cc'), ('giydi', '\u0643\u06cc\u06cc\u062f\u06cc'), ('s\u0131rt\u0131', '\u0635\u06cc\u0631\u062a\u06cc'), ('kapad\u0131', '\u0642\u0627\u067e\u0627\u062f\u06cc'), ('g\xfcld\xfc', '\u0643\u0648\u0644\u062f\u06cc'), ('istemedim', '\u0627\u06cc\u0633\u062a\u0647\u200c\u0645\u062f\u0645'), ('da\u011f\u0131tsa', '\u0637\u0627\u063a\u06cc\u062a\u0633\u0647'), ('yarasa', '\u06cc\u0627\u0631\u0627\u0633\u0647')]


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
        if satir.startswith("# Tur T"):
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
