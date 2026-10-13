"""Hayrat'taki ek parcasi kayitlari (in -> ڭ, ün -> ڭ, tan -> دن) kelime sayilmaz; tirnaktan sonraki ek yine ek yazilir. Kod klasorunde:
  docker run --rm -v "$PWD":/k -w /k berzahbey/osmanlica-cevirici:latest python tests/test_ek_parcasi.py"""
import os, sys
KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(KOK, "app"))
import logging
logging.disable(logging.CRITICAL)
from engine.transliterator import transliterate_text as T

DURUMLAR = [
    # (girdi, beklenen) ya da (girdi, (tur, deger)): tur basi / icerir / degil
    ("in", "این"),
    ("inin", ("basi", "این")),          # -in emir eki ayri turda (Hayrat ڭ): burada yalniz kok
    ("ün", "اون"),
    ("ünlü", ("basi", "اون")),
    ("ünü", ("basi", "اون")),
    ("tan", ("degil", "دن")),            # Tan yeri: dogru yazim (طاڭ) ayri turda sozluge
    ("“Hak”tan geldi.", "\"حقّ\"دن كلدی."),
    ("“Allah”ın emri.", "\"الله\"ڭ امری."),
    ("“Kur’an”dan okudu.", "\"قرآن\"دن اوقودی."),
    ("“Mesnevî”nin şerhi.", "\"مثنوی\"نڭ شرحی."),
    ("Allah'ın", "اللّهڭ"),
    ("Kur'an'dan", "قرآندن"),
    ("Ahmet'ten", "احمددن"),
    ("Musa'nın", "موسینڭ"),
    # ayri dusmus ek (11 Ekim olcumu: eskiden Hayrat'in ek parcasi kayidina tesadufen dogru dusuyordu)
    ("Rasulullah (sav)'ın sünneti", ("icerir", ")ڭ ")),
    ("Allah (C.C.)'ın emri", ("icerir", ")ڭ ")),
    ("Onlar (filozoflar) ın zikri", ("icerir", ") ڭ ")),
    ("düşenler(in hâli)", ("icerir", "(ڭ ")),
    ("Allah'- tan korkarsa", ("icerir", " دن ")),
    ("saltanat (ın)a", ("icerir", "(ڭ)ه")),
    ("Eyyühe'l-veled'in", ("icerir", "الولدڭ")),
    ("İbn-î Sinâ", ("icerir", " ی ")),
    ("Bir şehre (mısran) inin,", ("icerir", " اینڭ")),   # fiil: ek sayilmaz; Tur C: emir -in ڭ (Hayrat: girin كیرڭ)
    ("Hepiniz oradan inin!", ("icerir", " اینڭ")),
    ("Gökten in!", ("icerir", " این!")),
    # 2. olcumde cikan asiri genislik: bunlar ek DEGIL (12 Ekim)
    ("Bir kağıda veya erkeğin (ya da zekerin)", ("icerir", "(یا ده")),
    ("(Ya Muhammed!)", ("icerir", "(یا ")),
    ("(güç) ya irâde veya", ("icerir", ") یا ")),
    ("vara' ile arındırılmış", ("icerir", " ایله ")),
    ("cem' eden", ("icerir", " ایدن")),
    ("['İleride sakıncalı", ("icerir", "[ایلریده")),
    ("'La havle", ("icerir", "لا ")),
    ("velinimetim' türünden", ("icerir", " تورندن")),
    ("(Nun 71/5)", ("icerir", "(نون")),
    ("Rasulullah (sav)'tan rivayet", ("icerir", ")دن ")),
    ("Melik-i mutlak O'- dur", ("icerir", " در")),
    ("Allah teâlâ' ya karşı", ("icerir", " یه ")),
    ("tanımında", "طانیمنده"),                           # eskiden tan (دن) + ımında
    ("tanıma", "طانیمه"),
]
kalan = 0
for girdi, bek in DURUMLAR:
    c = T(girdi)
    if isinstance(bek, tuple):
        tur, deger = bek
        ok = c.startswith(deger) if tur == "basi" else (deger in c) if tur == "icerir" else c != deger
    else:
        ok = c == bek
    print("GECTI" if ok else "KALDI", girdi, "->", c, "" if ok else f"(beklenen {bek})")
    kalan += not ok
print("SONUC:", "HEPSI GECTI" if not kalan else f"{kalan} TEST KALDI")
sys.exit(1 if kalan else 0)
