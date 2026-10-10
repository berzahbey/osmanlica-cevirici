# -*- coding: utf-8 -*-
"""Hayrat'tan çift yazımları çıkarır: Türkçesi (Latin) aynı, Osmanlıcası farklı yazılmış bütün kelimeler.
Hiçbir şeyi değiştirmez, yalnız rapor yazar. Üç türe ayırır:
  senin_onun     : yalnız ن/ڭ farkı (كندینه/كندیڭه) - "senin" kuralının işi
  yazim_cesidi   : aynı kelime, iki doğru imlâ (ایت/ات, طولو/طولی, نشئت/نشأت, تقوا/تقوی) - hata sayılmaz
  anlam_farki    : kök harfi farklı (arz ارض/عرض, esîr اسیر/اثیر) - bağlam sözlüğü adayı
Ayrıca her kelime için "eser ayrışması": yazımlar eserden esere mi ayrılıyor (dönem/baskı farkı) yoksa aynı eserde
ikisi de mi var (anlam farkı belirtisi).
Girdi: HAYRAT_DIR/ham/<eser>/osmanlica_*.json (hayrat_baglam_ogren.py ile aynı okuyucu).
Çıktı (CIFT_CIKTI klasörü): cift_yazim_ozet.txt, yazim_cesitleri.tsv, anlam_farki.tsv, senin_onun.tsv
Eşikler: CIFT_TOPLAM (6), CIFT_AZINLIK (3), CIFT_ORAN (0.05): azınlık yazım en az 3 kez ve en az %5.
Çalıştırma (osmanlica deposunun kökünde, imajda):  python tools/cift_yazim.py"""
import sys, os, collections, logging
logging.disable(logging.WARNING)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hayrat_baglam_ogren as HB          # eserler(), norm(), D (sözlük)

CIKTI = os.environ.get("CIFT_CIKTI", "/cikti")
EN_AZ_TOPLAM = int(os.environ.get("CIFT_TOPLAM", "6"))
EN_AZ_AZINLIK = int(os.environ.get("CIFT_AZINLIK", "3"))
EN_AZ_ORAN = float(os.environ.get("CIFT_ORAN", "0.05"))
ORNEK_SAYISI = 3

UNLU = set("\u0627\u0648\u06cc\u064a\u0647\u0626\u0621\u0624\u0625\u0622\u0623\u06c0")   # ا و ی ي ه ئ ء ؤ إ آ أ ۀ (ة ünsüz sayılır: ت)
SIKI = {"\u0629": "\u062a"}                                              # ة -> ت (صلاة/صلات)
GEVSEK = {"\u0637": "\u062a", "\u062f": "\u062a", "\u0635": "\u0633", "\u0642": "\u0643",
          "\u063a": "\u0643", "\u0629": "\u062a"}                        # ط د -> ت, ص -> س, ق غ -> ك
ENG = "\u06ad"                                                            # ڭ
NUN = "\u0646"
ISARET = set("*\u0608\u0610\u0611\u0612\u0613\u0614")                    # Hayrat'ın dua işaretleri


def iskelet(o, harita):
    """Ünlü harfler atılmış ünsüz dizisi (harita ile ünsüz eşleştirmesi)."""
    return "".join(harita.get(c, c) for c in o if c not in UNLU)


def koken(w):
    try:
        h = HB.D.lookup_exact(w)
    except Exception:
        h = None
    return (h[1] if h and len(h) > 1 else "") or ""


def sinif(w, a, b):
    """İki yazımın farkının türü."""
    if a.replace(ENG, NUN) == b.replace(ENG, NUN):
        return "senin_onun"
    if iskelet(a, SIKI) == iskelet(b, SIKI):
        return "yazim_cesidi"                       # yalnız ünlü harf / hemze farkı
    if iskelet(a, GEVSEK) == iskelet(b, GEVSEK):
        k = koken(w)
        if k not in ("ar", "fa", "ar-fa", "fa-ar"):
            return "yazim_cesidi"                   # Türkçe kelimede ط/ت, د/ت, ص/س, ق/ك farkı (تورلی/دورلی)
    return "anlam_farki"


def ayrisma(eser_say):
    """Yazımlar eserden esere mi ayrılıyor: her eserin çoğunluk yazımına uyan kelime oranı ve
    iki yazımın da en az 2'şer kez birlikte geçtiği eser sayısı."""
    uyan = top = birlikte = 0
    for c in eser_say.values():
        if not c:
            continue                                # bu eserde yalnız eşik altı yazım var
        n = sum(c.values())
        top += n
        uyan += c.most_common(1)[0][1]
        if len(c) >= 2 and c.most_common(2)[1][1] >= 2:
            birlikte += 1
    return (uyan / top if top else 0.0), birlikte


