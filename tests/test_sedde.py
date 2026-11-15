"""Şedde: kök sonu ikiz ünsüz yalnız ünlü ek gelince yazılır (Hayrat)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
from engine.transliterator import transliterate_text as t

DURUMLAR = [
    ("Hak geldi.", "حق كلدی."), ("hakkı", "حقّی"), ("haktır", "حقدر"), ("hakta", "حقده"),
    ("Rab", "رب"), ("Rableri", "ربلری"), ("Rabbimiz", "ربّمز"), ("tam", "تام"), ("hac", "حج"), ("hacca", "حجّه"),
    ("sır", "سر"), ("şer", "شر"), ("zan", "ظن"), ("mühim", "مهم"), ("Hayy’dır", "حی‌در"),
    ("Hak Teâlâ buyurdu.", "حقّ تعالی بویوردی."), ("cennette", "جنّتده"), ("dikkat", "دقّت"), ("hediye", "هدیّه"),
]
kalan = 0
for latin, beklenen in DURUMLAR:
    cikan = t(latin)
    if cikan == beklenen:
        print("GECTI", latin, cikan)
    else:
        kalan += 1
        print("KALDI", latin, "beklenen", beklenen, "çıkan", cikan)
print("SONUC:", "HEPSI GECTI" if not kalan else f"{kalan} TEST KALDI")
sys.exit(1 if kalan else 0)
