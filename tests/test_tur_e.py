"""Tur E (13 Ekim): kitap raporlarından — sözlükteki çok yazımlı kayıt (kerahet) ve ikileme değeri (yavaş), şapkası düşmüş
"sozlukler" kaydının gölgelediği kelimeler (hane, sahabe, sükut: Hayrat yazımı), orma+nın yerine orman+ın, sözlük kökü + ilgi eki
(evrenin), "b." = ibn, radıyallahu, tek tek düzeltmeler. "korunan"lar bozulmamalı.
Çalıştırma: docker run --rm -v "$PWD":/k -w /k berzahbey/osmanlica-cevirici:latest python tests/test_tur_e.py"""
import logging
import os
import sys

logging.disable(50)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app"))
from engine.transliterator import transliterate_text as T  # noqa: E402

ZW = "‌"
DURUMLAR = [
    ("yavaş", "یاواش"), ("yavaş yavaş", "یاواش یاواش"), ("kana kana", "قانا قانا"), ("kerahet", "كراهت"), ("gazal", "غزال"),
    ("hane", "خانه"), ("sahabe", "صحابه"), ("sükut", "سكوت"), ("efkar", "افكار"), ("nafakanın", "نفقه‌ینڭ"), ("Halik", "خالق"), ("tahlil", "تحلیل"),
    ("ormanın", "اورمانڭ"), ("ormanda", "اورمانده"), ("çevrenin", "چوره‌نڭ"), ("düzeltmenin", "دوزلتمه‌نڭ"), ("Haris", "حارث"), ("evrenin", "اورنڭ"), ("konu", "قونو"), ("ilişkin", "ایلیشكین"),
    ("sânî", "ثانی"), ("mebde", "مبدأ"), ("müstahil", "مستحیل"), ("olmıyan", "اولمیان"),
    ("Ahmed b. Hanbel", "احمد بن حنبل"), ("Ömer radıyallahu anhu", "عمر رضی الله عنه"),
    # korunan
    ("bunun", "بونڭ"), ("onun", "اونڭ"), ("dinin", "دینڭ"), ("babanın", "بابانڭ"), ("dünyanın", "دنیانڭ"), ("devenin", "دوه‌نڭ"),
    ("bakiye", "بقیه"), ("karı", "قاری"), ("su", "صو"), ("pazar", "پازار"), ("Bkz. s. 45", "بقز. س. ٤٥"), ("sonun", "صوڭڭ"),
]


def main():
    kalan = 0
    for w, beklenen in DURUMLAR:
        c = T(w).strip()
        if c.replace(ZW, "") != beklenen.replace(ZW, ""):
            kalan += 1
            print(f"KALDI {w} -> {c} (beklenen {beklenen})")
    print("SONUC: HEPSI GECTI" if not kalan else f"SONUC: {kalan} TEST KALDI")


if __name__ == "__main__":
    main()
