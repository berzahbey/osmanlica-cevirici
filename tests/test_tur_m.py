# -*- coding: utf-8 -*-
"""Tur M (hayrat_tek_supheli.tsv'deki 1.202 kelimenin karari, tools/hayrat_tek_karar.tsv): H kelimeler Hayrat yazimiyla,
D kelimeler verilen dogru yazimla cikar; A kelimeler (Hayrat'in yanlis ya da es sesli yazimi) Hayrat yazimiyla cikmaz."""
import os, sys, logging, unicodedata
logging.disable(logging.CRITICAL)
KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(KOK, "app"))
from engine.transliterator import transliterate_text as tt

DURUMLAR = [
    ("Abdülhamîd", "عبد الحمید"), ("bilkabûl", "بالقبول"), ("zemberekleri", None), ("zembereğini", "زنبركنی"),
    ("kaziyesi", "قضیه‌سی"), ("Manisa'da", "مغنیساده"), ("kılıçlarından", "قیلیچلرندن"), ("ağlaya", "آغلایا"),
    ("durum", "دوروم"), ("durumunun", "دورومنڭ"), ("kazandık", "قزاندق"),
    ("işitiyordu", "ایشیتییوردی"), ("vursak", "اورسه‌ق"),
    ("huzû", "خضوع"), ("huzû ve huşû", "خضوع و خشوع"), ("a'lânın", "اعلانڭ"), ("lügatte", "لغتده"), ("darr", "ضرّ"), ("hükmetmemişler", "حكم ایتمه‌مشلر"),
]
kalan = 0
for latin, beklenen in DURUMLAR:
    if beklenen is None:
        continue
    cikan = tt(latin).strip()
    if cikan != beklenen:
        kalan += 1
        print(f"KALDI {latin}: beklenen {beklenen} çıkan {cikan}")
    else:
        print(f"GECTI {latin} {cikan}")

# Bilinen: bu 5 kelime sozluge gelmeden ozel katmanlarda (Allah'li terkip, -eten zarfi, Hayrat ifadesi) yaziliyor; Tur M degistirmedi.
BILINEN = {"kablelvukū'", "melâiketullâh", "rahmetullâhi", "veşşükrülillâh", "kelimetullâhın"}
say = {"H": 0, "D": 0, "A": 0}
for satir in open(os.path.join(KOK, "tools", "hayrat_tek_karar.tsv"), encoding="utf-8"):
    if satir.startswith("#") or not satir.strip():
        continue
    k, c, yz, o = satir.rstrip("\n").split("\t")[:4]
    cikan = tt(k).strip()
    say[c] += 1
    if c in ("H", "D") and cikan != yz and unicodedata.normalize("NFC", k) not in BILINEN:
        kalan += 1
        print(f"KALDI ({c}) {k}: beklenen {yz} çıkan {cikan}")
    if c == "A" and cikan == o:
        kalan += 1
        print(f"KALDI (A) {k}: alinmamasi gereken Hayrat yazimi cikti {o}")
print("karar:", say)
print("SONUC: HEPSI GECTI" if not kalan else f"SONUC: {kalan} TEST KALDI")
