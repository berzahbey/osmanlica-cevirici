# -*- coding: utf-8 -*-
"""Bağlam kuralları (app/data/baglam_kurallari.tsv): komşu kelimeye göre yazım. Çalıştırma: python tests/test_baglam_kural.py"""
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))
import logging
logging.disable(logging.CRITICAL)
import engine.transliterator as T
t = T.transliterate_text


def n(s):
    return re.sub("[\u064b-\u065f\u0670\u200c]", "", s).replace("\u06d5", "\u0647")


hata = 0
if not T._BK:
    print("HATA: bağlam kuralları yüklenmedi (app/data/baglam_kurallari.tsv)"); hata += 1
# (Türkçe, içinde geçmesi gereken, içinde geçmemesi gereken)
BEKLENEN = [
    ("Bunu sevgili üstâdıma arz ettiğim gibi", "عرض", "ارض"),
    ("farklılık arz eder.", "عرض", "ارض"),
    ("ve şükran arz et.", "عرض ایت", "ات."),
    ("arz ve semâ", "ارض", "عرض"),
    ("arz etrafında döner", "ارض", "عرض"),
    ("Şu hakîkati arza ictisâr ediyorum.", "عرضه", "ارضه"),
    ("mesafeyi kat eden", "قطع", "قات"),
    ("bir kat daha", "قات", "قطع"),
    ("cem‘iyetleri bel etti", "بلع", None),
    ("yine bel bağlıyoruz", "بل باغ", "بلع"),
    ("hedm ve kal edip", "قلع", None),
    ("misâfir kal otağda", "قال", "قلع"),
    ("rezîl nefse inkılâb etmişler mesh olmuşlar", "مسخ", "مسح"),
    ("mübârek eli ile mesh etti", "مسح", "مسخ"),
    ("mudgadan azm ve lahme", "عظم", "عزم"),
    ("sarsılmaz bir azm ile", "عزم", "عظم"),
    ("esîr maddesi üzerinde", "اثیر", "اسیر"),
    ("ruslara esîr düşmüştür", "اسیر", "اثیر"),
    ("avâm ve havâs", "خواص", "حواس"),
    ("havâs ve hissiyât", "حواس", "خواص"),
    ("Sevr muâhedesiyle", "سور", "ثور"),
    ("Sevr ve Hût melekleri", "ثور", None),
    ("kumandan arş emri ile", "آرش", "عرش"),
    ("Arş ve kürsî", "عرش", "آرش"),
    ("bir hisse mâlik değillerdir", "حسّه", "حصّه"),
    ("kıssadan hisse almak", "حصّه", "حسّه"),
    ("etrafında halka tutan", "حلقه", "خلقه"),
    ("halka karşı vaziyetleri", "خلقه", "حلقه"),
    ("dehşetli karın sancısı", "قارین", None),
    ("o karın üstünde", "قارڭ", "قارین"),
    ("kara ve deniz", "قاره", None),
    ("kalbi kara oldu", "قره", "قاره"),
    ("altından ve gümüşten kaplar", "آلتوندن", None),
    ("ağlama gül", "كول", None),
    ("bir gül bahçesi", "كل", "كول"),
]
for latin, var, yok in BEKLENEN:
    c = n(t(latin))
    if var and n(var) not in c:
        print("HATA:", latin, "->", c, "| olmalı:", var); hata += 1
    if yok and n(yok) in c:
        print("HATA:", latin, "->", c, "| olmamalı:", yok); hata += 1
# kural dışı metin aynen eskisi (katman yalnız kural tutan kelimeye dokunur)
for latin in ["Kızarmış et yedi.", "Buna dikkat et ve tefekkür et.", "De ki: O Allah birdir.", "senin başına", "Risâle-i Nûr",
              "Bu da‘vâ doğrudur.", "nübüvvet-i mutlaka", "1911 senesinde"]:
    if t(latin) != T._transliterate_text_kuralsiz(latin):
        print("HATA: kural katmanı kural dışı metni değiştirdi:", latin); hata += 1
print("SONUC: HEPSI GECTI" if not hata else f"SONUC: {hata} HATA")
