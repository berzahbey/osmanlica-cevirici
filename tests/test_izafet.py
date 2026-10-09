# -*- coding: utf-8 -*-
"""Ünlüyle biten kelimede izafet, hemzeli kelimeler, î + ye/yi ayrı, Osmanlıca rakamlar (Hayrat; Muhakemat karşılaştırması, 9 Ekim).
Çalıştırma: python tests/test_izafet.py"""
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))
from engine.transliterator import transliterate_text as t


def n(s):
    return re.sub("[\u064b-\u065f\u0670\u200c]", "", s).replace("\u06d5", "\u0647")


BEKLENEN = [
    ("istikrâ-i tâmm", "استقرای تام"), ("ulemâ-i sû’", "علمای سوء"), ("îfâ-i hakkında", "ایفای حقنده"),
    ("maânî-i ûlâ", "معانئ اولی"), ("müşterî-i hakîkat", "مشترئ حقیقت"), ("tedennî-i milletten", "تدنئ ملتدن"),
    ("mâ-i hayat", "ماء حیات"), ("verâ-i perde", "وراء پرده"), ("yed-i beyzâ-yı", "ید بیضای"),
    ("mebde’-i evvel", "مبدأ اول"), ("menşe’", "منشأ"), ("sû’-i fehm", "سوء فهم"),
    ("maksad-ı hakîkîye", "مقصد حقیقی یه"), ("hükm-ü zihnîyi", "حكم ذهنی یی"), ("nebîye", "نبی یه"),
    ("Sayfa 12, 1911 yılında", "صحیفه ١٢، ١٩١١ ییلنده"),
    # dokunulmaması gerekenler
    ("nokta-i nazar", "نقطهٔ نظر"), ("Risâle-i Nûr", "رسالهٔ نور"), ("Asâ-yı Mûsâ", "عصای موسی"), ("kalb-i insânî", "قلب انسانی"),
    ("emr-i Rabbânîyle", "امر ربانیله"), ("Talha’ dedi", "طلحه دیدی"), ("cüz’-i ihtiyârî", "جزء اختیاری"),
    ("Kur’an’ın", "قرآنڭ"), ("fıkh-ı ekber", "فقه اكبر"),
    ("Bkz. Essai de Chronologie des oeuvres de al-Ghazali, Paris 1959.", "بقز. Essai de Chronologie des oeuvres de al-Ghazali, Paris 1959."),
]
hata = 0
for latin, osm in BEKLENEN:
    c = t(latin)
    if n(c) != n(osm):
        print("HATA:", latin, "beklenen", osm, "çıkan", c); hata += 1
print("SONUC: HEPSI GECTI" if not hata else f"SONUC: {hata} HATA")
