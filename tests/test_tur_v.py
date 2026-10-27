"""Tur V (27 Ekim): Risale denetimi: bitisik onuc, kesmeli tam kelime (ser'iye), disil -iye + ek, kesmeli ad + iyelik (Rahim'ine), -magA,
kitap sozlugu Tur V bolumu.
Calistirma: docker run --rm -v "$PWD":/k -w /k berzahbey/osmanlica-cevirici:latest python tests/test_tur_v.py"""
import logging
import os
import sys

logging.disable(50)
KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app")
sys.path.insert(0, KOK)
from engine.transliterator import full_pipeline, transliterate_text as T  # noqa: E402

KELIMELER = [('on\xfc\xe7', '\u0627\u0648\u0646 \u0627\u0648\u0686'), ('on\xfc\xe7\xfcnc\xfc', '\u0627\u0648\u0646 \u0627\u0648\u0686\u0646\u062c\u06cc'), ('onbir', '\u0627\u0648\u0646 \u0628\u0631'), ('\u015fer\u2019iye', '\u0634\u0631\u0639\u06cc\u0647'), ("\u015fer'iye", '\u0634\u0631\u0639\u06cc\u0647'), ('merkeziyenin', '\u0645\u0631\u0643\u0632\u06cc\u0647\u200c\u0646\u06ad'), ('remziyeyi', '\u0631\u0645\u0632\u06cc\u0647\u200c\u06cc\u06cc'), ('\xe2diyenin', '\u0639\u0627\u062f\u06cc\u0647\u200c\u0646\u06ad'), ('esasiyeyi', '\u0627\u0633\u0627\u0633\u06cc\u0647\u200c\u06cc\u06cc'), ('diyedir', '\u062f\u06cc\u06cc\u0647\u200c\u062f\u0631'), ('hediyesi', '\u0647\u062f\u06cc\u0647\u200c\u0633\u06cc'), ('kediye', '\u0643\u062f\u06cc \u06cc\u0647'), ('Rah\xeem\u2019ine', '\u0631\u062d\u06cc\u0645\u0646\u0647'), ('Rah\xeem\u2019inin', '\u0631\u062d\u06cc\u0645\u0646\u06ad'), ("Ahmed'ine", '\u0627\u062d\u0645\u062f\u0646\u0647'), ("Allah'\u0131n", '\u0627\u0644\u0644\u0651\u0647\u06ad'), ("Kur'\xe2n'\u0131na", '\u0642\u0631\u0622\u0646\u0646\u0647'), ("Ali'nin", '\u0639\u0644\u06cc\u0646\u06ad'), ('okuma\u011fa', '\u0627\u0648\u0642\u0648\u0645\u063a\u0647'), ('ba\u011f\u0131rma\u011fa', '\u0628\u0627\u063a\u06cc\u0631\u0645\u063a\u0647'), ('parma\u011fa', '\u067e\u0627\u0631\u0645\u0627\u063a\u0647'), ('\u0131rma\u011fa', '\u0627\u06cc\u0631\u0645\u0627\u063a\u0647'), ('dama\u011fa', '\u062f\u0645\u0627\u063a\u0647')]
CUMLELER = [("Rahm\xe2n-\u0131 Rah\xeem'ine \u015f\xfck\xfcr.", '\u0631\u062d\u0645\u0627\u0646 \u0631\u062d\u06cc\u0645\u0646\u0647 \u0634\u0643\u0631.'), ('on\xfc\xe7 as\u0131r \xf6nce', '\u0627\u0648\u0646 \u0627\u0648\u0686 \u0639\u0635\u0631 \u0627\u0648\u06ad\u062c\u0647'), ('Allah\xfc Ekber', '\u0627\u0644\u0644\u0651\u0647 \u0627\u0643\u0628\u0631'), ('\u015fer\u2019iye ve merkeziyenin', '\u0634\u0631\u0639\u06cc\u0647 \u0648 \u0645\u0631\u0643\u0632\u06cc\u0647\u200c\u0646\u06ad')]


def main():
    kalan = 0
    for latin, beklenen in KELIMELER:
        cikan = T(latin).strip()
        if cikan != beklenen:
            kalan += 1
            print("KALDI", ascii(latin), "->", ascii(cikan), "(beklenen", ascii(beklenen) + ")")
    for latin, beklenen in CUMLELER:
        cikan = full_pipeline(latin, assume_turkish=True)["ottoman_text"].strip()
        if cikan != beklenen:
            kalan += 1
            print("KALDI (cumle)", ascii(latin), "->", ascii(cikan), "(beklenen", ascii(beklenen) + ")")
    yol = os.path.join(KOK, "data", "kitap_sozlugu.tsv")
    bolum = False
    for satir in open(yol, encoding="utf-8"):
        if satir.startswith("# Tur V"):
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
