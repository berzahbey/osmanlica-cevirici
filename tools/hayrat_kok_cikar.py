"""Kök sözlüğü (tur "kök listesi", 12 Ekim): app/data/hayrat_kok.tsv üretir.

Neyin kök olduğu: Zemberek kök listesi (tools/zemberek_kokler.tsv).
Kökün nasıl yazılacağı: Hayrat. Kökün kendisi ve "kök + yazımı kesin ek" biçimleri (gizle+mek كیزله‌مك -> كیزله)
oylanır; en az %75 aynı yazımı veren kök alınır. Ek önünde yumuşayan (kitab-, toprağ-) ve ünlüsü düşen (oğl-, boyn-)
biçimler de ayrı satır olarak yazılır.

Çalıştırma (kod klasöründe): python tools/hayrat_kok_cikar.py
Çıktı sütunları: latin, osmanlıca, tür (V/N), kaynak sayısı, not (yumusama / dusme / bos)
"""
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

KOK_DIZIN = Path(__file__).resolve().parent
sys.path.insert(0, str(KOK_DIZIN.parent / "app"))
from engine.alphabet import turkish_lower  # noqa: E402

ZW = "\u200c"


def N(x):
    """Hayrat Latin/Osmanlıca çiftlerindeki yazım farklarını birleştir (ە ه، گ ك، ي ی، hareke, ara boşluk)."""
    x = x.replace("\u06d5", "\u0647").replace("\u06af", "\u0643").replace("\u06a9", "\u0643").replace("\u064a", "\u06cc")
    return re.sub("[\u064b-\u0650\u0652\u0670]", "", x).replace(ZW, "")


# (Latin ek, Osmanlıca yazımı): yalnız yazımı kesin ve kökün sonunu değiştirmeyen ekler
EKLER_V = [("mek", "مك"), ("mak", "مق"), ("di", "دی"), ("dı", "دی"), ("du", "دی"), ("dü", "دی"), ("ti", "دی"), ("tı", "دی"),
           ("tu", "دی"), ("tü", "دی"), ("miş", "مش"), ("mış", "مش"), ("muş", "مش"), ("müş", "مش"), ("meli", "ملی"), ("malı", "ملی"),
           ("mez", "مز"), ("maz", "مز"), ("se", "سه"), ("sa", "سه"), ("dik", "دك"), ("dık", "دق"), ("mesi", "مسی"), ("ması", "مسی")]
EKLER_N = [("ler", "لر"), ("lar", "لر"), ("den", "دن"), ("dan", "دن"), ("ten", "دن"), ("tan", "دن"), ("de", "ده"), ("da", "ده"),
           ("dir", "دیر"), ("dır", "دیر"), ("dur", "دیر"), ("dür", "دیر"), ("le", "له"), ("la", "له"), ("dir", "در"), ("dır", "در"),
           ("dur", "در"), ("dür", "در")]


def zemberek():
    Z = {}
    for line in open(KOK_DIZIN / "zemberek_kokler.tsv", encoding="utf-8"):
        if line.startswith("#"):
            continue
        k, t, oz = line.rstrip("\n").split("\t")
        Z.setdefault(k, {})[t] = set(o for o in oz.split(",") if o)
    return Z


def hayrat():
    H = defaultdict(Counter)
    for line in open(KOK_DIZIN / "hayrat_kelime_ciftleri.tsv", encoding="utf-8"):
        l, o, s = line.rstrip("\n").split("\t")
        if " " in o.strip():
            continue
        H[turkish_lower(l)][N(o)] += int(s)
    return H


def oyla(H, r, ekler, yalin=True):
    """Yazım -> (kanıt sayısı, kanıt veren ek türleri)."""
    oy, tur = Counter(), defaultdict(set)
    for e, oe in ekler:
        for o, n in H.get(r + e, {}).items():
            if o.endswith(oe) and len(o) > len(oe):
                oy[o[: -len(oe)]] += n
                tur[o[: -len(oe)]].add(oe)
    if yalin:                                          # fiilde yalın biçim sayılmaz: "asıl" اصل isimdir, asıl- آصیل
        for o, n in H.get(r, {}).items():
            oy[o] += n
            tur[o].add("yalin")
    return oy, tur


