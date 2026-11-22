"""Tur YZ1 (12 Kasım 2026): çeviriden önce sözlükte bulunamayan kelimeyi sözlükteki biçimine yaklaştırma (yapay zekâsız ön adım).
1) Şapka farkı: metinde şapkasız yazılmış Arapça/Farsça kelime sözlükte şapkalı duruyorsa (tabiydi -> tâbiydi: تابع ایدی).
2) Birleşik kelime: Türkçe ön kelime + sözlükte bulunan kelime (başkahramanları -> baş kahramanları: باش قهرمانلری).
Yalnız kelimenin kendisi (ya da kök + ek) sözlükte HİÇ bulunmuyorsa denenir; bulunan kelimeye dokunulmaz."""
import re
from functools import lru_cache

from . import dictionary
from .alphabet import turkish_lower

_KELIME = re.compile(r"(?<![\w'’‘])([A-Za-zÇĞİÖŞÜçğıöşüÂÎÛâîû]{4,})(?=['’]|[^\w'’‘]|$)")
_SAPKA = {"a": "â", "i": "î", "u": "û"}
_ON_KELIME = ("baş",)   # yalnız baş + Arapça/Farsça kelime (başkahraman, başmüfettiş); ana+yasa, iç+erik gibi bölme yapılmaz


def _bulunur(wl: str) -> bool:
    return bool(wl in dictionary.HAYRAT_ANAHTAR or dictionary.lookup_exact(wl) or dictionary.lookup_with_suffix(wl)[0])


_ABD_RE = re.compile(r"^abd([üu])(?:l(?!l)([a-zçğıöşüâîû]{2,})|([tdrzsşn])(\3[a-zçğıöşüâîû]{2,}))$")


def _abd_bicim(w: str, wl: str):
    """Tur AB (22 Kasım 2026, İslam Tarihi denetimi): sözlükte olmayan Abd- adı harf-i tarifle ayrılır: Abdülvehhab -> Abdü'l-Vehhab
    (عبد الوهّاب)، Abdurrezzak -> Abdü'r-Rezzak (عبد الرزّاق)، Abduşşems، Abdüsselâm. Önceden fonetik yazılıyordu (آبدولوههاب، عبدوررززاق).
    Önce ü/u değişik biçimi sözlükte aranır (Abdürrahman -> abdurrahman عبد الرحمن); ad kısmı sözlükte tam bulunmalı."""
    m = _ABD_RE.match(wl)
    if not m or dictionary.lookup_exact(wl):
        return None
    diger = wl[:3] + ("u" if m.group(1) == "ü" else "ü") + wl[4:]
    if dictionary.lookup_exact(diger):
        return w[:3] + ("u" if m.group(1) == "ü" else "ü") + w[4:]
    ad = m.group(2) or m.group(4)
    harf = "l" if m.group(2) else m.group(3)
    if not dictionary.lookup_exact(ad):
        return None
    bas = len(w) - len(ad)
    return w[:3] + "ü'" + harf + "-" + w[bas:bas + 1].upper() + w[bas + 1:]


@lru_cache(maxsize=200000)
def _yeni_bicim(w: str):
    wl = turkish_lower(w)
    if wl.startswith("abd"):
        ab = _abd_bicim(w, wl)
        if ab:
            return ab
    if _bulunur(wl) or re.search(r"[çğışöü]", wl) and not re.search(r"[aiu]", wl):
        return None
    # 1) tek şapka (en fazla ilk 4 a/i/u): tabiydi -> tâbiydi, mahkumu -> mahkûmu
    yerler = [i for i, c in enumerate(wl) if c in _SAPKA][:4]
    for i in yerler:
        v = wl[:i] + _SAPKA[wl[i]] + wl[i + 1:]
        h = dictionary.lookup_exact(v)
        if h and str(h[1]) not in ("tr", "meal") and len(wl) >= 6:     # yalnız kelimenin tamamı (ekli tahmin yanlış köke götürüyor)
            return v if w[:1].islower() else v[:1].upper() + v[1:]
    # 2) birleşik kelime: ön kelime + sözlükte olan (en az 4 harf)
    for on in _ON_KELIME:
        if wl.startswith(on) and len(wl) - len(on) >= 4:
            kalan = wl[len(on):]
            h, ek = dictionary.lookup_with_suffix(kalan)
            kok = kalan[:len(kalan) - len("".join(ek))] if ek else kalan
            hk = dictionary.lookup_exact(kok)
            if hk and len(kok) >= 5 and str(hk[1]) in ("ar", "fa", "ar-fa", "fa-ar") and " " not in hk[0]:
                bas = w[:len(on)]
                return bas + " " + kalan
    return None


def duzelt_metin(metin: str) -> str:
    if not isinstance(metin, str):
        return metin
    return _KELIME.sub(lambda m: _yeni_bicim(m.group(1)) or m.group(1), metin)
