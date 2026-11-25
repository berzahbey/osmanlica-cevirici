"""Tur GF (25 Kasım 2026, Zahir kararı): kef/gef Hayrat gibi.
Hayrat (22 eser, 206 bin kef/gef'li kelime) ölçümü: kelime başı g ك (%99: gibi كبی، güzel كوزل); ince kelimede ğ گ (%96,5: eğer اگر،
değil دگل، ettiği ایتدیگی، mesleği مسلگی، vermeye ویرمگه); kalın ğ غ (olduğu اولدیغی); Türkçe kelime içi g ك (sevgili سوكیلی، zengin
زنكین، hangi هانكی); Farsça -gâh/-gâr/-gân/-gâm گ (dergâh درگاه، yegâne یگانه، hengâm هنگام); eski yazım: yirmi یگرمی، bey بگ.
Çevirici içeride her yerde ك yazar; bu son adım Latin kelimeyi Osmanlıca kelimeyle eşleyip k/g/ğ harflerini sırayla kef türüne
çevirir. Önce Hayrat'ın kendi yazımı (data/hayrat_gef.tsv: Hayrat kelimesinin kef/gef dizisi), yoksa kural. Eşlenemeyen kelimeye
dokunulmaz (ك kalır). Tablo Latin kelimeyle birlikte aranır (direğe دیرگه ile "der ki" دیركه karışmasın). Hayrat kelimelerinde kural tek başına %99,8 doğru (tools/hayrat_gef_uret.py ölçer).
OSM_GEF=0 ile kapatılır (eski davranış: her g ك)."""
import os
import re
from functools import lru_cache
from pathlib import Path

from . import birlik as _birlik

ACIK = os.environ.get("OSM_GEF", "1") != "0"
KEF, GEF = "ك", "گ"
_KEFLER = "كگقغک"      # ك گ ق غ ک (Latin k/g/ğ karşılıkları)
_FARSCA = re.compile(r"g[âa](h|r|n|m)")          # -gâh, -gâr, -gân, -gâm
_OZEL = [(re.compile(r"^yirm"), "yiğirm"),
         (re.compile(r"(?<![a-zçğışöüâîû])(|ağa|ata)bey(?=$|'|ler|im|imiz|in$|e$|i$|den|de$)"), r"\1beğ"),
         (re.compile(r"^güverc"), "göğerc")]
_HARF = re.compile(r"[ً-ٰٟؐ-ؚ‌‍ـ]")
_LAT_TOK = re.compile(r"[^\W\d_]+(?:['’‘ʻ][^\W\d_]+)*")
_OSM_TOK = re.compile(r"[ء-يً-ٰٟٱ-ۓەیگکڭپچژ‌ٔ]+")


def _kucuk(s):
    return s.replace("I", "ı").replace("İ", "i").lower().replace("’", "'").replace("‘", "'").replace("ʻ", "'")


def anahtar(osm):
    """Hayrat tablosu anahtarı: kef/gef, ە/ه, ي/ی, hareke, ara boşluk farkı yok."""
    o = osm.replace(GEF, KEF).replace("ک", KEF).replace("ە", "ه").replace("ي", "ی").replace("ى", "ی")
    o = o.replace("أ", "ا").replace("إ", "ا")
    return _HARF.sub("", o).replace("ّ", "").replace("ٔ", "")


def desen(osm):
    """Kelimedeki ك/گ harflerinin sırayla gef olup olmadığı: '0101'."""
    return "".join("1" if c == GEF else "0" for c in osm if c in (KEF, GEF, "ک"))


def hazirla(lat):
    l = _kucuk(lat)
    for r, y in _OZEL:
        l = r.sub(y, l)
    return re.sub(r"(kk|gg|ğğ)", lambda m: m.group(0)[0], l)


def harfler(lat, meye=False):
    """Latin kelimenin k/g/ğ harfleri sırayla: k (ك/ق), ğ (ince: گ), g (ك), gf (Farsça g: گ)."""
    l = hazirla(lat)
    if meye:
        l = re.sub(r"m([ea])y\1", r"m\1ğ\1", l)        # -meye/-maya mastar yönelmesi: مگه/مغه (Hayrat vermeye ویرمگه)
    out = []
    for i, ch in enumerate(l):
        if ch == "k":
            out.append("k")
        elif ch == "ğ":
            out.append("ğ")
        elif ch == "g":
            out.append("gf" if i > 0 and _FARSCA.match(l, i) else "g")
    return out


