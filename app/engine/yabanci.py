"""Tur KM6 (12 Kasım 2026): Osmanlıcada Latin harf kalmaz. Yabancı (Avrupa dilleri) kelime ve özel isimler önce aslının okunuşuna
göre Türkçe harflerle yeniden yazılır (Robespierre -> Robespyer, Cambridge -> Kembriç, The French Revolution -> Di Frenç Revolüsyon),
sonra çevirinin olağan kurallarıyla Arap harfine geçer. Kaynak: data/yabanci_okunus.tsv (elle), tabloda olmayan yabancı görünümlü
kelimede kaba okunuş kuralları. Türkçe sözlükte bulunan kelimeye dokunulmaz; kısa ya da Türkçeyle çakışan tablo kelimeleri (on, in,
der, art...) yalnız yanındaki kelime de yabancıysa değişir."""
import re
from pathlib import Path

from . import dictionary
from .alphabet import turkish_lower

_TABLO = {}
_dosya = Path(__file__).parent.parent / "data" / "yabanci_okunus.tsv"
if _dosya.exists():
    for _s in open(_dosya, encoding="utf-8"):
        if _s.startswith("#") or "\t" not in _s:
            continue
        _a, _b = _s.rstrip("\n").split("\t")[:2]
        if _a.strip() and _b.strip():
            _TABLO[_a.strip().lower()] = _b.strip()

_TR_HARF = set("çğışöüÇĞİŞÖÜıâîûāīūḥṣṭẓḍġḳĀĪŪḤṢṬẒḌĠḲ‘ʻ`")
_YABANCI_HARF = re.compile(r"[xwqéèêëàäœæßñçÿ]".replace("ç", ""))
# Büyük harfli (özel ad) kelimede Batı dili izi; th/sh/tt/ss gibi diziler Arapça kelimelerin Latin yazımında da var (Ethem, nesh, hissetti), sayılmaz
_YABANCI_IZ = re.compile(r"ph|ch|ck|gh|ou|eau|ee|oo|ae|oe|ie$")
_KELIME = re.compile(r"([A-Za-zÀ-ÿĞİŞığşÇçÖöÜüÂÎÛâîûœŒæÆāīūḥṣṭẓḍġḳĀĪŪḤṢṬẒḌĠḲ][A-Za-zÀ-ÿĞİŞığşÇçÖöÜüÂÎÛâîûœŒæÆāīūḥṣṭẓḍġḳĀĪŪḤṢṬẒḌĠḲ‘ʻ`\-]*)(['’][A-Za-zçğıöşüÇĞİÖŞÜâîû]+)?")


def _turkce_mi(w: str) -> bool:
    wl = turkish_lower(w)
    return bool(dictionary.lookup_exact(wl) or dictionary.lookup_with_suffix(wl)[0])


def _baglam_gerekir(anahtar: str) -> bool:
    """Türkçeyle çakışabilen tablo kelimesi: kısa ya da Türkçe sözlükte var (on, in, der, art, modern, simon)."""
    return _turkce_mi(anahtar) or anahtar in ("a", "an", "at", "on", "in", "is", "to", "de", "da", "la", "le", "en", "et", "du")


_LATINCE = re.compile(r"(us|um|ius|ae|is|es)$|^(sc|c[aoulrt])")


def latince_okunus(w: str) -> str:
    """Latince ad (Constantinus, Cassiodorus, Justinianus, Scotus): c -> k (e/i önünde s), j -> y, ph -> f, th -> t, ae -> e."""
    s = w.lower()
    for a, b in (("ph", "f"), ("th", "t"), ("ae", "e"), ("oe", "e"), ("qu", "kv"), ("x", "ks"), ("y", "i"), ("ch", "k")):
        s = s.replace(a, b)
    s = re.sub(r"c(?=[eiy])", "s", s).replace("c", "k")
    s = re.sub(r"^j|(?<=[aeiou])j", "y", s).replace("j", "y").replace("w", "v")
    s = re.sub(r"([bcdfgklmnprstvz])\1", r"\1", s)
    return s[:1].upper() + s[1:] if w[:1].isupper() else s


def _latince_mi(w: str) -> bool:
    """Latince / İtalyanca kelime: Türkçe olmayan harf dizisi (c+a/o/u, qu, ae, ii) ve Latince sonu (caritas, docere, Toscana)."""
    s = w.lower()
    if not re.search(r"c[aoulr]|qu|ae|oe|ii$|ph", s):
        return False
    if not w[:1].isupper():   # küçük harfli Latince kelime: yalnız belirgin Latince sonları (caritas, sequentia, mercurii)
        return len(s) >= 6 and bool(re.search(r"(tas|tis|tum|tus|ere|ii|ae|ia|ium|ius|orum|arum)$", s))
    return len(s) >= 5 and bool(re.search(r"(tas|tis|tum|tus|ere|ent|unt|ii|ae|ia|io|ium|ius|um|us|orum|arum|nna|ana|es)$", s))


