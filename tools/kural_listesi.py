"""Kitaplarda sözlükte olmayan (kural motorunun yazdığı) kelimeler. Osmanlıca çevirici konteynerinde:
    python3 /tmp/kural_listesi.py
Girdi: /data/kitaplar_tr/*.json (Kütüphane kitap.json kopyaları)   Çıktı: /data/kural_listesi.txt"""
import collections, glob, json, os, re, sys
sys.path.insert(0, "/app")
import logging
logging.disable(logging.CRITICAL)
from engine import dictionary as D
from engine.transliterator import transliterate_text as tt

RISALE = ("tılsım", "tilsim", "sikke", "asar", "âsâr")
KELIME = re.compile(r"[A-Za-zÇĞİÖŞÜçğıöşüÂÎÛâîû]+")


def kucuk(w):
    return w.replace("I", "ı").replace("İ", "i").lower()


say = collections.Counter()
kitap_say = collections.defaultdict(collections.Counter)
for yol in sorted(glob.glob("/data/kitaplar_tr/*.json")):
    k = json.load(open(yol, encoding="utf-8"))
    ad = k.get("baslik") or os.path.basename(yol)
    if any(r in kucuk(ad) for r in RISALE):
        continue
    for b in k.get("bloklar", []):
        metin = (b.get("metin") or {}).get("tr") or ""
        for w in KELIME.findall(metin):
            if len(w) >= 3:
                say[kucuk(w)] += 1
                kitap_say[kucuk(w)][ad] += 1

kural = []
for w, n in say.most_common():
    if w in D.DICTIONARY:
        continue
    try:
        hit, _ = D.lookup_with_suffix(w)
    except Exception:
        hit = None
    if hit:
        continue
    kural.append((n, w))

with open("/data/kural_listesi.txt", "w", encoding="utf-8") as f:
    toplam = sum(say.values())
    f.write(f"Risale dışı kitaplar: {len(say)} farklı kelime, {toplam} kez | sözlükte olmayan (kural motoru): "
            f"{len(kural)} farklı, {sum(n for n, _ in kural)} kez (%{100 * sum(n for n, _ in kural) / max(1, toplam):.1f})\n\n")
    for n, w in kural[:600]:
        kitaplar = ", ".join(a[:22] for a, _ in kitap_say[w].most_common(2))
        f.write(f"{n:>5}  {w:24s} {tt(w):24s} {kitaplar}\n")
print(open("/data/kural_listesi.txt", encoding="utf-8").readline())
