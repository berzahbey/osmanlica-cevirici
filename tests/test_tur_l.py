# -*- coding: utf-8 -*-
"""Tur L (Hayrat'in tamami olcumu, 9 kitap denetimi): Hayrat'ta az gecen kelimeler (hayrat_tek.tsv, yalniz tam eslesme),
-eddin adlari, kesmeli ekte ayin ve zamir n'si, Hayrat ifadesinin dis katmanlarda korunmasi, hemzeli -en zarfi,
"-den biri" ayri, Kuran, ov-/dov-/sov-, Hayrat turetilmis anahtar duzeltmeleri, vaz gec- baglam kurali."""
import os, sys, logging
logging.disable(logging.CRITICAL)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app"))
from engine.transliterator import transliterate_text as tt

DURUMLAR = [
    # hayrat_tek: tam eslesme, kok olarak kullanilmaz
    ("hamam", "حمام"), ("aşırı", "آشیری"), ("aşır", "عشر"), ("define", "دفینه"), ("def'ine", "دفعنه"),
    # -eddin adlari
    ("Şemseddin", "شمس الدّین"), ("Şemseddin’in", "شمس الدّینڭ"), ("Celâleddîn-i Rûmî", "جلال الدّین رومی"),
    ("Fahreddin", "فخر الدّین"), ("Alâeddin", "علاء الدّین"), ("Bahâeddin", "بهاء الدّین"), ("reddin", "ردّڭ"),
    # kesmeli ek: zamir n'si (ayin degil), iyelik ی'si
    ("Kastamonu Lâhikası’nda", "قسطمونی لاحقه‌سنده"), ("Nûriyesi’ndeki", "نوریه‌سنده‌كی"), ("Kur’ân-ı Şerîfi’nde", "قرآن شریفنده"),
    ("Meyve Risâlesi’nin kitabı", "میوه رساله‌سنڭ كتابی"), ("Ali’nin", "علینڭ"), ("ma’nâ", "معنا"), ("da’vâ", "دعوا"),
    # ayinla biten kelime + kesmeli ek
    ("nev’in", "نوعڭ"), ("nev’i", "نوعی"), ("kat’ı", "قطعی"), ("bey’i", "بیعی"), ("şer’iyedir", "شرعیه‌در"),
    ("lem’anın", "لمعه‌نڭ"), ("şey’in", "شیئڭ"),
    # Hayrat ifadesi dis katmanlarda bozulmaz
    ("hiss-i kable’l-vukū‘", "حسّ قبل الوقوع"), ("sû’-i isti‘mâl", "سوء استعمال"), ("Allâhü a‘lem", "اللّه اعلم"),
    # hemzeli -en zarfi
    ("iktifâen", "اكتفاء"), ("îmâen", "ایماء"), ("ibtidâen", "ابتداء"), ("zâhiren", "ظاهرا"),
    # -den biri / -den beri
    ("binden biri", "بیڭدن بری"), ("seneden beri gelir, binden biri de", "سنه‌دنبری كلیر، بیڭدن بری ده"), ("o zamandan beri", "او زماندنبری"),
    # Kuran
    ("Kuran", "قرآن"), ("Kuran’da", "قرآنده"), ("devleti kuran", "دولتی قوران"),
    # ov-/dov-/sov-
    ("övmek", "اوكمك"), ("övülmekten", "اوكولمكدن"), ("dövülür", "دوكولور"), ("sövmek", "سوكمك"), ("ödemek", "اوده‌مك"),
    # Hayrat turetilmis anahtar duzeltmeleri, sozluk
    ("sıfatın", "صفتڭ"), ("vakıf", "وقف"), ("yese", "ییسه"), ("ede ede", "ایده ایده"), ("Şâzelî", "شاذلی"), ("Makalat", "مقالات"),
    # baglam: vaz gec-
    ("vaz geçti", "واز كچدی"), ("kanun vaz edildi", "قانون وضع ایدیلدی"),
]

kalan = 0
for latin, beklenen in DURUMLAR:
    cikan = tt(latin)
    if cikan != beklenen:
        kalan += 1
        print(f"KALDI {latin}: beklenen {beklenen} çıkan {cikan}")
    else:
        print(f"GECTI {latin} {cikan}")
print("SONUC: HEPSI GECTI" if not kalan else f"SONUC: {kalan} TEST KALDI")
