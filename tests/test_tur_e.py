"""Tur E/F/G (13 Ekim): kitap raporlarından — sözlükteki çok yazımlı kayıt (kerahet) ve ikileme değeri (yavaş), şapkası düşmüş
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
    # Tur F (Bakara okuma listesi): mastar + -nız, -ğiniz (gaf), ünsüzle biten Arapça isim + -ınız, a/e ile biten isim + -sine
    ("almanız", "آلمه‌ڭز"), ("tutmanız", "طوتمه‌ڭز"), ("isteğinizi", "ایسته‌كڭزی"), ("belirlediğinizin", "بلیرلدیكڭزڭ"),
    ("devletiniz", "دولتڭز"), ("yaratanınız", "یارادانڭز"), ("öfkesine", "اوفكه‌سنه"), ("perdesinden", "پرده‌سندن"),
    ("Birçoğunu", "بر چوغنی"), ("Sâbiîler", "صابئیلر"), ("Râinâ", "راعنا"),
    # Tur G (Asâ-yı Mûsâ karşılaştırması): bitişik sayılar, -iye sıfatı, -âne, -stan, elifle biten Arapça kök + ek, sözlük kayıtları
    ("onbir", "اون بر"), ("Yirmiikinci", "یكرمی ایكنجی"), ("binüçyüz", "بیڭ اوچ یوز"), ("hikmet-i umumîye", "حكمت عمومیه"), ("kudret-i İlahîye", "قدرت الهیّه"), ("maksad-ı hakîkîye", "مقصد حقیقی یه"),
    ("mürîdane", "مریدانه"), ("bostan", "بوستان"), ("mezaristan", "مزارستان"), ("şahane", "شاهانه"), ("semasını", "سماسنی"),
    ("Zülkemal", "ذو الكمال"), ("billah", "باللّه"), ("ülemanın", "علمانڭ"), ("hakikaten", "حقیقتا"),
    # korunan
    ("terakkîye", "ترقّی یه"), ("birinci", "برنجی"), ("onun", "اونڭ"), ("binlerce", "بیڭلرجه"), ("insane", "انسانه"), ("uzaktan", "اوزاقدن"),
    ("hapishane", "حبس خانه"), ("kahvehane", "قهوه‌خانه"), ("duasını", "دعاسنی"),
    # Tur G2 (rapor_g1): birbir- sayi degil, bilesik fiil kuyrugunda ZWNJ, fiil + -mA + -sI, a'ma
    ("birbirin", "بربرڭ"), ("birbir", "بربر"), ("birbirine", "بربرینه"), ("hapsetmemek", "حپس ایتمه\u200cمك"), ("hapsedilmeyi", "حپس ایدیلمه\u200cیی"),
    ("zikretmemek", "ذكر ایتمه\u200cمك"), ("yağmasını", "یاغمه\u200cسنی"), ("yağması", "یاغمه\u200cسی"), ("yağmanın", "یغمانڭ"), ("amaları", "اعمالری"),
    ("esmasını", "اسماسنی"), ("onbir", "اون بر"), ("binbir", "بیڭ بر"),
    ("bırakmasın", "بیراقماسین"), ("tutmasın", "طوتماسین"), ("bırakmasınlar", "بیراقماسینلر"), ("bırakması", "بیراقمه\u200cسی"),
    ("cihadınız", "جهادیڭز"), ("dostunuz", "دوستیڭز"), ("kapınız", "قاپوڭز"), ("giymesine", "كییمسنه"), ("olmanız", "اولمه‌ڭز"),
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
