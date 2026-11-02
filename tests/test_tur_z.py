"""Tur Z (2 Kasım 2026, Hayrat verisiyle): ayrık ek Arap harfli kelimeden/tırnaktan sonra Osmanlıca ek biçimiyle ve ayrı yazılır (Hayrat); Sebîl’ür- = Sebîlü’r-;
cümle içi sıra sayısı rakam + نجی (Hayrat cümle içinde 75'te 74); satır başı, tarih ve cümle sonundaki yıl dokunulmaz.
Calistirma: docker run --rm -v "$PWD":/k -w /k berzahbey/osmanlica-cevirici:latest python tests/test_tur_z.py"""
import logging
import os
import sys

logging.disable(50)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app"))
from engine.transliterator import transliterate_text as T  # noqa: E402

D = [("bu قُلْ ün esası", "بو قُلْ ڭ اساسی"), ("اُولٰٓئِكَ nin tekrarı", "اُولٰٓئِكَ نڭ تكراری"), ("اِسْتَوٰی ye bağlı", "اِسْتَوٰی یه باغلی"), ("بِسْمِ اللّٰهِ den", "بِسْمِ اللّٰهِ دن"), ("Sebîl’ür-Reşâd’a yazdı", "سبیل الرّشاده یازدی"),
     ("olan 163. maddeye ek", "اولان ١٦٣ نجی مادّه‌یه اك"), ("ve 29. Mektûb’un altın", "و ٢٩ نجی مكتوبڭ آلتون"),
     ("Târîh : 27. 05. 1950 Sâat", "تاریخ : ٢٧. ٠٥. ١٩٥٠ ساعت"), ("1. Nota : bu", "١. نوطه : بو"),
     ("yılında 1950. Sonra geldi", "ییلنده ١٩٥٠. صوڭره كلدی"), ("İşte بِسْمِ اللّٰهِ deki", "ایشته بِسْمِ اللّٰهِ ده‌كی")]


def main():
    kalan = 0
    for a, b in D:
        c = T(a).strip()
        if c != b:
            kalan += 1
            print("KALDI", a, "->", c, "(beklenen", b + ")")
    print("SONUC:", "HEPSI GECTI" if not kalan else f"{kalan} TEST KALDI")


main()
