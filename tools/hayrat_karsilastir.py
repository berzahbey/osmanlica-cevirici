# -*- coding: utf-8 -*-
"""Bir Risale eserinin Türkçesini çeviriciden gerçek akışla geçirir, Hayrat'ın Osmanlıcasıyla kelime kelime karşılaştırır.
Hiçbir şeyi değiştirmez, yalnız rapor yazar.
Kullanım (osmanlica deposunun kökünde, imajda):
  python tools/hayrat_karsilastir.py liste                    -> eserler (slug, sayfa, ad)
  python tools/hayrat_karsilastir.py <slug> [<slug> ...]       -> CIKTI_DIR/karsilastirma_<slug>.txt ve .tsv
  python tools/hayrat_karsilastir.py hepsi                     -> bütün eserler + CIKTI_DIR/karsilastirma_ozet.txt
  EN_COK=300 ile her eserde ilk 300 paragraf.
İki oran yazılır:
  kesin    : Hayrat'ın bu eserdeki yazımıyla birebir aynı kelimeler
  imlâ payı: çeviricinin yazımı, aynı Latin kelime için Hayrat'ın BAŞKA eserlerinde en az CIFT_EN_AZ kez geçiyorsa
             (eserden esere iki doğru imlâ: نشئت/نشأت, طولو/طولی) doğru sayılır. Senin/onun (yalnız ن/ڭ farkı) sayılmaz.
Girdi: HAYRAT_DIR/eserler.json, HAYRAT_DIR/ham/<slug>/osmanlica_*.json ve latince_*.json (hayrat_indir.py çıktısı)."""
import sys, os, re, json, glob, difflib, collections, unicodedata, logging
logging.disable(logging.WARNING)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app"))
from bs4 import BeautifulSoup

H = os.environ.get("HAYRAT_DIR", "/h")
CIKTI = os.environ.get("CIKTI_DIR", "/cikti")
CIFT_EN_AZ = int(os.environ.get("CIFT_EN_AZ", "2"))
NOKTA = ".,;:!?\"'()[]«»“”‘’-—…"


def veri(d):
    return (d.get("data") or []) if isinstance(d, dict) else (d or [])


def duz(t):
    return re.sub(r"\s+", " ", t or "").strip()


def norm(o):
    """Karşılaştırma biçimi: hareke, şedde, ara boşluk, noktalama yok; گ ک -> ك, ە -> ه, ي ى -> ی, أ -> ا."""
    o = unicodedata.normalize("NFC", o).replace("\u06d5", "\u0647").replace("\u06c0", "\u0647") \
        .replace("\u06af", "\u0643").replace("\u06a9", "\u0643").replace("\u064a", "\u06cc").replace("\u0649", "\u06cc") \
        .replace("\u0623", "\u0627")
    o = re.sub("[\u0610-\u061a\u064b-\u065f\u0670\u0640\u0654\u200c\u200d]", "", o)   # dua işaretleri (ؐ ؑ ؓ) sayılmaz
    o = re.sub("[\u060c\u061b\u061f\u06d4\u066a-\u066d\u06dd\u06de]", "", o)   # Arapça noktalama
    return re.sub(r"[^\u0600-\u06ff0-9A-Za-zÇĞİÖŞÜçğıöşüÂÎÛâîû]", "", o)


def lat_kelime(l):
    from engine.alphabet import turkish_lower
    return turkish_lower(l).strip(NOKTA)


def eser_listesi():
    yol = f"{H}/eserler.json"
    eserler = json.load(open(yol, encoding="utf-8")) if os.path.exists(yol) else []
    adlar = {e.get("slug"): e for e in eserler}
    for kl in sorted(glob.glob(f"{H}/ham/*/")):
        s = os.path.basename(kl.rstrip("/"))
        if glob.glob(f"{kl}osmanlica_*.json"):
            e = adlar.get(s, {})
            yield s, e.get("sayfa_sayisi", "?"), e.get("latince", ""), e.get("sira") or 0


def liste():
    for s, n, ad, _ in sorted(eser_listesi(), key=lambda x: x[3]):
        print(f"{s:45} {n:>5} sayfa  {ad}")


def osm_paragraflari(slug):
    gorulen = set()
    for f in sorted(glob.glob(f"{H}/ham/{slug}/osmanlica_*.json")):
        for p in veri(json.load(open(f, encoding="utf-8"))):
            if p.get("id") in gorulen:
                continue
            gorulen.add(p.get("id"))
            soup = BeautifulSoup(p.get("osmanlica_html") or "", "html.parser")
            gruplar = [(duz(sp["data-latince"]), duz(sp.get_text(" "))) for sp in soup.select("span.kelime-grup[data-latince]")]
            if gruplar:
                yield p, gruplar


