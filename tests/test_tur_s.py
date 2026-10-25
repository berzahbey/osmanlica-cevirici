"""Tur S (25 Ekim): son yazim ek duzeltmeleri (-lIklA, -yIm ayri, -emem, -rsIn, -mAksIzIn, gecmis -tIn, onceki, yonelik, benz-) + men et- + kitap sozlugu.
Calistirma: docker run --rm -v "$PWD":/k -w /k berzahbey/osmanlica-cevirici:latest python tests/test_tur_s.py"""
import logging
import os
import sys

logging.disable(50)
KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app")
sys.path.insert(0, KOK)
from engine.transliterator import transliterate_text as T  # noqa: E402

DURUMLAR = [('özellikle', 'اوزللكله'), ('genellikle', 'كنللكله'), ('kolaylıkla', 'قولایلقله'), ('kişiyim', 'كیشی یم'), ('kararlıyım', 'قرارلی یم'), ('giyim', 'كیییم'), ('bilemem', 'بیله\u200cمم'), ('söyleyemem', 'سویله\u200cیه\u200cمم'), ('istemem', 'ایسته\u200cمم'), ('duyarsın', 'دویارسڭ'), ('ulaşırsın', 'اولاشیرسڭ'), ('geçirsin', 'كچیرسین'), ('versin', 'ویرسین'), ('olmaksızın', 'اولمقسزین'), ('gelmeksizin', 'كلمكسزین'), ('attın', 'آتدڭ'), ('uçtun', 'اوچدڭ'), ('etmiştin', 'ایتمشدڭ'), ('ziftin', 'زفتڭ'), ('önceki', 'اوڭجه\u200cكی'), ('öncekiler', 'اوڭجه\u200cكیلر'), ('yönelik', 'یوڭلیك'), ('benziyorsun', 'بڭزه\u200cیورسڭ'), ('benziyordu', 'بڭزه\u200cیوردی'), ('benzin', 'بنزین'), ('men etti', 'منع ایتدی'), ('men', 'من')]


def main():
    kalan = 0
    for latin, beklenen in DURUMLAR:
        cikan = T(latin).strip()
        if cikan != beklenen:
            kalan += 1
            print("KALDI", latin, "->", cikan, "(beklenen", beklenen + ")")
    yol = os.path.join(KOK, "data", "kitap_sozlugu.tsv")
    bolum = False
    for satir in open(yol, encoding="utf-8"):
        if satir.startswith("# Tur S"):
            bolum = True
            continue
        if not bolum or satir.startswith("#") or not satir.strip():
            continue
        latin, yazim = satir.rstrip("\n").split("\t")[:2]
        cikan = T(latin).strip()
        if cikan.replace("\u0651", "") != yazim.replace("\u0651", ""):
            kalan += 1
            print("KALDI (sozluk)", latin, "->", cikan, "(beklenen", yazim + ")")
    print("SONUC: HEPSI GECTI" if not kalan else "SONUC: %d TEST KALDI" % kalan)


if __name__ == "__main__":
    main()
