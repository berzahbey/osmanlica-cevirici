"""Tur Q (24 Ekim, 34 kitap denetimi 3): bulunma eki -ta/-te ده, sozlukte olmayan ad + kesmeli -ya/-ye ayri,
yabanci Latin harfleri (cevrilen kelimede e-akut, sz...; yabanci ibare asliyla kalir), ad ve kelime duzeltmeleri (Rasulallah, Umeyye, ispat, sonuc...). Yazim birebir (ZWNJ dahil).
Calistirma: docker run --rm -v "$PWD":/k -w /k berzahbey/osmanlica-cevirici:latest python tests/test_tur_q.py"""
import logging
import os
import sys

logging.disable(50)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app"))
from engine.transliterator import transliterate_text as T  # noqa: E402

DURUMLAR = [
    ("ger\u00e7ekte", "\u0643\u0631\u0686\u0643\u062f\u0647"),
    ("sonu\u00e7ta", "\u0635\u0648\u06ad\u0648\u0686\u062f\u0647"),
    ("sava\u015fta", "\u0635\u0627\u0648\u0627\u0634\u062f\u0647"),
    ("ba\u015flang\u0131\u00e7ta", "\u0628\u0627\u0634\u0644\u0627\u0646\u063a\u06cc\u0686\u062f\u0647"),
    ("bilin\u00e7te", "\u0628\u06cc\u0644\u06cc\u0646\u0686\u062f\u0647"),
    ("grupta", "\u063a\u0631\u0648\u067e\u062f\u0647"),
    ("\u00f6zellikte", "\u0627\u0648\u0632\u0644\u0644\u0643\u062f\u0647"),
    ("dipte", "\u062f\u06cc\u067e\u062f\u0647"),
    ("Tanr\u0131\u2019ya", "\u0637\u0627\u06ad\u0631\u06cc \u06cc\u0647"),
    ("Habe\u015f\u00ee'ye", "\u062d\u0628\u0634\u06cc \u06cc\u0647"),
    ("Maturidi\u2019ye", "\u0645\u0627\u062a\u0648\u0631\u06cc\u062f\u06cc \u06cc\u0647"),
    ("L\u00e9vi", "\u0644\u0648\u06cc"),
    ("Trait\u00e9", "\u062a\u0631\u0627\u06cc\u062a\u0647"),
    ("da\u00df", "\u062f\u0627\u0633\u0633"),
    ("\u00cdsl\u00e2m", "\u0627\u0633\u0644\u0627\u0645"),
    ("Ras\u00fblallah", "\u0631\u0633\u0648\u0644 \u0627\u0644\u0644\u0651\u0647"),
    ("\u00dcmeyye", "\u0627\u0645\u06cc\u0651\u0647"),
    ("Avf", "\u0639\u0648\u0641"),
    ("Muaz", "\u0645\u0639\u0627\u0630"),
    ("Hi\u015fam", "\u0647\u0634\u0627\u0645"),
    ("\u00dcbeyy", "\u0627\u0628\u06cc\u0651"),
    ("Kurayza", "\u0642\u0631\u06cc\u0638\u0647"),
    ("Abdulmuttalib", "\u0639\u0628\u062f \u0627\u0644\u0645\u0637\u0651\u0644\u0628"),
    ("ispat", "\u0627\u062b\u0628\u0627\u062a"),
    ("sonucu", "\u0635\u0648\u06ad\u0648\u062c\u06cc"),
    ("sonucunda", "\u0635\u0648\u06ad\u0648\u062c\u0646\u062f\u0647"),
    ("sonu\u00e7lar", "\u0635\u0648\u06ad\u0648\u0686\u0644\u0631"),
    ("sonu\u00e7land\u0131", "\u0635\u0648\u06ad\u0648\u0686\u0644\u0627\u0646\u062f\u06cc"),
    ("arac\u0131l\u0131\u011f\u0131yla", "\u0622\u0631\u0627\u062c\u06cc\u0644\u063a\u06cc\u0644\u0647"),
    ("uyum", "\u0627\u0648\u06cc\u0648\u0645"),
    ("dayal\u0131", "\u0637\u0627\u06cc\u0627\u0644\u06cc"),
    ("\u00f6zne", "\u0627\u0648\u0632\u0646\u0647"),
    ("b\u00e2til", "\u0628\u0627\u0637\u0644"),
    ("mubah", "\u0645\u0628\u0627\u062d"),
    ("ab\u0131hayat", "\u0622\u0628 \u062d\u06cc\u0627\u062a"),
    ("g\u00f6revi", "\u0643\u0648\u0631\u0648\u06cc"),
    ("bey'at", "\u0628\u06cc\u0639\u062a"),
    ("miyim", "\u0645\u06cc\u06cc\u0645"),
    ("i\u00e7inin", "\u0627\u06cc\u0686\u0646\u06ad"),
    ("bahset", "\u0628\u062d\u062b \u0627\u06cc\u062a"),
    ("\u00dcmm\u00fc Seleme", "\u0627\u0645\u0651 \u0633\u0644\u0645\u0647"),
    ("F\u00e2t\u0131ma binti Esed", "\u0641\u0627\u0637\u0645\u0647 \u0628\u0646\u062a \u0627\u0633\u062f"),
    ("hasta", "\u062e\u0633\u062a\u0647"),
    ("n\u00fckte", "\u0646\u0643\u062a\u0647"),
    ("liste", "\u0644\u06cc\u0633\u062a\u0647"),
    ("usta", "\u0627\u0648\u0633\u062a\u0647"),
    ("hafta", "\u0647\u0641\u062a\u0647"),
    ("i\u015fte", "\u0627\u06cc\u0634\u062a\u0647"),
    ("vakte", "\u0648\u0642\u062a\u0647"),
    ("\u00fcste", "\u0627\u0648\u0633\u062a\u0647"),
    ("\u00fcstte", "\u0627\u0648\u0633\u062a\u062f\u0647"),
    ("softa", "\u0635\u0648\u0641\u062a\u0647"),
    ("kaf'tan", "\u0642\u0627\u0641\u062f\u0646"),
    ("ba\u015fta", "\u0628\u0627\u0634\u062f\u0647"),
    ("El\u00e7i'ye", "\u0627\u06cc\u0644\u0686\u06cc \u06cc\u0647"),
    ("Musa'ya", "\u0645\u0648\u0633\u06cc \u06cc\u0647"),
    ("tanr\u0131ya", "\u0637\u0627\u06ad\u0631\u06cc \u06cc\u0647"),
    ("nokta", "\u0646\u0642\u0637\u0647"),
]
# Tamamen Latin kalan yabanci ibare (kaynakca) oldugu gibi kalir
LATIN_KALIR = ["Brunschvig, La Berb\u00e9rie orientale sous les Hafsides", "Soci\u00e9t\u00e9 de Droit Compar\u00e9, lix"]
LATIN_YOK = ["L\u00e9vi-Proven\u00e7al", "Gewi\u00dfheit", "Encyclop\u00e9die de l\u2019Isl\u00e2m"]


def main():
    kalan = 0
    for w, b in DURUMLAR:
        c = T(w).strip()
        if c != b:
            kalan += 1
            print(f"KALDI {w} -> {c} (beklenen {b})")
    for w in LATIN_YOK:
        c = T(w)
        if any(ch.isalpha() and ord(ch) < 0x0250 for ch in c):
            kalan += 1
            print(f"KALDI {w}: Latin harf kaldi: {c}")
    for w in LATIN_KALIR:
        if T(w).strip() != w:
            kalan += 1
            print(f"KALDI {w}: Latin ibare degisti: {T(w)}")
    print("SONUC: HEPSI GECTI" if not kalan else f"SONUC: {kalan} TEST KALDI")


if __name__ == "__main__":
    main()
