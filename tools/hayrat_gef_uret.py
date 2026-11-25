"""Tur GF: Hayrat kelime çiftlerinden kef/gef tablosu (app/data/hayrat_gef.tsv) ve kuralın ölçümü.
Tabloya girer: Hayrat'ta gef'li yazılan ya da kuralın Hayrat'tan ayrıldığı kelime (Latin + anahtar -> ك/گ dizisi; aynı anahtarın
yazımlarının en az %90'ı aynı dizideyse). Kullanım: python tools/hayrat_gef_uret.py [kelime_ciftleri.tsv]"""
import collections, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app"))
from engine import gef

KAYNAK = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "hayrat_kelime_ciftleri.tsv")
HEDEF = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app", "data", "hayrat_gef.tsv")
D = collections.defaultdict(collections.Counter)
kural_farki = collections.Counter()
olc = collections.Counter()
for satir in open(KAYNAK, encoding="utf-8"):
    p = satir.rstrip("\n").split("\t")
    if len(p) < 3 or " " in p[0].strip() or " " in p[1].strip():
        continue
    lat, osm, n = p[0], p[1].replace("ە", "ه"), int(p[2])
    if not any(c in osm for c in (gef.KEF, gef.GEF)):
        continue
    d = gef.desen(osm)
    D[(gef._kucuk(lat), gef.anahtar(osm))][d] += n
    r = gef.kural(lat, osm.replace(gef.GEF, gef.KEF))
    olc["toplam"] += n
    if r is None:
        olc["eslenemedi"] += n
    elif r == osm:
        olc["dogru"] += n
    else:
        olc["yanlis"] += n
        kural_farki[(gef._kucuk(lat), gef.anahtar(osm))] += n
# genel tablo (Latin eşlenemeyince): aynı Osmanlıca anahtarın bütün Latin karşılıkları aynı diziyle yazılıyorsa
G = collections.defaultdict(collections.Counter)
for (lat, k), c in D.items():
    G[k].update(c)
yaz = 0
with open(HEDEF, "w", encoding="utf-8") as f:
    f.write("# Tur GF: Hayrat kef/gef dizisi (1 = گ). tools/hayrat_gef_uret.py üretir.\n")
    for k in sorted(D):
        d, s = D[k].most_common(1)[0]
        if s / sum(D[k].values()) < 0.9:
            continue
        if "1" in d or k in kural_farki:
            f.write(f"{k[0]}\t{k[1]}\t{d}\n")
            yaz += 1
    for k in sorted(G):
        d, s = G[k].most_common(1)[0]
        if s / sum(G[k].values()) >= 0.95 and "1" in d:
            f.write(f"*\t{k}\t{d}\n")
            yaz += 1
t = olc["toplam"]
print(f"kural: {t} geçiş, doğru %{100*olc['dogru']/t:.2f}, yanlış %{100*olc['yanlis']/t:.2f}, eşlenemedi %{100*olc['eslenemedi']/t:.2f}")
print(f"tablo: {yaz} kelime -> {HEDEF}")
