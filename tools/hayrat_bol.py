"""Hayrat kelime çiftlerini EĞİTİM ve SINAV olarak ayırır. Stüdyo konteynerinde: python3 /tmp/hayrat_bol.py
Sınav: özgün eserler. Sınav eserlerinde geçen her paragraf (başka eserde de geçse) eğitimden çıkarılır.
Çıktı: /data/hayrat/egitim_kelime.tsv, /data/hayrat/sinav_kelime.tsv"""
import collections, json, os, re, sys
from bs4 import BeautifulSoup

KOK = "/data/hayrat/ham"
SINAV = {"muhakemat", "isaratul-i-caz", "emirdag-lahikasi-4"}
HAREKE = re.compile("[\u064B-\u065F\u0670\u0640\u200c\u200d\s،؛؟.,;:!?«»\"'()\\[\\]-]")


def veri(d):
    return (d.get("data") or []) if isinstance(d, dict) else (d or [])


def duz(t):
    return re.sub(r"\s+", " ", t or "").strip()


paragraflar = []  # (eser, anahtar, çiftler)
for slug in sorted(os.listdir(KOK)):
    gorulen = set()
    for f in sorted(os.listdir(f"{KOK}/{slug}")):
        if not (f.startswith("osmanlica_") and f.endswith(".json")):
            continue
        for p in veri(json.load(open(f"{KOK}/{slug}/{f}", encoding="utf-8"))):
            if p["id"] in gorulen:
                continue
            gorulen.add(p["id"])
            soup = BeautifulSoup(p.get("osmanlica_html") or "", "html.parser")
            anahtar = HAREKE.sub("", soup.get_text())
            ciftler = [(duz(sp["data-latince"]), duz(sp.get_text())) for sp in soup.select("span.kelime-grup[data-latince]")]
            if ciftler and len(anahtar) >= 20:
                paragraflar.append((slug, anahtar, ciftler))

sinav_metin = {a for s, a, _ in paragraflar if s in SINAV}
egitim, sinav = collections.Counter(), collections.Counter()
cikarilan = 0
for slug, anahtar, ciftler in paragraflar:
    if slug in SINAV:
        sinav.update(ciftler)
    elif anahtar in sinav_metin:
        cikarilan += 1
    else:
        egitim.update(ciftler)

for ad, c in (("egitim", egitim), ("sinav", sinav)):
    with open(f"/data/hayrat/{ad}_kelime.tsv", "w", encoding="utf-8") as f:
        for (l, o), n in sorted(c.items(), key=lambda x: -x[1]):
            f.write(f"{l}\t{o}\t{n}\n")
print(f"paragraf: {len(paragraflar)} | sınav eserleri: {', '.join(sorted(SINAV))}")
print(f"eğitim: {sum(egitim.values())} kelime ({len(egitim)} çift) | sınav: {sum(sinav.values())} kelime ({len(sinav)} çift) | "
      f"sınavda da geçtiği için eğitimden çıkarılan paragraf: {cikarilan}")