def kural_okunus(w: str) -> str:
    """Tabloda olmayan yabancı kelime için kaba okunuş (Fransızca / Almanca / İngilizce izlerine göre)."""
    s = w.lower()
    if (w[:1].isupper() and len(s) >= 5 and re.search(r"(us|um|ius)$", s)) or _latince_mi(w):
        return latince_okunus(w)
    fr = re.search(r"eau|oi|ou|ais|ait|eux|ez$|et$|ier$|ière|[éèêàç]|gn|qu|ille|tte$|aux$|ault|ois$|que$|eur$", s)
    de = re.search(r"sch|[äöüß]|ei|ie|tz|mann$|berg$|ung$|lich$|isch", s) and not fr
    if fr:
        for a, b in (("eaux", "o"), ("eau", "o"), ("aux", "o"), ("au", "o"), ("oi", "uva"), ("ou", "u"), ("ai", "e"), ("ei", "e"),
                     ("eu", "ö"), ("œu", "ö"), ("qu", "k"), ("ph", "f"), ("th", "t"), ("ch", "ş"), ("gn", "ny"), ("ille", "iy"),
                     ("tion", "syon")):
            s = s.replace(a, b)
        s = re.sub(r"(?<=[aeiouö])([stdxzp]|nt)$", "", s)       # sondaki okunmayan ünsüz (Furet, Robert, Sieyès)
        s = re.sub(r"(?<=[^aeiouö])e$", "", s)                   # sondaki okunmayan e
        s = re.sub(r"c(?=[eiyé])", "s", s)
        s = re.sub(r"g(?=[eiyé])", "j", s)
    elif de:
        for a, b in (("sch", "ş"), ("tsch", "ç"), ("ch", "h"), ("ei", "ay"), ("ie", "i"), ("äu", "oy"), ("eu", "oy"), ("ß", "s"),
                     ("tz", "ts"), ("ck", "k"), ("ph", "f"), ("th", "t")):
            s = s.replace(a, b)
        s = s.replace("z", "ts").replace("w", "v").replace("ä", "e")
        s = re.sub(r"^v", "f", s)
        s = re.sub(r"(?<=[aeiouöü])j|^j", "y", s)
    else:
        for a, b in (("tion", "şen"), ("sion", "jen"), ("th", "t"), ("ph", "f"), ("sh", "ş"), ("ch", "ç"), ("ck", "k"), ("gh", ""),
                     ("ee", "i"), ("oo", "u"), ("ea", "i"), ("qu", "kv"), ("wh", "v")):
            s = s.replace(a, b)
        s = re.sub(r"c(?=[eiy])", "s", s)
        s = re.sub(r"(?<=[^aeiou])e$", "", s) if len(s) > 4 else s
        s = re.sub(r"y$", "i", s)
        s = s.replace("j", "c")
    for a, b in (("x", "ks"), ("w", "v"), ("q", "k"), ("c", "k"), ("y", "y"), ("é", "e"), ("è", "e"), ("ê", "e"), ("ë", "e"),
                 ("à", "a"), ("â", "a"), ("ñ", "ny"), ("æ", "e"), ("œ", "ö"), ("ÿ", "i")):
        s = s.replace(a, b)
    s = re.sub(r"([bcdfgklmnprstvz])\1", r"\1", s)                # çift ünsüz tek okunur
    s = re.sub(r"[^a-zçğıöşüâîû\-]", "", s)
    if not s:
        s = w
    return s[:1].upper() + s[1:] if w[:1].isupper() else s


def _yabanci_aday(w: str) -> bool:
    """Temkinli: Türkçe/Arapça kelimenin Latin yazımına (hissetti, Ethem, vaz‘iyet) dokunulmaz."""
    if any(c in _TR_HARF for c in w) or len(w) < 2:
        return False
    if _turkce_mi(w) or _turkce_mi(w.translate(str.maketrans("éèêëÉÈÊË", "eeeeEEEE"))):
        return False
    if _YABANCI_HARF.search(w.lower()):
        return True        # Türk alfabesinde olmayan harf (x, w, q, é...)
    if not w[:1].isupper():
        return _latince_mi(w)
    if (len(w) >= 5 and re.search(r"(us|um|ius)$", w)) or re.search(r"^(Sc|Cl|Cr|Ct)", w):
        return True        # Latince / Batı dili özel adı (Constantinus, Cluny): Türkçe c (ج) okunmaz
    return _latince_mi(w) or bool(_YABANCI_IZ.search(w.lower()))


