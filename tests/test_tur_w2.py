"""Tur W2 (2 Kasım 2026): OpenITI yazımı yalnız güçlü Arapça işaretli kelimede (şapka, ünlü arası şedde, aynı iki ünlü, -iye/-iyet).
Kitap listesinden (sunucu ölçümü): OCR'da ş/ğ/ı'sı düşmüş Türkçe ve yabancı adlar değişmemeli; Arapça kelimeler OpenITI yazımıyla.
Calistirma: docker run --rm -v "$PWD":/k -w /k berzahbey/osmanlica-cevirici:latest python tests/test_tur_w2.py"""
import logging
import os
import sys

logging.disable(50)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app"))
from engine.transliterator import transliterate_text as T  # noqa: E402

DOGRU = [("Suyûtî", "سیوطی"), ("lâzim", "لازم"), ("Rabbih", "ربه"), ("Aynî", "عینی"), ("Süheylî", "سهیلی"), ("Medârik", "مدارك"),
         ("menât", "مناط"), ("arizî", "عرضی"), ("nefsaniyet", "نفسانیت"), ("Dârekutnî", "دارقطنی"), ("Sakîfler", "ثقیفلر"),
         ("hâsil", "حاصل"), ("Dineverî", "دینوری"), ("kiraat", "قراءت"), ("Teymiyye", "تیمیه"), ("merfû", "مرفوع"), ("Râgıb", "راغب"),
         ("Tûsî", "طوسی"), ("Bistamî", "بسطامی"), ("Tahâvî", "طحاوی"), ("Sakafî", "ثقفی"), ("Huzâî", "خزاعی"), ("Rabîa", "ربیعه"),
         ("Sümeyye", "سمیه"), ("Rukayye", "رقیه"), ("Affan", "عفان"), ("mebî", "مبیع"), ("Yâküt", "یاقوت"), ("Hammad", "حماد")]
DOKUNMA = ("Muhibbüt yaptigi Hanffe Pierre Beyrut asagidaki berbat bakista yasagin faûlün feûlün Neseff ievâid Patrik Essai "
           "satilmasi sayilan Bakiyy tedirgin musulmane kuzeyde Tezayak yasagi yeniay ticari birakma detaylı tasiyan Megazi "
           "Lapanne devasa Maurice ıssının ıssılık kullanilisi Melâmet Vetâ Dürzîler Ezdî Sellam kafiyesindeki").split()


def main():
    kalan = 0
    for latin, beklenen in DOGRU:
        c = T(latin).strip()
        if c != beklenen:
            kalan += 1
            print("KALDI", latin, "->", c, "(beklenen", beklenen + ")")
    os.environ["OSM_TUR_W"] = "0"
    eski = {w: T(w).strip() for w in DOKUNMA}
    os.environ["OSM_TUR_W"] = "1"
    for w in DOKUNMA:
        c = T(w).strip()
        if c != eski[w]:
            kalan += 1
            print("KALDI (dokunulmamalı)", w, "->", c, "(önce", eski[w] + ")")
    print("SONUC:", "HEPSI GECTI" if not kalan else f"{kalan} TEST KALDI")


main()
