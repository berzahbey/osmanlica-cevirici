# -*- coding: utf-8 -*-
"""Tur J (17 Ekim): Türkçe mealde parantez içindeki Arapça okunuşlar (el-muttaqîn, şeyâtînihim, lâ ikrâhe fî'd-dîn) Kur'an'daki
Arapça kelimeyle yazılır. Kur'an metni data/quran_arabic.json (Tanzil Uthmani); yazım harekesiz, şedde açık, standart imlâ
(Hayrat gibi: الصلاة، الربا، السماوات، كلمات).
Eşleştirme: okunuşun ünsüz iskeleti (uzun ünlü harfleri, ayın/hemze ve hareke sayılmaz, benzer harfler tek sınıf) Kur'an'daki
ardışık 1-6 kelimenin iskeletine eşit olmalı; adaylar arasında ünlü yerleriyle birlikte en benzeyen (en az %75), eşitlikte paragraf
başındaki ayet numarası ve sıklık. "el-" ile başlayan okunuşta Arapçası da ال ile başlamalı; tutmazsa "el-"siz denenir
(el-keferû -> كفروا). Eşleşmezse None: çevirici okunuşu eski yolla yazar. OSM_KURAN_OKUNUS=0 kapatır."""
import json
import re
import collections
import difflib
from pathlib import Path

DATA_FILE = Path(__file__).parent.parent / "data" / "quran_arabic.json"


def _U(s):
    return s.encode("ascii").decode("unicode_escape")


# Arapça harf -> sınıf (benzer sesler birleşik)
_AR_SINIF = {}
for _harfler, _sinif in (("\\u0628", "B"), ("\\u062a\\u0637\\u0629", "T"), ("\\u062b\\u0633\\u0635", "S"), ("\\u062c", "C"),
                         ("\\u062d\\u062e\\u0647", "H"), ("\\u062f\\u0630\\u0632\\u0636\\u0638", "D"), ("\\u0631", "R"),
                         ("\\u0634", "SH"), ("\\u063a", "G"), ("\\u0641", "F"), ("\\u0642\\u0643", "K"), ("\\u0644", "L"),
                         ("\\u0645", "M"), ("\\u0646", "N")):
    for _h in _U(_harfler):
        _AR_SINIF[_h] = _sinif if _sinif != "SH" else "X"
_AR_INCE = dict(_AR_SINIF)
for _h, _v in zip(_U("\\u0627\\u0648\\u06cc\\u064a\\u0649"), "AUIIA"):
    _AR_INCE[_h] = _v                                    # uzun ünlü harfleri (elif, vav, ye; elif maksura A)
for _h in _U("\\u0623\\u0625\\u0621\\u0626\\u0624\\u0639"):
    _AR_INCE[_h] = "'"                                   # hemze ve ayın
_AR_INCE[_U("\\u0622")] = "'A"                           # medli elif
_AR_INCE[_U("\\u0642")] = "Q"                            # Tur J2: kaf/kef ayrimi yalniz benzerlikte (baqara)
_UNLU_HARF = _U("\\u0627\\u0648\\u06cc\\u0649\\u0621\\u0629")    # kelime sonunda uzun ünlü karşılığı

_LA_SINIF = {"b": "B", "p": "B", "t": "T", "s": "S", "c": "C", "ç": "C", "h": "H", "d": "D", "z": "D", "r": "R",
             "ş": "X", "ğ": "G", "g": "G", "f": "F", "k": "K", "q": "K", "l": "L", "m": "M", "n": "N"}
_LA_INCE = dict(_LA_SINIF, q="Q", **{"â": "A", "î": "I", "û": "U", "'": "'", "v": "U", "w": "U", "y": "I"})
_HARF = "a-zçğıöşüâîûq"
_UNSUZ = "bcçdfğghjklmnprsştvyzq"

_ISARET = re.compile(_U("[\\u064b-\\u0650\\u0652-\\u065f\\u06d6-\\u06ed\\u0640]"))
_DAGGER = _U("\\u0670")
_DAGGER_YOK = re.compile(_U("(\\u0647\\u0630|\\u0647\\u0624\\u0644|\\u0630\\u0644\\u0643|\\u0644\\u0643\\u0646|\\u0627\\u0648\\u0644\\u0626\\u0643"
                            "|\\u0623\\u0648\\u0644\\u0626\\u0643|\\u0627\\u0644\\u0647|\\u0625\\u0644\\u0647|\\u0631\\u062d\\u0645\\u0646)"))
