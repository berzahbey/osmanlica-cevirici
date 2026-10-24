"""Kök sözlüğü turu (12 Ekim): data/hayrat_kok.tsv + engine/kok.py.
Düzelenler: kural motoru kökü harf harf yazıyordu, şimdi kök sözlüğündeki (Hayrat) yazımla.
Korunanlar: yanlış kök seçilmemeli (ata+cağız, asıl+dı, dile+k, der+gi, içim+iz, dilim+ize, aşır+ı).
Çalıştırma: docker run --rm -v "$PWD":/k -w /k berzahbey/osmanlica-cevirici:latest python tests/test_kok.py"""
import logging
import os
import sys

logging.disable(50)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app"))
from engine.transliterator import transliterate_text as T  # noqa: E402

ZW = "\u200c"
DURUMLAR = [
    # düzelen (beklenen = Hayrat)
    ("hatırlattıran", "خاطرلاتدیران"), ("duyduk", "دویدق"), ("yediren", "ییدیرن"), ("birleştik", "برلشدك"),
    ("bulundurmuştur", "بولوندیرمشدر"), ("ihtiyarlandıran", "اختیارلاندیران"), ("tarihimizde", "تاریخمزده"),
    ("binmişsiniz", "بینمشسڭز"), ("ehemmiyetleştirir", "اهمّیتلشدیرر"), ("benzetirler", "بڭزتیرلر"),
    ("kelimem", "كلمه‌م"), ("esirgememeli", "اسیركه‌مه‌ملی"), ("kararlaştırır", "قرارلاشدیرر"), ("söndürdük", "سوندیردك"),
    ("benzedi", "بڭزه‌دی"), ("beslediğim", "بسله‌دیكم"), ("anlamıştık", "آڭلامشدق"), ("gizleyemezler", "كیزله‌یه‌مزلر"),
    # korunan (eski çıktı doğruydu)
    ("aşırı", "آشیری"), ("kapanarak", "قاپانارق"), ("kasırga", "قاصیرغه"), ("dilimize", "دیلمزه"), ("içimiz", "ایچمز"),
    ("atacağız", "آتاجغز"), ("asıldı", "آصیلدی"), ("dilek", "دیلك"), ("demet", "دمت"), ("gülerken", "كولركن"),
    ("dalarken", "طالاركن"), ("bekler", "بكلر"), ("benzetip", "بڭزتوب"),
    # sunucu ölçümü 1'de bozulan (12 Ekim): ottoman_dict anlam karşılığı, uzun kökün başı, -lık, -yan fiil eki
    ("oysaki", "اویساكی"), ("hamam", "حمام"), ("ortamda", "اورتامده"), ("karşılığında", "قارشیلیغنده"), ("yarayan", "یارایان"),
    # uzun kök engeli fiilde uygulanmaz
    ("anlamıştık", "آڭلامشدق"), ("işleme", "ایشله‌مه"),
    # sunucu ölçümü 2'de bozulan: isim kökü fiil çekiminde (yara+dılan, yara+nan, asıl+ır)
    ("yaradılan", "یارادیلان"), ("yaranan", "یارانان"), ("asılır", "آصیلیر"),
    # sunucu ölçümü 3: ünlüyle biten isim + 2. tekil iyelik -n (ڭ), -ncı
    ("elbisen", "البسه‌ڭ"), ("sermayen", "سرمایه‌ڭ"), ("annenle", "آننه‌ڭله"), ("birinci", "برنجی"), ("bilginler", "بیلكینلر"),
    # sunucu ölçümü 4: kök+n gerçek kelime (oran, safran); ilk kök tutmazsa sıradaki (hizmetçi -> hizmet)
    ("oranla", "اورانله"), ("safran", "زعفران"), ("hizmetçin", "خدمتچڭ"),
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
