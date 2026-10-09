"""İmlâ turu 12 (Âlemlerin Sırrı, İmam Gazâlî) gerileme testi. Kod klasöründe:
  docker run --rm -v "$PWD":/k -w /k berzahbey/osmanlica-cevirici:latest python tests/test_imla12.py"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app"))
import logging
logging.disable(logging.CRITICAL)
from engine.transliterator import transliterate_text


def cevir(s):
    return transliterate_text(s)


ORNEK = [
    # bozuk / yanlış anlamlı sözlük kayıtları
    ("Rahman ve Rahim Olan Allah'ın Adı ile başlarım.", "رحمان و رحیم اولان اللّهڭ آدی ایله باشلارم."),
    ("Alemlerin Sırrı", "عالملرڭ سرّی"),
    ("bir hadis meali", "بر حدیث مألی"),
    ("etme! dikkat etmelisin", "ایتمه! دقّت ایتمهلیسڭ"),
    ("Değerli şair", "دكرلی شاعر"),
    ("İmamı Gezâlî", "امامی غزالی"),
    ("atına bakar", "آتنه باقار"),
    ("Bakare sûresi", "بقره سوره‌سی"),
    ("kıralın", "قرالڭ"),
    ("kâh", "كاه"),
    # bağlam: "et" emir, "bin" sayı, cümle sonundaki "başlar"
    ("Esbaba tevessül et!", "اسبابه توسّل ایت!"),
    ("Kızarmış et yedi.", "قیزارمش ات یدی."),
    ("Ali bin Ebu Talip", "علی بن ابو طالب"),
    ("kırk bin koyun", "قرق بیڭ قویون"),
    ("esmeye başlar.", "اسمكه باشلار."),
    ("başlarına", None),
    # dua ibareleri
    ("Resulullah sellellahu aleyhi ve sellem dedi.", "رسول الله صلّی الله علیه وسلّم دیدی."),
    ("Mustafa Sallallahu aleyhi ve sellem'in kıblesi", "مصطفی صلّی الله علیه وسلّمڭ قبلهسی"),
    ("Vellahu âlem.", "والله اعلم."),
    ("Yarabbi", "یا ربّی"),
    # OCR'ın düşürdüğü İ ve Irak/ırak
    ("Ibrahim aleyhisselâm", "ابراهیم علیه السلام"),
    ("Islâma olan hücumlar", "اسلامه اولان هجوملر"),
    ("Iyi pişmemiş ekmek", "ایی پیشمهمش اكمك"),
    ("Islâk yünden", None),
    ("Irak valisi", "عراق والیسی"),
    ("gözden ırak", "كوزدن ایراق"),
    # kural motoru: -lerin/-ların ilgi eki
    ("valilerin", "والیلرڭ"),
    ("tatlıların", "طاتلیلرڭ"),
]
kalan = 0
for latin, beklenen in ORNEK:
    sonuc = cevir(latin)
    if beklenen is None:          # yalnız bozulmadığına bakılır: önceki yazımla aynı kalmalı (aşağıda)
        print("BILGI", latin, "->", sonuc)
        continue
    if sonuc.replace("\u200c", "") == beklenen.replace("\u200c", ""):   # ara boşluk (ZWNJ) yalnız görünüş
        print("GECTI", latin, sonuc)
    else:
        kalan += 1
        print("KALDI", latin, "\n   beklenen:", beklenen, "\n   bulunan :", sonuc)
# değişmemesi gerekenler (önceki turların yazımı)
for latin, beklenen in [("başlarına", "باشلرینه"), ("Islâk", "اسلاق")]:
    sonuc = cevir(latin)
    if sonuc.startswith(beklenen[:4]) and "باشلار" not in sonuc and "اسلاك" != sonuc:
        print("GECTI", latin, sonuc)
    else:
        kalan += 1
        print("KALDI", latin, "\n   beklenen:", beklenen, "\n   bulunan :", sonuc)
print("SONUC: HEPSI GECTI" if not kalan else "SONUC: %d TEST KALDI" % kalan)
