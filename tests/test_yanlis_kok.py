"""Yanlış kök turu (13 Ekim): sözlükteki iyelik biçimi (oğlu اوغلی، kolu قولی، boynu بوینی) + n'li/m'li ek kök sanılıyordu
(oğlunu اوغلینی). Kısa kök sözlükte yoksa ama Zemberek'e göre gerçek kökse (kol; oğul/boyun ünlü düşmesiyle), kısa kökün yazımı iyelik
biçiminden ی atılarak alınır, ekler sözlük yolundan yazılır (dictionary._iyelik_kisa). Beklenenler Hayrat'ın yazımı.
Çalıştırma: docker run --rm -v "$PWD":/k -w /k berzahbey/osmanlica-cevirici:latest python tests/test_yanlis_kok.py"""
import logging
import os
import sys

logging.disable(50)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app"))
from engine.transliterator import transliterate_text as T  # noqa: E402

ZW = "‌"
DURUMLAR = [
    # düzelen (beklenen = Hayrat)
    ("oğlunu", "اوغلنی"), ("koluna", "قولنه"), ("boynuna", "بویننه"), ("kolunun", "قولنڭ"), ("ufkuna", "افقنه"),
    ("kazancını", "قزانجنی"), ("karanlığını", "قراڭلغنی"), ("sevincine", "سوینجنه"), ("etrafınızı", "اطرافڭزی"),
    ("kitabınıza", "كتابڭزه"), ("zamanınıza", "زمانڭزه"), ("ümidinizi", "امیدیڭزی"), ("bülbülümüz", "بلبلمز"),
    ("canınızdan", "جانڭزدن"), ("merakınızı", "مراقڭزی"),
    # korunan (eski çıktı doğruydu)
    ("oğluna", "اوغلنه"), ("oğlunuza", "اوغلڭزه"), ("askerimizin", "عسكریمزڭ"), ("dördünün", "دردینڭ"),
    ("tokatından", "طوقاتندن"), ("oğlu", "اوغلی"), ("kolu", "قولی"), ("boynu", "بوینی"), ("kitabını", "كتابنی"),
    ("dilimize", "دیلمزه"), ("varlığınızdan", "وارلغڭزدن"), ("hareketimizin", "حركتمزڭ"),
    # sunucu ölçümü 1'de bozulan (13 Ekim): Arapça -î nisbet (sofi), sözlükteki kök yazımı (bütün بتون)
    ("sofinin", "صوفینڭ"), ("bütününden", "بتونندن"), ("halinizi", "حالڭزی"), ("orucundan", "اوروجندن"),
    # sunucu ölçümü 2: sözlükteki eşsesli kök (tahlil تخلیل، batın بطن، tarik تاریك) değil, Hayrat'ın iyelik biçiminden
    ("tahlilinden", "تحلیلندن"), ("batınının", "باطننڭ"), ("tarikinin", "طریقنڭ"), ("şeyinden", "شیئندن"), ("mensubiyetinden", "منسوبیّتندن"),
]


def main():
    kalan = 0
    for w, beklenen in DURUMLAR:
        c = T(w).strip()
        if c.replace(ZW, "") != beklenen.replace(ZW, ""):
            kalan += 1
            print(f"KALDI {w} -> {c} (beklenen {beklenen})")
    print(f"{len(DURUMLAR)} durum")
    print("SONUC: HEPSI GECTI" if not kalan else f"SONUC: {kalan} TEST KALDI")


if __name__ == "__main__":
    main()
