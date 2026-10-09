"""Kur'an mealleri testi (tests/mealler/). Kod klasöründe:
  docker run --rm -v "$PWD":/k -w /k berzahbey/osmanlica-cevirici:latest python tests/test_mealler.py
1) Meallerdeki her kelime Hayrat'ta geçiyorsa çıktı Hayrat'ın yazımıyla aynı olmalı (BILINEN listesindekiler hariç).
2) tests/mealler/osm/<sure>.txt (onaylı Osmanlıca) varsa çıktı ona harfi harfine eşit olmalı (ara boşluk sayılmaz).
3) Bilgi: Hayrat'ta olmayan kelime sayısı."""
import os, sys, re, glob, collections, unicodedata
KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(KOK, "app"))
import logging
logging.disable(logging.CRITICAL)
from engine.transliterator import transliterate_text, WORD_RE
from engine.alphabet import turkish_lower

# Bağlama göre değişen ya da Hayrat örneği tek/yanıltıcı olan kelimeler (gerekçesiyle)
BILINEN = {
    "rabbine": "bağlam: 2. kişi ربڭه (Rabbine = senin Rabbine), 3. kişi ربنه; onaylı metinde ayet ayet",
    "et": "cümlede Arapça isimden sonra ایت (tesbih et); tek başına sınanınca ات",
    "çağlar": "'çağlar boyu' isim: چاغلر; Hayrat'taki tek örnek fiil (چاغلار)",
    "oturma": "'oturma yerleri' isim; Hayrat'ta tek örnek",
    "atlastan": "atlas kumaş: اطلس; Hayrat'taki tek örnek başka anlam",
}


def norm(o):
    o = unicodedata.normalize("NFC", o).replace("\u06d5", "\u0647").replace("\u06c0", "\u0647").replace("\u06af", "\u0643") \
        .replace("\u06a9", "\u0643").replace("\u064a", "\u06cc").replace("\u0649", "\u06cc").replace("\u0623", "\u0627")
    return re.sub("[\u064b-\u065f\u0670\u0640\u0654\u0610-\u061a\u200c\u200d ]", "", o)


H = collections.defaultdict(collections.Counter)
for satir in open(os.path.join(KOK, "tools", "hayrat_kelime_ciftleri.tsv"), encoding="utf-8"):
    p = satir.rstrip("\n").split("\t")
    if len(p) >= 3 and " " not in p[0]:
        H[turkish_lower(p[0]).replace("\u2019", "'")][norm(p[1])] += int(p[2])

kalan = 0
dosyalar = sorted(glob.glob(os.path.join(KOK, "tests", "mealler", "tr", "*.txt")))
sayac = collections.Counter()
kelimeler = collections.Counter()
for f in dosyalar:
    tr = open(f, encoding="utf-8").read()
    osm = transliterate_text(tr)
    for w in WORD_RE.findall(tr):
        kelimeler[turkish_lower(w).replace("\u2019", "'")] += 1
    if re.search(r"(^|\s)ات(?=[\s.،؛!؟]|$)", osm):
        kalan += 1
        print("KALDI", os.path.basename(f), ": 'et' cümlede ات yazılmış (ایت olmalı)")
    onayli = os.path.join(KOK, "tests", "mealler", "osm", os.path.basename(f))
    if os.path.exists(onayli):
        sayac["onayli"] += 1
        a = osm.replace("\u200c", "").rstrip().split("\n")
        b = open(onayli, encoding="utf-8").read().replace("\u200c", "").rstrip().split("\n")
        for i in range(max(len(a), len(b))):
            x = a[i] if i < len(a) else ""
            y = b[i] if i < len(b) else ""
            if x != y:
                kalan += 1
                print("KALDI", os.path.basename(f), "satir", i + 1, "\n   onayli:", y, "\n   cikan :", x)

for w, n in sorted(kelimeler.items()):
    h = H.get(w)
    if not h:
        sayac["hayratta_yok"] += n
        continue
    o = norm(transliterate_text(w))
    t = sum(h.values())
    if o == h.most_common(1)[0][0] or (o in h and h[o] / t >= 0.2):
        sayac["hayrat_ayni"] += n
        if w in BILINEN:
            print("BILGI: BILINEN listesindeki", w, "artik Hayrat'la ayni; listeden cikarilabilir")
    elif w in BILINEN:
        sayac["bilinen"] += n
    else:
        kalan += 1
        print("KALDI", w, "cikan", transliterate_text(w), "Hayrat", h.most_common(1)[0][0], "(%d kez)" % n)

print(f"BILGI: {len(dosyalar)} sure, {sum(kelimeler.values())} kelime | Hayrat'la ayni {sayac['hayrat_ayni']} | "
      f"bilinen {sayac['bilinen']} | Hayrat'ta yok {sayac['hayratta_yok']} | onayli sure {sayac['onayli']}")
print("SONUC:", "HEPSI GECTI" if not kalan else f"{kalan} TEST KALDI")
sys.exit(1 if kalan else 0)