def paragraflar(slug):
    lat = {}
    for f in sorted(glob.glob(f"{H}/ham/{slug}/latince_*.json")):
        for p in veri(json.load(open(f, encoding="utf-8"))):
            lat[p["id"]] = p
    for p, gruplar in osm_paragraflari(slug):
        ls = BeautifulSoup((lat.get(p["id"]) or {}).get("latince_html") or "", "html.parser")
        for sp in ls.select("[data-latince-ust-bilgi]"):   # isim üstü dua işareti (asm, as): metne karışmasın
            ub, yazi = sp["data-latince-ust-bilgi"], sp.get_text().rstrip()
            if ub and yazi.endswith(" " + ub):
                sp.string = yazi[: -len(ub)].rstrip()
        latince = duz(ls.get_text(" "))
        if latince:
            yield p.get("sayfa"), latince, gruplar


_YAZIMLAR = None


def yazimlar():
    """Latin kelime -> eser -> Counter(norm yazım). Bütün eserlerden, bir kez."""
    global _YAZIMLAR
    if _YAZIMLAR is None:
        _YAZIMLAR = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
        for s, *_ in eser_listesi():
            for _p, gruplar in osm_paragraflari(s):
                for lat, osm in gruplar:
                    lw = [lat_kelime(x) for x in lat.split() if lat_kelime(x)]
                    ow = osm.split()
                    if len(lw) == 1 and len(ow) == 1:
                        _YAZIMLAR[lw[0]][s][norm(ow[0])] += 1
    return _YAZIMLAR


def baska_eserde(lat, bizim_norm, slug):
    """Çeviricinin yazımı aynı Latin kelime için Hayrat'ın başka eserlerinde en az CIFT_EN_AZ kez var mı."""
    w = lat_kelime(lat)
    if not w or " " in w:
        return False
    de = yazimlar().get(w)
    if not de:
        return False
    return sum(c.get(bizim_norm, 0) for s, c in de.items() if s != slug) >= CIFT_EN_AZ


def katman(latin):
    """Latin kelime çeviricide nereden yazılır."""
    from engine import dictionary as D
    w = lat_kelime(latin)
    if not w:
        return "-"
    if " " in w:
        return "çok kelimeli grup"
    if re.search(r"-[ıiuü]$", w):
        return "izafet (-ı/-i)"
    if w in D.HAYRAT_ANAHTAR:
        return "Hayrat sözlüğü"
    if D.lookup_exact(w):
        return "eski sözlük"
    if D.lookup_with_suffix(w)[0]:
        return "sözlük kökü + ek"
    return "kural motoru"