_ELIF = _U("\\u0627")
_SEDDE = _U("\\u0651")
_SUKUN = _U("\\u0652")

_INDEKS = None


def _standart(t: str) -> str:
    """Uthmani kelime -> harekesiz standart yazım (şedde kalır). Vasıl elifi -> ا; üstteki elif: و'nun üstünde و yerine ا
    (الصلاة، الربا، الحياة); ى/ي'nin üstünde yazılmaz (على); öteki yerde ا (كلمات، السماوات); هذا، ذلك، إله، الرحمن'da yazılmaz.
    Kelime başındaki idgam şeddesi (مّناسككم) yazılmaz. ي/ى -> ی (çeviricinin harfi)."""
    t = t.replace(_U("\\u0671"), _ELIF)
    duz = _ISARET.sub("", t).replace(_DAGGER, "")
    if _DAGGER in t and not _DAGGER_YOK.search(duz):
        t = t.replace(_U("\\u0648") + _DAGGER, _ELIF)
        t = re.sub(_U("(?<=[\\u0649\\u064a])\\u0670"), "", t)
        t = re.sub(_U("\\u0640?\\u0670"), _ELIF, t)
    duz = _ISARET.sub("", t).replace(_DAGGER, "").replace(_SUKUN, "")
    duz = re.sub(_ELIF + "{2,}", _ELIF, duz)
    duz = re.sub("^(.)" + _SEDDE, r"\1", duz)
    return duz.replace(_U("\\u064a"), _U("\\u06cc"))      # elif maksura eşleştirmede A sayılır; çıktıda ی olur


def _ar_iskelet(t: str) -> str:
    return "".join(_AR_SINIF.get(c, "") for c in t)


def _ar_ince(t: str) -> str:
    return "".join(_AR_INCE.get(c, "") for c in t.replace(" ", ""))


def _la_hazirla(s: str) -> str:
    s = s.lower().replace("’", "'").replace("‘", "'").replace("ʿ", "'").replace("ʾ", "'")
    s = re.sub(r"(?<![" + _HARF + r"'])e([" + _UNSUZ + r"])\1", r"el-\1", s)       # esselvâ -> el-selvâ
    s = re.sub(r"(?<![" + _HARF + r"'])el(?=[" + _UNSUZ.replace("l", "") + r"])", "el-", s)   # elğayyi -> el-ğayyi
    s = re.sub(r"([" + _UNSUZ + r"])-\1", r"l|\1", s)                               # es-sufehâ, fî'd-dîn, ven-nesle
    s = re.sub(r"(?<![" + _HARF + r"'])[ea]l-", "l|", s).replace("'l-", "l|").replace("l-", "l|")
    s = re.sub(r"(?<![" + _HARF + r"'])[aeıiouâîû]", "'", s)   # kelime başı ünlü = elif/hemze (el-esmâe, innâ)
    return re.sub(r"([" + _UNSUZ + r"])\1", r"\1", s.replace("|", ""))             # muttaqîn: çift harf (şedde) tek


def la_iskelet(s: str) -> str:
    return "".join(_LA_SINIF.get(c, "") for c in _la_hazirla(s))


def _la_ince(s: str) -> str:
    return "".join(_LA_INCE.get(c, "") for c in _la_hazirla(s))


def _cift_tek(k: str) -> str:
    return re.sub(r"(.)\1", r"\1", k)


def _yukle():
    global _INDEKS
    if _INDEKS is None:
        d = json.load(open(DATA_FILE, encoding="utf-8"))
        idx = collections.defaultdict(collections.Counter)
        idx_c = collections.defaultdict(set)          # çift harfi tek iskelet (Allah'daki iki lam: allâh)
        ayet = collections.defaultdict(list)          # ayet numarası -> o numaralı ayetlerin standart yazımı (eşitlikte ipucu)
        on_ek = (_U("\\u0648"), _U("\\u0641"))
        harf_var = re.compile(_U("[\\u0621-\\u064a\\u0671]"))
        for sure in d.values():
            for v in sure:
                toks = [x for x in v["text"].split() if harf_var.search(x)]
                std = [_standart(x) for x in toks]
                ayet[v["verse"]].append(" " + " ".join(std) + " ")
                isk = [_ar_iskelet(x) for x in std]
                for i in range(len(toks)):
                    for n in range(1, 7):
                        if i + n > len(toks):
                            break
                        k = "".join(isk[i:i + n])
                        if len(k) > 26:
                            break
                        yaz = " ".join(std[i:i + n])
                        idx[k][yaz] += 1
                        idx_c[_cift_tek(k)].add(k)
                        if std[i][:1] in on_ek and len(isk[i]) >= 3:     # vav/fa ön eki olmadan (fe-rihânun -> rihân)
                            y2 = " ".join([std[i][1:]] + std[i + 1:i + n])
                            k2 = k[1:] if std[i][:1] == on_ek[1] else k
                            idx[k2][y2] += 0
                            idx_c[_cift_tek(k2)].add(k2)
        _INDEKS = (idx, ayet, idx_c)
    return _INDEKS