def gecerli(r, y, tur):
    if not y or not re.fullmatch("[\u0621-\u064a\u0651\u067e\u0686\u0698\u06ad\u06cc\u06c6]+", y):
        return False
    if len(y) >= 4 and y[: len(y) // 2] == y[len(y) // 2:]:
        return False                                   # ikileme: fırıl fırıl, akın akın
    if tur == "V" and re.search("(et|ed|ol|eyle|eyl)$", r) and len(r) >= 5:
        return False                                   # birleşik fiil (zemmet, mahvol): _bilesik_fiil yazar
    unsuz = len(re.findall("[^aeıioöuüâîû]", r))
    if len(y) < unsuz - 1 or len(y) > len(r) + 1:
        return False                                   # harf sayısı kökle uyuşmuyor (görev كورو)
    return True


# Kelimenin ilk sesi ile Osmanlıca ilk harfin uyumu (ottoman_dict'te yazım değil anlam karşılığı olan kayıtlar: oysa حالبوكه)
_ILK = {"b": "ب", "c": "جغ", "ç": "چ", "d": "دضط", "f": "ف", "g": "كغگ", "ğ": "غ", "h": "هحخ", "j": "ژج", "k": "كقخ", "l": "ل",
        "m": "م", "n": "ن", "p": "پب", "r": "ر", "s": "سصث", "ş": "ش", "t": "تط", "v": "و", "y": "ی", "z": "زذضظ"}


def bas_uyumlu(latin, osm):
    ilk = latin[:1]
    if ilk in "aeıioöuüâîû":
        return osm[:1] in "اآأإعئو"
    return osm[:1] in _ILK.get(ilk, osm[:1])


_SES = {"k": ("ğ", {"\u0642": "\u063a", "\u0643": "\u0643"}), "p": ("b", {"\u067e": "\u0628", "\u0628": "\u0628"}),
        "ç": ("c", {"\u0686": "\u062c", "\u062c": "\u062c"}), "t": ("d", {"\u062a": "\u062f", "\u0637": "\u062f", "\u062f": "\u062f"})}


def main():
    Z = zemberek()
    H = hayrat()
    cikti = {}
    for r, turler in Z.items():
        if len(r) < 3:
            continue
        for tur, oz in turler.items():
            oy, ekturu = oyla(H, r, EKLER_V if tur == "V" else EKLER_N, yalin=(tur == "N"))
            if not oy:
                continue
            (y, n), = oy.most_common(1)
            top = sum(oy.values())
            if n / top < (0.9 if tur == "V" else 0.75) or not gecerli(r, y, tur):
                continue                               # Hayrat iki türlü yazıyorsa (kapandı قاپاندی / kapanmış قپانمش) alınmaz
            if len(ekturu[y]) < 2:
                continue                               # tek ek türünden gelen kanıt yetmez (kas- yazımı kasdı قصدی'den gelmesin)
            cikti[(r, tur)] = (y, n, "")                  # isim ve fiil ayrı: boya بویه / boya- بویا، dal دال / dal- طال
            # ek önünde yumuşama (kitab-, toprağ-): Zemberek'in Voicing işareti ya da çok heceli Türkçe k/p/ç
            hece = len(re.findall("[aeıioöuüâîû]", r))
            son = r[-1]
            if son in _SES and "NoVoicing" not in oz and ("Voicing" in oz or (hece >= 2 and son in "kpç")) and tur == "N":
                yr, tablo = _SES[son]
                if y[-1] in tablo:
                    cikti.setdefault((r[:-1] + yr, tur), (y[:-1] + tablo[y[-1]], n, "yumusama"))
            # ünlü düşmesi (oğul -> oğl-, boyun -> boyn-): sondan ikinci harf ünlü harfiyse yazımdan düşer
            if "LastVowelDrop" in oz and re.search("[aeıioöuü][^aeıioöuü]$", r):
                d = r[:-2] + r[-1]
                yd = y[:-2] + y[-1] if len(y) >= 3 and y[-2] in "\u0648\u06cc\u0627" else y
                cikti.setdefault((d, tur), (yd, n, "dusme"))
            if "Doubling" in oz:
                cikti.setdefault((r + r[-1], tur), (y, n, "ikiz"))
    # Hayrat'tan yazımı çıkmayan Zemberek kökü ottoman_dict'te Arapça/Farsça kayıtsa o da alınır (hatırla- خاطرلا، havsala حوصله).
    # Türkçe kayıtlar alınmaz (ölçüldü: kurut-, sark-, tala- bozuluyordu).
    for line in open(KOK_DIZIN.parent / "app" / "data" / "ottoman_dict.tsv", encoding="utf-8"):
        p = line.rstrip("\n").split("\t")
        if len(p) < 3:
            continue
        k = turkish_lower(p[0])
        arap = p[2] in ("ar", "fa", "ar-fa", "fa-ar") or re.search("[\u0639\u062d\u062b\u0630\u0638\u0636\u062e]", p[1])
        if len(k) >= 3 and k in Z and not any((k, t) in cikti for t in ("N", "V")) and " " not in p[1] and arap \
                and k not in H and bas_uyumlu(k, p[1]):
            cikti[(k, "N")] = (p[1], 1, "ottoman_dict")
    yol = KOK_DIZIN.parent / "app" / "data" / "hayrat_kok.tsv"
    with open(yol, "w", encoding="utf-8") as f:
        for r, tur in sorted(cikti):
            y, n, nt = cikti[(r, tur)]
            if y[:1] in ("\u0623", "\u0625"):
                y = "\u0627" + y[1:]                     # kelime başında hemze yazılmaz (eyle أیله -> ایله; dictionary.py ile aynı)
            f.write(f"{r}\t{y}\t{tur}\t{n}\t{nt}\n")
    print(f"{len(cikti)} kök -> {yol}")
    # Zemberek'in bütün kökleri (yazımı bilinmeyenler dahil): motor, daha uzun gerçek kökün başını kök saymasın (ham+am "hamam")
    zyol = KOK_DIZIN.parent / "app" / "data" / "zemberek_kok.txt"
    with open(zyol, "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(Z)) + "\n")
    print(f"{len(Z)} Zemberek kökü -> {zyol}")


if __name__ == "__main__":
    main()
