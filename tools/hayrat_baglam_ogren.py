# -*- coding: utf-8 -*-
"""Hayrat'tan bağlam sözlüğü: aynı Latin kelimenin bağlama göre farklı yazıldığı yerler (arz ارض/عرض, esîr اسیر/اثیر).
Girdi: HAYRAT_DIR/ham/<eser>/osmanlica_*.json (kelime grupları, data-latince). Kaynak eserler değişmez.
Çıktı: app/data/hayrat_baglam.tsv (kelime, yazım, özellik, sayı). Her eser, kendisi dışındaki eserlerden öğrenilen
bilgiyle denenir (bir kitabı dışarıda bırak); düzelen/bozulan sayıları eşik eşik yazılır.
Çalıştırma (osmanlica deposunun kökünde, imajda):  python tools/hayrat_baglam_ogren.py [esik]"""
import sys, os, re, json, glob, math, collections, unicodedata, logging
logging.disable(logging.WARNING)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app"))
from bs4 import BeautifulSoup
from engine import dictionary as D
from engine.alphabet import turkish_lower

H = os.environ.get("HAYRAT_DIR", "/h")
CIKTI = os.environ.get("BAGLAM_CIKTI", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app", "data", "hayrat_baglam.tsv"))
NOKTA = ".,;:!?\"'()[]«»“”‘’-—…"


def norm(o):
    o = unicodedata.normalize("NFC", o).replace("\u06d5", "\u0647").replace("\u06c0", "\u0647").replace("\u06af", "\u0643") \
        .replace("\u06a9", "\u0643").replace("\u064a", "\u06cc").replace("\u0649", "\u06cc").replace("\u0623", "\u0627")
    o = re.sub("[\u0610-\u061a\u064b-\u065f\u0670\u0640\u0654\u200c\u200d]", "", o)
    return re.sub("[\u060c\u061b\u061f\u06d4]", "", o)


def kelime(l):
    return turkish_lower(l).strip(NOKTA)


def eserler():
    """Her eser için paragraflar: [(latin_kelime, osm_norm|None, osm_ham|None), ...]"""
    for kl in sorted(glob.glob(f"{H}/ham/*/")):
        ad = os.path.basename(kl.rstrip("/"))
        pars, gor = [], set()
        for f in sorted(glob.glob(f"{kl}osmanlica_*.json")):
            d = json.load(open(f, encoding="utf-8"))
            for p in (d.get("data") or []) if isinstance(d, dict) else (d or []):
                if p.get("id") in gor:
                    continue
                gor.add(p.get("id"))
                soup = BeautifulSoup(p.get("osmanlica_html") or "", "html.parser")
                seq = []
                for sp in soup.select("span.kelime-grup[data-latince]"):
                    lat = re.sub(r"\s+", " ", sp["data-latince"]).strip()
                    osm = re.sub(r"\s+", " ", sp.get_text(" ")).strip()
                    lw = [kelime(x) for x in lat.split() if kelime(x)]
                    ow = osm.split()
                    if len(lw) == 1 and len(ow) == 1:
                        seq.append((lw[0], norm(ow[0]), ow[0]))
                    else:
                        seq += [(w, None, None) for w in lw]
                if seq:
                    pars.append(seq)
        if pars:
            yield ad, pars


def ozellikler(seq, i):
    f = []
    for k, ad in ((-1, "L1"), (1, "R1"), (-2, "L2"), (2, "R2")):
        j = i + k
        f.append(f"{ad}:{seq[j][0]}" if 0 <= j < len(seq) else f"{ad}:#")
    return f


def main():
    esikler = [float(x) for x in sys.argv[1:]] or [1.0, 2.0, 3.0, 4.0, 5.0]
    eser = dict(eserler())
    print(f"{len(eser)} eser", flush=True)
    # 1) yazım sayıları (eser eser)
    yaz = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))   # w -> eser -> norm -> n
    ham = collections.defaultdict(collections.Counter)                                       # (w,norm) -> ham -> n
    for ad, pars in eser.items():
        for seq in pars:
            for w, o, oh in seq:
                if o:
                    yaz[w][ad][o] += 1
                    ham[(w, o)][oh] += 1
    belirsiz = {}
    for w, de in yaz.items():
        top = collections.Counter()
        for c in de.values():
            top.update(c)
        n = sum(top.values())
        if len(top) < 2 or n < 6:
            continue
        iki = top.most_common(2)
        if iki[1][1] >= 3 and iki[1][1] / n >= 0.05:
            if len({o.replace("\u06ad", "\u0646") for o in top}) < len(top):
                continue                     # senin/onun (yalnız ن/ڭ farkı): "senin" kuralının işi
            belirsiz[w] = top
    print(f"bağlama bağlı kelime: {len(belirsiz)}", flush=True)
    # 2) özellik sayıları (eser eser)
    oz = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))     # (w,norm) -> eser -> feat -> n
    for ad, pars in eser.items():
        for seq in pars:
            for i, (w, o, _) in enumerate(seq):
                if o and w in belirsiz:
                    for f in ozellikler(seq, i):
                        oz[(w, o)][ad][f] += 1

    def varsayilan(w, top):
        h = D.lookup_exact(w)
        if h and norm(h[0]) in top:
            return norm(h[0])
        return top.most_common(1)[0][0]

    # toplamlar: dışarıda bırakılan eserin payı toplamdan çıkarılır (hızlı)
    onc_top = {w: dict(top) for w, top in belirsiz.items()}
    oz_top = {}
    for key, de in oz.items():
        t = collections.Counter()
        for c in de.values():
            t.update(c)
        oz_top[key] = t

    def skor(w, ozs, haric):
        """Her yazım için log olasılık (Naive Bayes, eklemeli düzeltme). haric: dışarıda bırakılan eser."""
        sonuc = {}
        eh = yaz[w].get(haric, {})
        onc = {o: n - eh.get(o, 0) for o, n in onc_top[w].items()}
        topl = sum(onc.values())
        if topl <= 0:
            return None
        for o, n in onc.items():
            if n <= 0:
                continue
            ft, fe = oz_top.get((w, o), {}), oz[(w, o)].get(haric, {})
            s = math.log(n / topl)
            enc = 0
            for f in ozs:
                c = ft.get(f, 0) - fe.get(f, 0)
                enc = max(enc, c)
                s += math.log((c + 0.1) / (n + 5.0))
            sonuc[o] = (s, enc)
        return sonuc

    # 3) bir kitabı dışarıda bırak
    sonuc = {e: collections.Counter() for e in esikler}
    kelime_say = {e: collections.defaultdict(collections.Counter) for e in esikler}
    ornek = {e: [] for e in esikler}
    for k, (ad, pars) in enumerate(eser.items()):
        if k % 20 == 0:
            print(f"  ölçülüyor: {k}/{len(eser)} eser", flush=True)
        for seq in pars:
            for i, (w, o, _) in enumerate(seq):
                if not o or w not in belirsiz:
                    continue
                v = varsayilan(w, belirsiz[w])
                sk = skor(w, ozellikler(seq, i), ad)
                if not sk or v not in sk:
                    continue
                en = max(sk, key=lambda x: sk[x][0])
                fark = sk[en][0] - sk[v][0]
                for e in esikler:
                    sec = en if (en != v and fark >= e and sk[en][1] >= 2) else v
                    if sec == v:
                        sonuc[e]["dogru_kaldi" if v == o else "yanlis_kaldi"] += 1
                    elif sec == o:
                        sonuc[e]["duzeldi"] += 1
                        kelime_say[e][w]["duzeldi"] += 1
                    elif v == o:
                        sonuc[e]["bozuldu"] += 1
                        kelime_say[e][w]["bozuldu"] += 1
                        if len(ornek[e]) < 15:
                            ornek[e].append((ad, w, o, sec, round(fark, 1), " ".join(x[0] for x in seq[max(0, i - 3):i + 4])))
                    else:
                        sonuc[e]["yanlis_degisti"] += 1
                        kelime_say[e][w]["bozuldu"] += 1
    print("\nBir kitabı dışarıda bırak (her eser kendisi hariç öğrenilenle):")
    for e in esikler:
        s = sonuc[e]
        print(f"  eşik {e}: düzelen {s['duzeldi']}, bozulan {s['bozuldu']}, yanlıştan yanlışa {s['yanlis_degisti']}, "
              f"doğru kalan {s['dogru_kaldi']}, yanlış kalan {s['yanlis_kaldi']}")
        for x in ornek[e][:8]:
            print("     bozulan:", *x)
    # 4) kelime seçimi: görmediği eserlerde hiç bozmayan, en az EN_AZ kez düzelten kelimeler
    EN_AZ = int(os.environ.get("BAGLAM_EN_AZ", "3"))
    print(f"\nKelime seçimi (bozan kelime alınmaz, en az {EN_AZ} düzeltme):")
    en_iyi = None
    for e in esikler:
        secilen = {w for w, c in kelime_say[e].items() if c["bozuldu"] == 0 and c["duzeldi"] >= EN_AZ}
        duz = sum(kelime_say[e][w]["duzeldi"] for w in secilen)
        print(f"  eşik {e}: {len(secilen)} kelime, düzelen {duz}, bozulan 0")
        if en_iyi is None or duz > en_iyi[1]:
            en_iyi = (e, duz, secilen)
    esik, _, secilen = en_iyi
    print(f"Seçilen eşik: {esik}; kelimeler: {', '.join(sorted(secilen)[:80])}{' …' if len(secilen) > 80 else ''}")
    for w in sorted(secilen)[:40]:
        c = kelime_say[esik][w]
        print(f"   {w}: düzelen {c['duzeldi']}  ({' / '.join(ham[(w, o)].most_common(1)[0][0] + ' ' + str(n) for o, n in belirsiz[w].most_common(3))})")
    belirsiz = {w: belirsiz[w] for w in secilen}
    # 5) bütün eserlerle tablo (yalnız seçilen kelimeler)
    with open(CIKTI, "w", encoding="utf-8") as f:
        f.write("# Hayrat bağlam sözlüğü (tools/hayrat_baglam_ogren.py). kelime\tyazım\tözellik\tsayı; özellik * = toplam\n")
        f.write(f"#esik\t{esik}\n")
        for w in sorted(belirsiz):
            for o, n in belirsiz[w].most_common():
                oh = ham[(w, o)].most_common(1)[0][0]
                f.write(f"{w}\t{oh}\t*\t{n}\n")
                fs = collections.Counter()
                for c in oz[(w, o)].values():
                    fs.update(c)
                for ft, c in sorted(fs.items()):
                    if c >= 2:
                        f.write(f"{w}\t{oh}\t{ft}\t{c}\n")
    print(f"\nTablo: {CIKTI}")


if __name__ == "__main__":
    main()