def karsilastir(slug, en_cok=None):
    from engine.transliterator import transliterate_text as cevir
    from engine import dictionary as D
    say = collections.Counter()
    kat_say = collections.Counter()
    hatalar = collections.Counter()        # (latin, hayrat, bizim, katman)
    ornekler = []
    for i, (sayfa, latince, gruplar) in enumerate(paragraflar(slug)):
        if en_cok and i >= en_cok:
            break
        bizim = cevir(latince)
        b_tok = [t for t in bizim.split() if norm(t)]
        h_tok = []                          # (hayrat kelimesi, latin grubu)
        for lat, osm in gruplar:
            for t in osm.split():
                if norm(t):
                    h_tok.append((t, lat))
        bn = [norm(t) for t in b_tok]
        hn = [norm(t) for t, _ in h_tok]
        sm = difflib.SequenceMatcher(None, bn, hn, autojunk=False)
        farklar = []
        bloklar = []
        for op, i1, i2, j1, j2 in sm.get_opcodes():
            if op == "replace" and i2 - i1 == j2 - j1 and j2 - j1 > 1:
                bloklar += [("replace", i1 + k, i1 + k + 1, j1 + k, j1 + k + 1) for k in range(j2 - j1)]
            else:
                bloklar.append((op, i1, i2, j1, j2))
        for op, i1, i2, j1, j2 in bloklar:
            if op == "equal":
                say["dogru"] += j2 - j1
                continue
            hy = " ".join(t for t, _ in h_tok[j1:j2]) or "-"
            bz = " ".join(b_tok[i1:i2]) or "-"
            lat = " ".join(dict.fromkeys(l for _, l in h_tok[j1:j2])) or "(Hayrat'ta yok)"
            if i2 > i1 and j2 > j1 and "".join(bn[i1:i2]) == "".join(hn[j1:j2]):
                say["dogru"] += j2 - j1         # harfler aynı, yalnız bitişik/ayrı yazım farkı
                say["bitisik"] += 1
                hatalar[(lat, hy, bz, "yalnız bitişik/ayrı farkı (doğru sayıldı)")] += 1
                continue
            say["yanlis"] += j2 - j1
            if j2 == j1:
                say["fazla"] += i2 - i1         # çevirici Hayrat'ta olmayan kelime yazdı
            if op == "replace" and i2 - i1 == 1 and j2 - j1 == 1:
                if bn[i1].replace("\u06ad", "\u0646") == hn[j1].replace("\u06ad", "\u0646"):
                    k = "senin/onun (ن/ڭ)"
                elif baska_eserde(lat, bn[i1], slug):
                    say["imla"] += 1
                    k = "imlâ payı: Hayrat başka eserde böyle yazıyor"
                else:
                    k = None
                if k:
                    kat_say[k] += 1
                    hatalar[(lat, hy, bz, k)] += 1
                    continue
            k = katman(lat) if j2 - j1 == 1 else ("eksik/fazla kelime" if op != "replace" else "birden çok kelime")
            if k == "Hayrat sözlüğü":
                sv = D.lookup_exact(lat_kelime(lat))
                if sv and norm(sv[0]) != norm(hy):
                    k = "Hayrat sözlüğü (burada başka yazım)"
            kat_say[k] += max(j2 - j1, 1)
            hatalar[(lat, hy, bz, k)] += 1
            farklar.append(f"    {lat}  |  Hayrat: {hy}  |  çevirici: {bz}  [{k}]")
        if farklar and len(ornekler) < 40:
            ornekler.append(f"--- sayfa {sayfa}\n  TR: {latince[:400]}\n" + "\n".join(farklar[:15]))
    top = say["dogru"] + say["yanlis"]
    kesin = 100 * say["dogru"] / max(top, 1)
    payli = 100 * (say["dogru"] + say["imla"]) / max(top, 1)
    os.makedirs(CIKTI, exist_ok=True)
    yol = f"{CIKTI}/karsilastirma_{slug}"
    with open(yol + ".txt", "w", encoding="utf-8") as f:
        f.write(f"Eser: {slug}\nHayrat kelimesi: {top}\n"
                f"Kesin aynı: {say['dogru']} (%{kesin:.2f}), farklı: {say['yanlis']}\n"
                f"İmlâ payıyla (Hayrat'ın başka eserlerinde en az {CIFT_EN_AZ} kez geçen yazım doğru): %{payli:.2f} "
                f"({say['imla']} kelime)\n"
                f"Yalnız bitişik/ayrı yazım farkı (doğru sayıldı): {say['bitisik']} yer\n"
                f"Çeviricinin fazladan yazdığı kelime (Hayrat'ta karşılığı yok): {say['fazla']}\n\n"
                f"Farkların katmanlara göre dağılımı (Hayrat kelimesi sayısı):\n")
        for k, n in kat_say.most_common():
            f.write(f"  {n:6}  {k}\n")
        f.write("\nEn sık farklar, imlâ payı hariç (adet | Türkçe | Hayrat | çevirici | katman):\n")
        for (lat, hy, bz, k), n in [x for x in hatalar.most_common() if not x[0][3].startswith(("imlâ", "yalnız"))][:150]:
            f.write(f"  {n:4} | {lat} | {hy} | {bz} | {k}\n")
        f.write("\nİmlâ payı sayılanlar (adet | Türkçe | Hayrat burada | çevirici):\n")
        for (lat, hy, bz, k), n in [x for x in hatalar.most_common() if x[0][3].startswith("imlâ")][:60]:
            f.write(f"  {n:4} | {lat} | {hy} | {bz}\n")
        f.write("\nÖrnek paragraflar:\n" + "\n".join(ornekler) + "\n")
    with open(yol + ".tsv", "w", encoding="utf-8") as f:
        f.write("adet\tturkce\thayrat\tcevirici\tkatman\n")
        for (lat, hy, bz, k), n in hatalar.most_common():
            f.write(f"{n}\t{lat}\t{hy}\t{bz}\t{k}\n")
    print(f"{slug}: Hayrat kelimesi {top}, kesin %{kesin:.2f}, imlâ payıyla %{payli:.2f}", flush=True)
    return slug, top, kesin, payli, kat_say


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    en_cok = int(os.environ["EN_COK"]) if os.environ.get("EN_COK") else None
    if sys.argv[1] == "liste":
        liste()
        sys.exit(0)
    sluglar = [s for s, *_ in eser_listesi()] if sys.argv[1] == "hepsi" else sys.argv[1:]
    sonuclar = [karsilastir(s, en_cok) for s in sluglar]
    if len(sonuclar) > 1:
        os.makedirs(CIKTI, exist_ok=True)
        tk = sum(t for _, t, *_ in sonuclar)
        with open(f"{CIKTI}/karsilastirma_ozet.txt", "w", encoding="utf-8") as f:
            f.write("eser\tkelime\tkesin %\timlâ payıyla %\n")
            for s, t, k, p, _ in sonuclar:
                f.write(f"{s}\t{t}\t{k:.2f}\t{p:.2f}\n")
            if tk:
                f.write(f"TOPLAM\t{tk}\t{sum(t * k for _, t, k, _, _ in sonuclar) / tk:.2f}\t"
                        f"{sum(t * p for _, t, _, p, _ in sonuclar) / tk:.2f}\n")
            kt = collections.Counter()
            for *_, ks in sonuclar:
                kt.update(ks)
            f.write("\nBütün eserlerde katmanlara göre farklar:\n")
            for k, n in kt.most_common():
                f.write(f"  {n:7}  {k}\n")
        print(f"Özet: {CIKTI}/karsilastirma_ozet.txt")
