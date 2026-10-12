# -*- coding: utf-8 -*-
"""Hayrat sozlugundeki koken etiketini duzeltir: yalniz harfe bakilarak "ar" denmis Turkce kelimeler (kork قورق، toplu طوپلی) "tr" olur.
Kural app/engine/koken.py'de (hayrat_sozluk_uret.py de onu kullanir). Yalniz 3. sutun degisir, satir sirasi ve geri kalan aynen kalir.
Tekrar calistirilabilir (ikinci calistirmada 0 degisir).
Kullanim (kod klasorunde): python tools/hayrat_koken_duzelt.py app/data/hayrat.tsv [degisen_listesi.tsv]"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app"))
from engine.koken import turkce_mi, isaretli_ikizler

yol = sys.argv[1] if len(sys.argv) > 1 else "app/data/hayrat.tsv"
satirlar = open(yol, encoding="utf-8").read().split("\n")
kayitlar = [s.split("\t") for s in satirlar]
ikiz = isaretli_ikizler([(p[0], p[1]) for p in kayitlar if len(p) >= 3 and not p[0].startswith("#")])
degisen = []
for i, p in enumerate(kayitlar):
    if len(p) == 3 and not p[0].startswith("#") and p[2] == "ar" and turkce_mi(p[0], p[1], p[0] in ikiz):
        satirlar[i] = p[0] + "\t" + p[1] + "\ttr"
        degisen.append(p[0] + "\t" + p[1])
if degisen:
    with open(yol, "w", encoding="utf-8") as f:
        f.write("\n".join(satirlar))
if len(sys.argv) > 2:
    with open(sys.argv[2], "w", encoding="utf-8") as f:
        f.write("\n".join(degisen) + "\n")
print("KOKEN DUZELTME:", yol, "ar -> tr:", len(degisen))
