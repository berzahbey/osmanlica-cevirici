"""Tur AB (22 Kasım 2026, 41 kitap denetimi; İslam Tarihi kaynak notları ağırlıklı): Abd- adları harf-i tarifle (Abdülvehhab عبد الوهّاب),
sh. sahife ص, sözlükte bütün tamlama (İbnü'l-Esîr ابن الاثیر), kesmeli adın kökü kesmesiz yazımla aynı kaynaktan (Kayser'in قیصرڭ),
müellif/yer adları ve merfû -u (Allahu Ekber).
Calistirma: docker run --rm -v "$PWD":/k -w /k berzahbey/osmanlica-cevirici:latest python tests/test_tur_ab.py"""
import logging
import os
import sys

logging.disable(50)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app"))
from engine.transliterator import transliterate_text as T  # noqa: E402

D = [
    # Abd- adları
    ("Abdurrezzak", "عبد الرّزّاق"), ("Abdülvehhab", "عبد الوهّاب"), ("Abdülvehhab'ın", "عبد الوهّابڭ"), ("Abdülkerim", "عبد الكریم"),
    ("Abduşşems", "عبد الشمس"), ("Abdüsselâm", "عبد السلام"), ("Abdulmünzir", "عبد المنذر"), ("Abdürrahman", "عبد الرحمن"),
    ("Abdülhalik", "عبد الخالق"), ("Abdullah", "عبد اللّه"), ("Abdülhamid", "عبد الحمید"),
    ("abdest", "آبدست"), ("Abdal", "آبدال"), ("Abdi", "عبدی"),
    # kaynak notları
    ("sh. 45", "ص ٤٥"), ("Sh. 12", "ص ١٢"), ("c: II, sh: 511", "ج: ٢، ص: ٥١١"), ("s: 45", "ص: ٤٥"), ("Saat: 5", "ساعت: ٥"), ("İbnü'l-Esîr, Üsdü'l-Gâbe", "ابن الاثیر، اسد الغابه"), ("İbn Seyyidinnâs", "ابن سیّد الناس"),
    ("Heysemî", "هیثمی"), ("Belâzurî'nin", "بلاذرینڭ"), ("es-Sîre", "السیره"), ("el-Bidâye ve'n-Nihâye", "البدایه والنهایه"),
    ("Kurtubî", "قرطبی"), ("Ahbâru Mekke", "اخبار مكّه"), ("Allahu Ekber", "اللّه اكبر"), ("Tunus'a", "تونسه"), ("Siyam", "صیام"),
    # kesmeli ad
    ("Kayser'in", "قیصرڭ"), ("Berlin'e", "برلینه"), ("Miskeveyh'in", "مسكویهڭ"), ("Vâil'in", "وائلڭ"),
    ("Vâkıdî'ye", "واقدی یه"), ("Mustafa'ya", "مصطفی یه"), ("Hakk'a", "حقّه"), ("Gazetesi'nin", "غزته‌سنڭ"),
    # Tur AB2 (Hayrat sınavı listesi)
    ("saâdet-i ebediyenin", "سعادت ابدیه‌نڭ"), ("irâde-i külliyenin", "ارادهٔ كلّیه‌نڭ"), ("kanâat-ı kat‘iyemle", "قناعت قطعیّه‌مله"),
    ("hizmet-i Kur’âniyemi", "خدمت قرآنیه‌می"), ("saâdet-i ebediyeme", "سعادت ابدیه‌مه"), ("ebediyyen", "ابدیّا"),
    ("kānûn-u esâsîlerinin", "قانون اساسیلرینڭ"), ("kābil", "قابل"), ("kânûn", "كانون"), ("sıfatına", "صفتنه"), ("sıfata", "صفته"),
    ("kaziye", "قضیه"), ("Mersin", "مرسین"), ("düşersin", "دوشرسڭ"), ("bahaneyi de", "بهانه‌یی ده"), ("kütüphaneyi", "كتابخانه‌یی"),
    ("sıfât-ı seb‘aya", "صفات سبعه‌یه"), ("mâlâ-yaʻnî", "مالایعنی"), ("ma‘tûfun aleyh", "معطوفٌ علیه"), ("müşebbehün bih", "مشبّهٌ به"),
    ("mümesselün leh", "ممثّلٌ له"), ("bunun aleyhinde", "بونڭ علیهنده"), ("arz-ı ihtirâm", "عرض احترام"), ("küre-i arz", "كرهٔ ارض"),
    ("arz-ı mev'ûd", "ارض موعود"), ("Şemsettin", "شمس الدّین"), ("Alaettin", "علاء الدّین"), ("Bahattin", "بهاء الدّین"),
    ("Salahattin", "صلاح الدّین"), ("Muhittin", "محیی الدّین"), ("fethettin", "فتح ایتدڭ"), ("zevâhir-i İslâmiyet", "ظواهر اسلامیّت"),
    ("zü’l-acâib", "ذو العجائب"), ("İbnü’l-Fârıd", "ابن الفارض"), ("Hüseyin Avnî", "حسین عونی"), ("Binâen alâ hâzâ", "بناءً علی هذا"),
    # dokunulmaz
    ("esir aldılar", "اسیر آلدیلر"), ("enderü'l-vukû", "اندر الوقوع"), ("Ebu'l-Kasım", "ابو القاسم"),
]


def main():
    kalan = 0
    for a, b in D:
        c = T(a).strip()
        if c != b:
            kalan += 1
            print("KALDI", a, "->", c, "(beklenen", b + ")")
    print("SONUC:", "HEPSI GECTI" if not kalan else f"{kalan} TEST KALDI")


main()
