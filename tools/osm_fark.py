# -*- coding: utf-8 -*-
# Osmanlica cevirici olcum araci: eski kod ile yamali kod ayni metinleri cevirir, yalniz degisen kelimeler baglamiyla yazilir.
# Kullanim (kod klasorunde, imajin icinde):
#   FARK_KOD=/app   python tools/osm_fark.py uret /cikti/eski.jsonl <dosya ya da klasor> ...   (imajdaki kod)
#   FARK_KOD=/k/app python tools/osm_fark.py uret /cikti/yeni.jsonl <dosya ya da klasor> ...   (yamali kod)
#   python tools/osm_fark.py karsilastir /cikti/eski.jsonl /cikti/yeni.jsonl /cikti/rapor.txt
# Girdi: .txt (oldugu gibi) ve .pdf (sayfa metni). Her satir ayri cevrilir (Studyo da paragraf paragraf gonderir).
import os, sys, json, time, glob, difflib, collections, re


def _dosyalar(girdiler):
    for g in girdiler:
        if os.path.isdir(g):
            for f in sorted(glob.glob(os.path.join(g, "**", "*"), recursive=True)):
                if f.lower().endswith((".txt", ".pdf")):
                    yield f
        elif os.path.isfile(g):
            yield g
        else:
            print("UYARI: bulunamadi:", g)


def _metin(f):
    if f.lower().endswith(".pdf"):
        import fitz
        d = fitz.open(f)
        t = "\n".join(p.get_text() for p in d)
        d.close()
        return t
    return open(f, encoding="utf-8-sig", errors="replace").read()


def uret(cikti, girdiler):
    kod = os.environ.get("FARK_KOD") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app")
    sys.path.insert(0, os.path.abspath(kod))
    import logging
    logging.disable(logging.CRITICAL)
    import engine.transliterator as tr_mod
    from engine.transliterator import transliterate_text
    print("KOD:", os.path.dirname(os.path.dirname(os.path.abspath(tr_mod.__file__))),
          "| PYTHONHASHSEED:", os.environ.get("PYTHONHASHSEED", "(yok)"))
    bas = time.time()
    ds = sy = ke = 0
    with open(cikti, "w", encoding="utf-8") as out:
        for f in _dosyalar(girdiler):
            ds += 1
            for i, satir in enumerate(_metin(f).replace("\r\n", "\n").replace("\r", "\n").split("\n"), 1):
                if not satir.strip():
                    continue
                osm = transliterate_text(satir)
                sy += 1
                ke += len(satir.split())
                out.write(json.dumps({"d": os.path.basename(f), "s": i, "tr": satir, "osm": osm}, ensure_ascii=False) + "\n")
    print(f"URETILDI: {ds} dosya, {sy} satir, {ke} kelime, {time.time() - bas:.0f} sn -> {cikti}")


def _oku(yol):
    v = {}
    for satir in open(yol, encoding="utf-8"):
        r = json.loads(satir)
        v[(r["d"], r["s"])] = r
    return v


_NOKTA = re.compile(r"^[^\w]+|[^\w]+$")


def karsilastir(eski, yeni, rapor):
    a, b = _oku(eski), _oku(yeni)
    sorun = []
    for k in sorted(set(a) ^ set(b)):
        sorun.append(f"SATIR YALNIZ {'ESKIDE' if k in a else 'YENIDE'}: {k[0]}:{k[1]}")
    gruplar = collections.defaultdict(list)
    degisen_satir = ka = kb = 0
    for k in sorted(set(a) & set(b)):
        x, y = a[k], b[k]
        if x["tr"] != y["tr"]:
            sorun.append(f"TURKCE FARKLI (girdi degismis): {k[0]}:{k[1]}")
            continue
        ta, tb, tt = x["osm"].split(), y["osm"].split(), x["tr"].split()
        ka += len(ta)
        kb += len(tb)
        if ta == tb:
            continue
        degisen_satir += 1
        hizali = len(tt) == len(ta)
        for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, ta, tb, autojunk=False).get_opcodes():
            if op == "equal":
                continue
            if hizali:
                t1, t2 = i1, max(i2, i1 + 1)
                tr_parca = " ".join(tt[t1:t2])
            else:
                o = len(tt) / max(len(ta), 1)
                t1, t2 = int(i1 * o), max(int(i2 * o), int(i1 * o) + 1)
                tr_parca = "~" + " ".join(tt[t1:t2])
            baglam = " ".join(tt[max(0, t1 - 4):t1] + ["[" + " ".join(tt[t1:t2]) + "]"] + tt[t2:t2 + 4])
            anahtar = (_NOKTA.sub("", tr_parca.lower()) or tr_parca, " ".join(ta[i1:i2]) or "(yok)", " ".join(tb[j1:j2]) or "(yok)")
            gruplar[anahtar].append(f"{k[0]}:{k[1]}  {baglam}")
    sirali = sorted(gruplar.items(), key=lambda g: (-len(g[1]), g[0]))
    ozet = [f"OZET: {len(a)} satir (eski), {len(b)} satir (yeni) | degisen satir {degisen_satir} | "
            f"farkli kelime grubu {len(gruplar)}, toplam yer {sum(len(v) for v in gruplar.values())} | "
            f"Osmanlica kelime sayisi eski {ka}, yeni {kb} (fark {kb - ka})"]
    satirlar = []
    for (t, o1, o2), yerler in sirali:
        satirlar.append(f"{len(yerler):5d}  {t}:  {o1}  ->  {o2}")
        for y in yerler[:3]:
            satirlar.append("         " + y)
    with open(rapor, "w", encoding="utf-8") as f:
        f.write("\n".join(ozet + sorun + satirlar) + "\n")
    goster = int(os.environ.get("FARK_GOSTER", "120"))
    print("\n".join(ozet + sorun[:20]))
    gr = 0
    for s in satirlar:
        if not s.startswith(" "):
            gr += 1
        if gr > goster:
            print(f"... (devami raporda: {rapor})")
            break
        print(s)
    print("SONUC:", "FARK YOK" if not gruplar and not sorun else f"{len(gruplar)} GRUP FARK, {len(sorun)} UYARI", "| rapor:", rapor)


if __name__ == "__main__":
    if len(sys.argv) >= 4 and sys.argv[1] == "uret":
        uret(sys.argv[2], sys.argv[3:])
    elif len(sys.argv) == 5 and sys.argv[1] == "karsilastir":
        karsilastir(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        print("Kullanim: osm_fark.py uret <cikti.jsonl> <girdi>... | karsilastir <eski.jsonl> <yeni.jsonl> <rapor.txt>")
        sys.exit(2)
