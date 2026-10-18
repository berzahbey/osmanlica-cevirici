"""Tur O (18 Ekim): Kur'an okunus katmani kaldirildi. Parantez icindeki Latin harfli Arapca, Kur'an'daki bir kelimeyle
degistirilmez; parantez disindaki metinle ayni yoldan (harf harf) cevrilir.
Calistirma: docker run --rm -v "$PWD":/k -w /k berzahbey/osmanlica-cevirici:latest python tests/test_tur_o.py"""
import logging
import os
import sys

logging.disable(50)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app"))
from engine.transliterator import transliterate_text as T  # noqa: E402

# (metin, ciktida OLMAMASI gereken Kur'an yazimi)
YASAK = [
    ("Fakihler (furu\u0302'un) ayrintilarinda", "\u0641\u0631\u0639\u0648\u0646"),
    ("azat eden (mu'tik) kisi", "\u0645\u0627 \u0623\u062a\u0648\u0643"),
    ("akli zayif (ma'tuh) olan", "\u0645\u0648\u062a\u0647"),
    ("2. Sak\u0131nanlar (el-muttaq\u00een) i\u00e7in", "\u0627\u0644\u0645\u062a\u0651\u0642\u06cc\u0646"),
    ("6. nank\u00f6rl\u00fck edenleri (el-kefer\u00fb) uyarsan da", "\u0643\u0641\u0631\u0648\u0627"),
]


def main():
    kalan = 0
    try:
        import engine.kuran_okunus  # noqa: F401
        kalan += 1
        print("KALDI: engine.kuran_okunus hala var")
    except ImportError:
        pass
    for w, yasak in YASAK:
        c = T(w)
        if yasak in c:
            kalan += 1
            print(f"KALDI {w} -> {c} (icinde {yasak} olmamali)")
        # parantez ici, parantez olmadan cevrilenle ayni olmali
        ic = w[w.index("(") + 1:w.index(")")]
        if T(ic).strip() not in c:
            kalan += 1
            print(f"KALDI {w} -> {c} (parantez ici {T(ic).strip()} olmali)")
    print("SONUC: HEPSI GECTI" if not kalan else f"SONUC: {kalan} TEST KALDI")


if __name__ == "__main__":
    main()