def _varyantlar(okunus: str):
    """(iskelet, ince) çiftleri; kelime sonu tenvin: -en/-an elifle (endâden, metâ'an), -un/-in yazılmaz (halîfeten)."""
    secenek = []
    for w in okunus.split():
        v = [(w, 0)]
        if re.search(r"[ae]n$", w.lower()) and len(w) > 3:
            v += [(w[:-2] + "â", 0), (w[:-1], 1)]   # Tur J2: elifli tenvin once
        elif re.search(r"[ıiuoâîû]n$", w.lower()) and len(w) > 3:
            v.append((w[:-1], 0))
        secenek.append(v)
    out = [[]]
    for v in secenek:
        out = [o + [x] for o in out for x in v][:27]
    return [(la_iskelet(" ".join(x for x, _ in o)), _la_ince(" ".join(x for x, _ in o)), sum(r for _, r in o)) for o in out]


def bul(okunus: str, ayet_no=None, esik: float = 0.75):
    """Okunuşun Kur'an'daki Arapça yazımı ya da None."""
    if __import__("os").environ.get("OSM_KURAN_OKUNUS", "1") == "0":
        return None
    idx, ayet, idx_c = _yukle()
    hazir = _la_hazirla(okunus)
    tarifli = bool(re.match(r"(?:[ea]l-|e([" + _UNSUZ + r"])-?\1)", okunus.lower()))
    bas_v = hazir[:1] in "vw"
    son_uzun = okunus.rstrip()[-1:] in "âîû"
    sinir = len(okunus.split()) + len(re.findall("['’‘-]", okunus)) + len(re.findall("llâh", okunus.lower()))
    for gecis in (0, 1):
        sonuc = _bul_gecis(okunus, ayet_no, esik, gecis, idx, ayet, idx_c, tarifli, bas_v, son_uzun, sinir)
        if sonuc or not tarifli:
            return sonuc
    return None


def _bul_gecis(okunus, ayet_no, esik, gecis, idx, ayet, idx_c, tarifli, bas_v, son_uzun, sinir):
    vav = _U("\\u0648")
    tarif = tuple(_U(x) for x in ("\\u0627\\u0644", "\\u0644\\u0644", "\\u0628\\u0627\\u0644", "\\u0641\\u0627\\u0644",
                                  "\\u0648\\u0627\\u0644", "\\u0643\\u0627\\u0644"))
    adaylar = {}
    for k, ince, sira in _varyantlar(okunus):
        if len(k) < 2:
            continue
        if gecis == 0:
            kk, ii = k, ince
        elif tarifli and k.startswith("L"):
            kk, ii = k[1:], ince[1:]                    # mealdeki "el-" Kur'an'da yok (el-keferû)
        else:
            continue
        anahtarlar = [kk] if idx.get(kk) else sorted(idx_c.get(_cift_tek(kk), ()))
        for a in anahtarlar:
            for y in idx.get(a, ()):
                yy = y[1:] if y[:1] == vav and not bas_v and len(y) > 3 else y
                if tarifli and gecis == 0 and not yy.startswith(tarif):
                    continue                            # "el-" ile başlayan okunuşun Arapçası da elif-lam ile başlar
                if son_uzun and yy[-1:] not in _UNLU_HARF:
                    continue                            # uzun ünlüyle biten okunuş (keferû) ünsüzle biten kelime değil
                oran = difflib.SequenceMatcher(None, ii, _ar_ince(yy)).ratio()
                if len(yy.split()) > sinir:
                    oran -= 0.15
                p = (round(oran, 2), -sira, 1 if ayet_no and any(" " + y + " " in m for m in ayet.get(ayet_no, ())) else 0,
                     idx[a][y], -len(yy))
                if yy not in adaylar or p > adaylar[yy]:
                    adaylar[yy] = p
    if not adaylar:
        return None
    en = max(adaylar, key=lambda y: adaylar[y])
    return en.replace(_U("\\u0649"), _U("\\u06cc")) if adaylar[en][0] >= esik else None