_HEDEF = {"k": KEF, "ğ": GEF, "g": KEF, "gf": GEF}


def kural(lat, osm):
    """Latin kelimeye göre ك/گ; eşlenemezse None."""
    pos = [i for i, c in enumerate(osm) if c in _KEFLER]
    L = harfler(lat)
    if len(L) != len(pos):
        L = harfler(lat, meye=True)
        if len(L) != len(pos):
            return None
    o = list(osm)
    for h, p in zip(L, pos):
        if o[p] in (KEF, GEF, "ک"):
            o[p] = _HEDEF[h]
    return "".join(o)


def desen_uygula(osm, d):
    pos = [i for i, c in enumerate(osm) if c in (KEF, GEF, "ک")]
    if len(pos) != len(d):
        return None
    o = list(osm)
    for p, b in zip(pos, d):
        o[p] = GEF if b == "1" else KEF
    return "".join(o)


TABLO = {}


def _yukle():
    yol = Path(__file__).parent.parent / "data" / "hayrat_gef.tsv"
    if yol.exists():
        for satir in open(yol, encoding="utf-8"):
            p = satir.rstrip("\n").split("\t")
            if len(p) >= 3 and not satir.startswith("#"):
                TABLO[(p[0], p[1])] = p[2]


_yukle()


def kelime(lat, osm):
    """Tek kelime: önce Hayrat yazımı, sonra kural; ikisi de yoksa olduğu gibi."""
    if not any(c in osm for c in (KEF, GEF, "ک")):
        return osm
    d = TABLO.get(anahtar(osm))
    if d is not None:
        r = desen_uygula(osm, d)
        if r is not None:
            return r
    r = kural(lat, osm)
    return r if r is not None else osm


# Eşleme için hızlı ünsüz iskeleti: belirsiz harfler (ünlüler, v, y, h; ا و ی ه ع ء ح خ) sayılmaz; s/t/d/z bir sınıf,
# k/g/ğ bir sınıf (ك گ ق غ); art arda aynı sınıf tek sayılır (şedde, kk, ettiği ایتدیگی).
_L_SINIF = str.maketrans({"b": "B", "p": "B", "c": "C", "ç": "C", "j": "C", "t": "X", "d": "X", "s": "X", "z": "X", "k": "K", "g": "K",
                          "ğ": "K", "l": "L", "m": "M", "n": "N", "r": "R", "f": "F", "ş": "Ş"})
_O_SINIF = str.maketrans({"ب": "B", "پ": "B", "ج": "C", "چ": "C", "ژ": "C", "ت": "X", "ط": "X", "د": "X", "ض": "X", "ث": "X", "ذ": "X",
                          "ز": "X", "ظ": "X", "س": "X", "ص": "X", "ك": "K", "گ": "K", "ق": "K", "غ": "K", "ک": "K", "ل": "L", "م": "M",
                          "ن": "N", "ڭ": "N", "ر": "R", "ف": "F", "ش": "Ş"})


def _sikistir(s, gecerli):
    out = []
    for c in s:
        if c in gecerli and (not out or out[-1] != c):
            out.append(c)
    return "".join(out)


_SINIFLAR = set("BCXKLMNRFŞ")


@lru_cache(maxsize=300000)
def _iskelet_l(lat):
    l = hazirla(lat)
    a = _sikistir(l.translate(_L_SINIF), _SINIFLAR)
    l2 = re.sub(r"m([ea])y\1", r"m\1ğ\1", l)
    return a, (_sikistir(l2.translate(_L_SINIF), _SINIFLAR) if l2 != l else a)


@lru_cache(maxsize=300000)
def _iskelet_o(osm):
    return _sikistir(osm.translate(_O_SINIF), _SINIFLAR)


def _uyar(lat, osm):
    o = _iskelet_o(osm)
    a, b = _iskelet_l(lat)
    return bool(o) and (o == a or o == b)


_BITISIK_RE = re.compile(r"^(ki|beri|m[iıuü](s[iıuü]n|y[iıuü]m|d[iıuü]r|y[iıuü]z|s[iıuü]n[iıuü]z|d[iıuü]|ydi|ymiş)?)$")