def _roma(w: str):
    """Büyük harfli Roma rakamı (I-L): sayı; değilse None (XIV. yüzyıl -> 14. yüzyıl)."""
    if not re.fullmatch(r"(?=[IVXL])L?X{0,3}(IX|IV|V?I{0,3})", w):
        return None
    d = {"I": 1, "V": 5, "X": 10, "L": 50}
    t = 0
    for i, c in enumerate(w):
        t += -d[c] if i + 1 < len(w) and d[w[i + 1]] > d[c] else d[c]
    return str(t) if t else None


def yeniden_yaz(metin: str) -> str:
    """Metindeki yabancı kelimeleri Türkçe okunuşla yeniden yazar (Latin harfle kalacak kelime bırakmaz)."""
    if not isinstance(metin, str) or not re.search(r"[A-Za-z]", metin):
        return metin
    parcalar = list(_KELIME.finditer(metin))
    karar = []      # (yeni, kesin_yabanci, baglam_bekliyor)
    for m in parcalar:
        w = m.group(1)
        k = w.lower()
        r_ = _roma(w) if len(w) > 1 or not m.group(2) else None
        if r_ and (len(w) > 1 or re.match(r"\.?\s+(yüzyıl|asır|cilt|bölüm|kısım)", metin[m.end():m.end() + 12], re.I)):
            karar.append((r_, True, False, ""))   # Roma rakamı: sayı (tek harfli I/V/X yalnız ardından nokta ya da yüzyıl gelirse)
            continue
        if k in ("d", "l") and m.group(2) and m.group(2)[1:2].isupper():   # Fransızca D'Harcourt, L'Humanité: tek kelime okunur
            ad = m.group(2)[1:]
            karar.append(("D" if k == "d" else "L", True, False, (_TABLO.get(ad.lower()) or kural_okunus(ad)).lower()))
            continue
        if any(c in "‘ʻ`" for c in w):
            karar.append((None, False, False, None))
            continue
        if k in _TABLO:
            if _baglam_gerekir(k) and not (w[:1].isupper() and not _turkce_mi(w)):
                karar.append((_TABLO[k], False, True, None))
            else:
                karar.append((_TABLO[k], True, False, None))
        elif _yabanci_aday(w):
            karar.append((kural_okunus(w), True, False, None))
        else:
            karar.append((None, False, False, None))
    # bağlam bekleyen kelime (de, la, on, der): yalnız iki yanı da yabancı olan dizinin içindeyse yabancıdır
    # (Histoire de la Révolution); bir yanı Türkçe ise Türkçe kalır (Robespierre de geldi -> ده)
    i = 0
    while i < len(karar):
        if karar[i][2] and not karar[i][1]:
            j = i
            while j < len(karar) and karar[j][2] and not karar[j][1]:
                j += 1
            sol = i > 0 and karar[i - 1][1]
            sag = j < len(karar) and karar[j][1]
            if sol and sag:
                for k in range(i, j):
                    y, _, bek, b = karar[k]
                    karar[k] = (y, True, bek, b)
            i = j
        else:
            i += 1
    out, pos = [], 0
    for i, m in enumerate(parcalar):
        yeni, kesin, bekler, birlesik = karar[i]
        if birlesik is not None:
            out.append(metin[pos:m.start(0)] + yeni + (birlesik or (m.group(2) or "")))
            pos = m.end(0)
            continue
        if bekler and not kesin:
            yeni = None
        out.append(metin[pos:m.start(1)])
        if yeni:
            w = m.group(1)
            if w.isupper() and len(w) > 1:
                yeni = yeni.upper()
            elif w[:1].isupper():
                yeni = yeni[:1].upper() + yeni[1:]
            else:
                yeni = turkish_lower(yeni[:1]) + yeni[1:]
            out.append(yeni)
        else:
            out.append(m.group(1))
        pos = m.end(1)
    out.append(metin[pos:])
    return "".join(out)


_LATIN_KALAN = re.compile(r"[A-Za-zÀ-ÿœŒæÆ][A-Za-zÀ-ÿœŒæÆ\-]*")


def latin_kalan_var(o: str) -> bool:
    return bool(_LATIN_KALAN.search(o or ""))
