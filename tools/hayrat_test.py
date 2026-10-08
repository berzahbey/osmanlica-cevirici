"""Osmanlıca çevirici doğruluk testi: Hayrat Risale-i Nur kelime çiftleri (Latin -> Hayrat Osmanlıcası).
Osmanlıca çevirici konteynerinde: python3 /tmp/hayrat_test.py [en_sik_kac_kelime]
Girdi: /data/hayrat_kelime.tsv   Çıktı: /data/hayrat_test.txt, /data/hayrat_eksik.tsv"""
import collections, re, sys, time, unicodedata
sys.path.insert(0, "/app")
import logging
logging.disable(logging.CRITICAL)
from engine.transliterator import transliterate_text as tt
from engine import dictionary as D

LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else 30000
HAREKE = re.compile("[\u064B-\u0653\u0655-\u065F\u0670\u06D6-\u06ED\u0640\u200c\u200d\u200f\u200e]")
ARAP = re.compile("[\u0600-\u06FF]")
LATIN = re.compile("[A-Za-zÇĞİÖŞÜçğıöşüÂÎÛâîû]")


def norm(o):
    o = unicodedata.normalize("NFC", o or "")
    o = o.replace("\u06C0", "\u0647\u0654").replace("\u06D5", "\u0647").replace("\u064A", "\u06CC").replace("\u0649", "\u06CC")
    o = o.replace("\u06A9", "\u0643").replace("\u06C1", "\u0647")
    o = HAREKE.sub("", o)
    o = re.sub(r"[،؛؟.,;:!?«»\"'()\[\]\-]", " ", o)
    return re.sub(r"\s+", " ", o).strip()


def kucuk(w):
    return w.replace("I", "ı").replace("İ", "i").lower()


# Latin kelime grubu -> Hayrat yazımlarının sayımı
yazim = collections.defaultdict(collections.Counter)
for satir in open("/data/hayrat_kelime.tsv", encoding="utf-8"):
    p = satir.rstrip("\n").split("\t")
    if len(p) != 3:
        continue
    l, o, n = p[0].strip(), p[1].strip(), int(p[2])
    if not LATIN.search(l) or ARAP.search(l) or re.search(r"\d", l) or not ARAP.search(o):
        continue
    yazim[l][norm(o)] += n

secili = sorted(yazim.items(), key=lambda x: -sum(x[1].values()))[:LIMIT]
toplam = sum(sum(c.values()) for _, c in secili)
dogru = dogru_tip = 0
hatalar, eksik = [], []
t0 = time.time()
for i, (l, c) in enumerate(secili):
    hay, n = c.most_common(1)[0]
    adet = sum(c.values())
    try:
        bizim = norm(tt(l, use_ollama_refine=False))
    except Exception as e:
        bizim = f"HATA:{type(e).__name__}"
    if bizim == hay or bizim in c:      # Hayrat'ın kendi yazımlarından biriyse doğru sayılır
        dogru += adet
        dogru_tip += 1
    else:
        k = kucuk(l)
        try:
            hit, _ = D.lookup_with_suffix(k)
        except Exception:
            hit = None
        tur = "sözlükte farklı" if (D.DICTIONARY.get(k) or hit) else "sözlükte yok"
        hatalar.append((adet, l, bizim, hay, tur))
        if tur == "sözlükte yok" and " " not in l:
            eksik.append((k, hay, adet))
    if i % 2000 == 0:
        print(f"  {i}/{len(secili)}  {time.time() - t0:.0f} sn", flush=True)

with open("/data/hayrat_test.txt", "w", encoding="utf-8") as f:
    f.write(f"HAYRAT DOĞRULUK TESTİ — en sık {len(secili)} kelime grubu, metinde {toplam} kez geçiyor\n")
    f.write(f"Doğruluk (geçme sıklığına göre): %{100 * dogru / max(1, toplam):.2f}  |  "
            f"kelime grubu bazında: %{100 * dogru_tip / max(1, len(secili)):.2f}\n")
    say = collections.Counter(t for _, _, _, _, t in hatalar)
    agir = collections.Counter()
    for a, _, _, _, t in hatalar:
        agir[t] += a
    f.write(f"Hata türleri: " + ", ".join(f"{t}: {say[t]} grup ({agir[t]} kez)" for t in say) + "\n\n")
    f.write("== En sık 400 hata (kez | Latin | bizim | Hayrat | tür)\n")
    for adet, l, b, h, t in sorted(hatalar, reverse=True)[:400]:
        f.write(f"{adet:>6}  {l:28s}  {b:22s}  {h:22s}  {t}\n")
with open("/data/hayrat_eksik.tsv", "w", encoding="utf-8") as f:
    for k, h, a in sorted(eksik, key=lambda x: -x[2]):
        f.write(f"{k}\t{h}\t{a}\n")
print(open("/data/hayrat_test.txt", encoding="utf-8").read().split("\n== ")[0], flush=True)