def _esle(L, O, bant=10):
    """Latin ve Osmanlıca kelime dizilerini sırayı bozmadan eşler (en çok eşleşme; köşegen çevresinde bant). Bitişik ki/mi/beri
    iki Latin kelimeyi tek Osmanlıca kelimeyle eşleyebilir."""
    n, m = len(L), len(O)
    if not n or not m:
        return {}
    oran = m / n
    NEG = -1
    dp = {}

    def bantta(i, j):
        return abs(j - i * oran) <= bant
    # geriye doğru: dp[(i, j)] = i'den ve j'den sonraki en çok eşleşme
    for i in range(n, -1, -1):
        jm = int(i * oran)
        for j in range(min(m, jm + bant + 1), max(-1, jm - bant - 1), -1):
            if i == n or j == m:
                dp[(i, j)] = (0, None)
                continue
            en = max(dp.get((i + 1, j), (NEG,))[0], dp.get((i, j + 1), (NEG,))[0])
            sec = None
            if dp.get((i + 1, j), (NEG,))[0] >= dp.get((i, j + 1), (NEG,))[0]:
                sec = ("L",)
            else:
                sec = ("O",)
            if i + 1 < n and _BITISIK_RE.match(_kucuk(L[i + 1])) and (i + 2, j + 1) in dp and _uyar(L[i] + _kucuk(L[i + 1]), O[j]):
                v = dp[(i + 2, j + 1)][0] + 1
                if v > en:
                    en, sec = v, ("B",)
            if j + 1 < m and (i + 1, j + 2) in dp and _uyar(L[i], O[j] + O[j + 1]):
                v = dp[(i + 1, j + 2)][0] + 1          # Latin bitişik, Osmanlıca ayrı: vasfettiği وصف ایتدیگی
                if v > en:
                    en, sec = v, ("S",)
            if (i + 1, j + 1) in dp and _uyar(L[i], O[j]):
                v = dp[(i + 1, j + 1)][0] + 1
                if v > en or (v == en and sec[0] != "B"):
                    en, sec = v, ("E",)
            dp[(i, j)] = (max(en, 0), sec)
    esler = {}
    i, j = 0, 0
    if (0, 0) not in dp:
        return {}
    while i < n and j < m and (i, j) in dp:
        sec = dp[(i, j)][1]
        if sec is None:
            break
        if sec[0] == "E":
            esler[j] = L[i]
            i += 1
            j += 1
        elif sec[0] == "B":
            esler[j] = L[i] + _kucuk(L[i + 1])
            i += 2
            j += 1
        elif sec[0] == "S":
            esler[(j, j + 1)] = L[i]
            i += 1
            j += 2
        elif sec[0] == "L":
            i += 1
        else:
            j += 1
    return esler


def metin(latin, osm_metin):
    """Çevirinin bütün metni: Latin kelimeler Osmanlıca kelimelerle sırayla eşlenir (kısa ileri bakışla), eşlenen kelimeye
    kef/gef kuralı uygulanır. Eşlenmeyen kelimede yalnız Hayrat tablosu."""
    if not osm_metin or not (ACIK or _birlik.ACIK):
        return osm_metin
    L = _LAT_TOK.findall(latin or "")
    O = list(_OSM_TOK.finditer(osm_metin))
    esler = _esle(L, [m.group(0) for m in O])
    for anah, lat in list(esler.items()):
        if isinstance(anah, tuple):                  # iki Osmanlıca kelimeye bölünen Latin kelime: birlikte düzeltilir
            a, b = anah
            r = kural(lat, O[a].group(0) + " " + O[b].group(0))
            del esler[anah]
            if r is not None:
                ra, rb = r.split(" ", 1)
                esler[a], esler[b] = ("=", ra), ("=", rb)
    parcalar, son = [], 0
    for k, m in enumerate(O):
        w = m.group(0)
        e = esler.get(k, "")
        yeni = e[1] if isinstance(e, tuple) else (kelime(e, w) if ACIK else w)
        yeni = _birlik.duzelt("" if isinstance(e, tuple) else e, yeni)   # Tur ÇY: Hayrat'ın çift yazımlarında kurala uyan
        if yeni != w:
            parcalar.append(osm_metin[son:m.start()])
            parcalar.append(yeni)
            son = m.end()
    if not parcalar:
        return osm_metin
    parcalar.append(osm_metin[son:])
    return "".join(parcalar)
