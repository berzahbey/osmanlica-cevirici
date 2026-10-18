# -*- coding: utf-8 -*-
"""Tur N (9 kitap + Usûl-i İctihâd): yazım varyantları (müspet ~ müsbet, içtihat ~ içtihad), çift y (fıkhiyye, şer'iyye, cemiyyet),
dişil -iyye (esâsiyye اساسیه), nisbe -î ve çoğul -în/-ûn, Latin harfli harf-i tarif (bilhak بالحق), sondaki kesme ayın (men' منع، vâzı'-ı şerîat),
-In ile biten kök (bilgin بیلكین), sözlükte bozuk kayıtlar (tâze تازه), Türkçe kelimeler korunur (sapık، kaplasın، kazıp، bakarsın)."""
import os, sys, logging
logging.disable(logging.CRITICAL)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app"))
from engine.transliterator import transliterate_text as tt

DURUMLAR = [
    # yazım varyantı
    ("müspet", "مثبت"), ("içtihat", "اجتهاد"), ("içtihatları", "اجتهادلری"), ("mukayyet", "مقیّد"), ("istibdat", "استبداد"), ("tasvip", "تصویب"),
    ("rakip", "رقیب"), ("Halep", "حلب"), ("zümrüt", "زمرد"), ("Lukman", "لقمان"),
    # çift y ve dişil -iyye
    ("fıkhiyye", "فقهیه"), ("fıkhiyyeye", "فقهیه‌یه"), ("şer'iyye", "شرعیه"), ("ahkâm-ı şer'iyyeyi", "احكام شرعیه‌یی"), ("cemiyyet", "جمعیت"),
    ("esâsiyye", "اساسیه"), ("külliyye", "كلّیه"), ("fer'iyye", "فرعیه"), ("Şâfi'iyye", "شافعیه"), ("keyfiyyeten", "كیفیّتًا"),
    # nisbe ve çoğul
    ("fıkhî", "فقهی"), ("kıyâs-ı fıkhî", "قیاس فقهی"), ("müctehidîn", "مجتهدین"), ("sâlikîn", "سالكین"), ("Sahnûn", "سحنون"),
    # harf-i tarif
    ("bilhak", "بالحقّ"), ("bilaraz", "بالعرض"), ("bittakdir", "بالتقدیر"), ("bilistişare", "بالاستشاره"), ("bilmedin", "بیلمدڭ"),
    # sondaki kesme
    ("men' ve tahrîm", "منع و تحریم"), ("Vâzı'-ı şerîat", "واضع شریعت"), ("der'-i mefâsid", "درء مفاسد"), ("vaz' etti", "وضع ایتدی"),
    # -In kökler
    ("bilgin", "بیلكین"), ("seçkin", "سچكین"), ("olgun", "اولغون"), ("ilkin", "ایلكین"), ("evin", "اوڭ"), ("gücün", "كوجڭ"),
    # bozuk sözlük kayıtları ve tek tek
    ("hayât-ı tâze", "حیات تازه"), ("mansûsa", "منصوصه"), ("Cüneyd", "جنید"), ("menafi", "منافع"), ("mutahassıs", "متخصّص"),
    ("icabeder", "ایجاب ایدر"), ("Âdem'de", "آدمده"), ("Hasbiyallah", "حسبی الله"),
    # Türkçe kelimeler varyanta düşmez
    ("sapık", "صاپیق"), ("kaplasın", "قاپلاسین"), ("kazıp", "قازوب"), ("bakarsın", "باقارسڭ"), ("tepkiye", "تپكی یه"), ("somut", "صوموت"), ("Kursî", "قرسی"),
    # Tur N2: sondaki kesme yanlış eşleşmeleri ve dişil nisbe -iye
    ("tabi’ tutulmuştur", "تابع طوتولمشدر"), ("şâyan-ı istima’ değildir", "شایان استماع دكلدر"), ("bu ittihad-ı şeri’", "بو اتّحاد شرعی"),
    ("celb-ül menafi’", "جلب المنافع"), ("meyl-üt tevsi’", "میل التوسیع"), ("kal’ ve ref’", "قلع و رفع"), ("bey' akdi", "بیع عقدی"),
    ("menafi’-i şahsiye", "منافع شخصیه"), ("hürriyet-i şahsiye", "حرّیت شخصیه"), ("esasiye", "اساسیه"), ("tarihiye", "تاریخیه"),
    ("şimdiye", "شیمدی یه"), ("terakkiye", "ترقّی یه"), ("araziye", "اراضی یه"), ("ciddiye", "جدّی یه"), ("birinciye", "برنجی یه"), ("hakîkîye", "حقیقی یه"),
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
