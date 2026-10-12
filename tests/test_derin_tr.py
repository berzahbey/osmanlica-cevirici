"""Tur 1b+3 (12 Ekim; v2: unsuzden sonra -ımız/-ınız/-ını/-ına bitismeyen harften sonra ی, Hayrat sayimi): Hayrat koken etiketi (kork قورق Turkce) ve derin kokte Hayrat'taki Turkce kok (yurt + ları+nız+dan).
Cogul + -ınız/-ımız Hayrat'ta لریڭز/لریمز (655/1003 kez, لرڭز/لرمز hic yok). Kod klasorunde:
  docker run --rm -v "$PWD":/k -w /k berzahbey/osmanlica-cevirici:latest python tests/test_derin_tr.py"""
import os, sys, csv
KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(KOK, "app"))
import logging
logging.disable(logging.CRITICAL)
from engine.transliterator import transliterate_text as T
from engine.koken import turkce_mi

DURUMLAR = [
    # duzelenler
    ("yurtlarınızdan", "یورتلریڭزدن"), ("başlarınızı", "باشلریڭزی"), ("günahlarınızdan", "كناهلریڭزدن"),
    ("âyetlerimizi", "آیتلریمزی"), ("gönderdiklerinize", "كوندردكلریڭزه"), ("yaratanınıza", "یارادانڭزه"),
    ("gireceğinizi", "كیره‌جكڭزی"), ("içindekini", "ایچنده‌كینی"), ("yanındakini", "یاننده‌كینی"),
    ("kavuşacağımı", "قاووشاجغمی"),
    # eskisi dogru olup degismemesi gerekenler
    ("edinsin", "ایدینسین"), ("gördüğünde", "كوردیكنده"), ("hayvanlarınızın", "حیوانلریڭزڭ"),
    ("ilahlarınızı", "الهلریڭزی"), ("kızlarınızı", "قیزلریڭزی"), ("toprağımızı", "طوپراغمزی"),
    ("yakınlarınız", "یاقینلریڭز"), ("ağacına", "آغاجنه"), ("kalbiniz", "قلبڭز"),
    # v2 (12 Ekim, sunucu olcumu 1'den sonra): bitismeyen harf kurali, iyelik koku, M1 cift ه
    ("varlığının", "وارلغنڭ"), ("dilimize", "دیلمزه"), ("delilimiz", "دلیلمز"), ("kararınızı", "قراریڭزی"),
    ("senedimiz", "سندیمز"), ("kapımız", "قاپومز"), ("köyümüz", "كویمز"), ("çayımız", "چایمز"),
    ("kararını", "قرارینی"), ("yiyeceğin", "یییه‌جكڭ"), ("bilgimiz", "بیلكمز"), ("yokluğunun", "یوقلغنڭ"),
    ("hayvanlarınızın", "حیوانلریڭزڭ"), ("ilahlarınızı", "الهلریڭزی"), ("miskini", "مسكینی"), ("kadının", "قادینڭ"),
]
KOKEN = [("kork", "قورق", True), ("toplu", "طوپلی", True), ("sağlam", "صاغلام", True), ("kadın", "قادین", True),
         ("kader", "قدر", False), ("kayıt", "قید", False), ("tavır", "طور", False), ("sabık", "سابق", False),
         ("lokma", "لقمه", False), ("peygamber", "پیغمبر", False), ("kalb", "قلب", False), ("nakkaş", "نقّاش", False)]
kalan = 0
for girdi, bek in DURUMLAR:
    c = T(girdi)
    ok = c == bek
    print("GECTI" if ok else "KALDI", girdi, "->", c, "" if ok else f"(beklenen {bek})")
    kalan += not ok
for l, o, bek in KOKEN:
    ok = turkce_mi(l, o) == bek
    print("GECTI" if ok else "KALDI", "koken", l, o, "Turkce" if bek else "Arapca")
    kalan += not ok
# hayrat.tsv'de duzeltme yapilmis olmali (kork tr)
hy = {r[0]: r[2] for r in csv.reader(open(os.path.join(KOK, "app", "data", "hayrat.tsv"), encoding="utf-8"), delimiter="\t") if len(r) >= 3}
ok = hy.get("kork") == "tr" and hy.get("toplu") == "tr"
print("GECTI" if ok else "KALDI", "hayrat.tsv koken duzeltmesi (kork, toplu tr)")
kalan += not ok
print("SONUC:", "HEPSI GECTI" if not kalan else f"{kalan} TEST KALDI")
sys.exit(1 if kalan else 0)