def topla(eser):
    yaz = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))   # w -> eser -> norm -> n
    ham = collections.defaultdict(collections.Counter)                                      # (w, norm) -> ham yazım -> n
    ornek = collections.defaultdict(list)                                                   # (w, norm) -> [(eser, bağlam)]
    for ad, pars in eser.items():
        for seq in pars:
            for i, (w, o, oh) in enumerate(seq):
                if not o or any(c in ISARET for c in oh or ""):
                    continue
                yaz[w][ad][o] += 1
                ham[(w, o)][oh] += 1
                if len(ornek[(w, o)]) < ORNEK_SAYISI:
                    sol = " ".join(x[0] for x in seq[max(0, i - 5):i])
                    sag = " ".join(x[0] for x in seq[i + 1:i + 6])
                    ornek[(w, o)].append((ad, f"{sol} [{w}] {sag}".strip()))
    return yaz, ham, ornek


def cozumle(yaz, ham, ornek):
    sonuc = []                                   # (tür, w, top, [(norm, ham, n)], ayrışma, birlikte, örnekler)
    for w, de in yaz.items():
        top = collections.Counter()
        for c in de.values():
            top.update(c)
        n = sum(top.values())
        if len(top) < 2 or n < EN_AZ_TOPLAM:
            continue
        yazimlar = [(o, k) for o, k in top.most_common() if k >= EN_AZ_AZINLIK and k / n >= EN_AZ_ORAN]
        if len(yazimlar) < 2:
            continue
        cogun = yazimlar[0][0]
        turler = {sinif(w, cogun, o) for o, _ in yazimlar[1:]}
        tur = "anlam_farki" if "anlam_farki" in turler else ("yazim_cesidi" if "yazim_cesidi" in turler else "senin_onun")
        ay, bir = ayrisma({e: collections.Counter({o: k for o, k in c.items() if o in dict(yazimlar)})
                           for e, c in de.items()})
        liste = [(o, ham[(w, o)].most_common(1)[0][0], k) for o, k in yazimlar]
        orn = {o: ornek[(w, o)] for o, _ in yazimlar}
        sonuc.append((tur, w, n, liste, ay, bir, orn))
    sonuc.sort(key=lambda x: (x[0], -x[2]))
    return sonuc


def yaz_dosyalar(sonuc, eser_sayisi):
    os.makedirs(CIKTI, exist_ok=True)
    dosya = {"yazim_cesidi": "yazim_cesitleri.tsv", "anlam_farki": "anlam_farki.tsv", "senin_onun": "senin_onun.tsv"}
    acik = {t: open(os.path.join(CIKTI, f), "w", encoding="utf-8") for t, f in dosya.items()}
    for t, f in acik.items():
        f.write("# kelime\ttoplam\tyazımlar (yazım:adet)\teser ayrışması\tikisi birlikte geçen eser\torijin\n")
        if t == "anlam_farki":
            f.write("#   (alt satırlar: yazım\teser\tbağlam)\n")
    for tur, w, n, liste, ay, bir, orn in sonuc:
        f = acik[tur]
        f.write(f"{w}\t{n}\t{' '.join(f'{h}:{k}' for _, h, k in liste)}\t{ay:.2f}\t{bir}\t{koken(w)}\n")
        if tur == "anlam_farki":
            for o, h, _ in liste:
                for ad, bag in orn[o]:
                    f.write(f"#   {h}\t{ad}\t{bag}\n")
    for f in acik.values():
        f.close()
    say = collections.Counter(t for t, *_ in sonuc)
    eserden = sum(1 for t, w, n, l, ay, bir, o in sonuc if t == "anlam_farki" and ay >= 0.95 and bir == 0)
    with open(os.path.join(CIKTI, "cift_yazim_ozet.txt"), "w", encoding="utf-8") as f:
        f.write(f"Hayrat: {eser_sayisi} eser. Eşik: toplam ≥{EN_AZ_TOPLAM}, azınlık yazım ≥{EN_AZ_AZINLIK} ve ≥%{EN_AZ_ORAN*100:.0f}\n")
        for t in ("yazim_cesidi", "anlam_farki", "senin_onun"):
            f.write(f"{t}: {say[t]} kelime -> {dosya[t]}\n")
        f.write(f"anlam_farki içinde eserden esere ayrılan (ayrışma ≥0.95, hiçbir eserde birlikte değil; dönem/baskı farkı olabilir): {eserden}\n")
        f.write("\nEn sık anlam farkı adayları:\n")
        for tur, w, n, liste, ay, bir, orn in [x for x in sonuc if x[0] == "anlam_farki"][:60]:
            f.write(f"  {w} ({n}): {' / '.join(f'{h}({k})' for _, h, k in liste)}  ayrışma {ay:.2f}, birlikte {bir} eser\n")
    return say


def main():
    eser = dict(HB.eserler())
    print(f"{len(eser)} eser", flush=True)
    sonuc = cozumle(*topla(eser))
    say = yaz_dosyalar(sonuc, len(eser))
    print(f"yazım çeşidi {say['yazim_cesidi']}, anlam farkı {say['anlam_farki']}, senin/onun {say['senin_onun']}")
    print(f"Rapor: {CIKTI}/cift_yazim_ozet.txt")


if __name__ == "__main__":
    main()
