"""Kök sözlüğü (tur "kök listesi", 12 Ekim; data/hayrat_kok.tsv, tools/hayrat_kok_cikar.py ile üretilir).

Sözlükte kök + ek olarak bulunamayan kelime kural motoruna düşer ve kökü harf harf yazılır (gizleyemezler -> كیزلیهمزلر).
Kelimenin başında kök sözlüğünde bir kök varsa (Zemberek'e göre gerçek kök, yazımı Hayrat'tan), kural motorunun çıktısındaki
kök kısmı sözlükteki yazımla değiştirilir; ekler kural motorunun yazdığı gibi kalır (gizle كیزله + یه‌مزلر).
OSM_KOK=0 kapatır.
"""
import os
import re
from pathlib import Path

from . import rules

_ACIK = os.environ.get("OSM_KOK", "1") != "0"
_UNLU = "aeıioöuüâîû"
_KALIN = "aıouâû"
_SABIT_SON = ("ken", "ki", "yor", "leyin", "daş", "taş")


def _yukle():
    d = {}
    yol = Path(__file__).resolve().parent.parent / "data" / "hayrat_kok.tsv"
    if not yol.exists():
        return d
    for line in open(yol, encoding="utf-8"):
        p = line.rstrip("\n").split("\t")
        if len(p) >= 3:
            d.setdefault(p[0], {})[p[2]] = (p[1], int(p[3]) if len(p) > 3 and p[3].isdigit() else 1)   # kök -> {"N"/"V": (yazım, kanıt)}
    return d


KOK = _yukle() if _ACIK else {}


def _zemberek():
    yol = Path(__file__).resolve().parent.parent / "data" / "zemberek_kok.txt"
    return set(open(yol, encoding="utf-8").read().split()) if yol.exists() else set()


ZKOK = _zemberek() if _ACIK else set()
# Kısa kökten daha uzun Zemberek köküne giden parça yapım eki mi (birleş+ik, isim+lendir, çoğun+luk); değilse (ham+am, orta+m)
# uzun kök gerçek köktür ve kısa kök kullanılmaz.
_YAPIM = re.compile(r"^(l[aeıiuü]|c|ç|s[ıiuü]z|[dt][ıiuü]r|[ıiuü]?[nlşkt]|m[ae]|[aeıiuü]r|g[ıiuüae]|k[ıiuü]|c[ıiuü]|[ıiuü]m|[ıiuü]c)")


def _uzun_kok_engeli(w: str, L: int) -> bool:
    for L2 in range(len(w), L, -1):
        if w[:L2] in ZKOK and not _YAPIM.match(w[L:L2]):
            return True
    return False


def _uyum(kok: str, kalan: str) -> bool:
    """Ekin ilk ünlüsü kökün son ünlüsüyle uyumlu mu (kalın/ince). Sabit ekler (-ken, -ki, -yor) hariç."""
    if kalan.startswith(_SABIT_SON):
        return True
    ku = [c for c in kok if c in _UNLU]
    eu = [c for c in kalan if c in _UNLU]
    if not ku or not eu:
        return True
    return (ku[-1] in _KALIN) == (eu[0] in _KALIN)


# Kökten sonra kalan kısım gerçek bir ekle mi başlıyor (dile+k "dilek", der+gi "dergi", deme+t "demet" değil)
_FIIL_IPUCU = re.compile(r"^(y[ae]n|[aeıiuü]r(ken|d|s|l|m|$)|m[ae][ksdyzlm]|m[ae]$|[ıiuü]?yor|y?[ıiuü]p|y?[ae]bil|y?[ae]m[ae]|y?[ae]c[ae][kğ]|[ıiuü]l|[ıiuü]ş|t[ıiuü]r)")
_EK_V_UNLU = re.compile(r"^(y|r|n|l|ş|t|m[ae]|m[ıiuü]ş|d|s|k[ae]n)")            # ünlüyle biten fiil kökü: benze-t, bekle-r, gizle-yemez
_EK_V_UNSUZ = re.compile(r"^([aeıioöuü]|m[ae]|m[ıiuü]ş|d|t|s[ae]|s[ıiuü]n|c[ae]|ç[ae]|k[ae]n)")
_D = r"[dt]([ae]($|n|ki|y)|[ıiuü]($|r|m|n|k|y|s|l[ae]r))"            # -de/-den/-deki ya da -dır/-dı(m) (devre+der, yara+dılan değil)
# ünlüyle biten isim + -la/-laş/-lan/-lı/-lık: Hayrat kökü değiştiriyor (yaka+la یاقالا، karşı+lık قارشیلق): alınmaz
_N = r"n($|l[ae]$|c[ıiuü]|[ıiuü]($|n|z)|[ae]$|d|t)"                       # -n/-nle/-ncı/-nı/-nın/-nız/-na/-nda (yara+nan, yara+nır değil)
_EK_N_UNLU = re.compile(r"^(y|" + _N + r"|s[ıiuü]|l[ae]r|" + _D + r"|m|c|k[ie]|k[ae]n|ş)")
_EK_N_UNSUZ = re.compile(r"^([aeıioöuü]|l|" + _D + r"|c|ç|s[ıiuü]z|k[ie]|k[ae]n)")


_IYELIK_COGUL = re.compile(r"^[ıiuü](m[ıiuü]z|n[ıiuü]z)")


def _ek_gecerli(kok: str, kalan: str, tur: str) -> bool:
    unlu = kok[-1] in _UNLU
    if tur == "V":
        return bool((_EK_V_UNLU if unlu else _EK_V_UNSUZ).match(kalan))
    return bool((_EK_N_UNLU if unlu else _EK_N_UNSUZ).match(kalan))


# Tur A (13 Ekim): Arapça/Farsça isim + -la/-le/-lan/-len/-landır/-lendir/-laş/-leş fiil kökü (lanetle- لعنتله، faydalan- فائده‌لان،
# rızıklandır- رزقلاندیر، hoşlan- خوشلان). Kök sözlüğünde yoksa isim sözlükteki yazımıyla, ek Hayrat'taki gibi (kalında لا، incede له/ل).
_TUREV = [("landır", "لاندیر"), ("lendir", "لندیر"), ("laş", "لاش"), ("leş", "لش"), ("lan", "لان"), ("len", "لن"), ("la", "لا"), ("le", "له")]
# Türkçe fiil, Arapça/Farsça isimden türemiş değil (sunucu ölçümü, Tur A): dinle- دیڭله، ısmarla- ایصمارلا، filizlen-، havla-، horla-
_TUREV_DEGIL = {"din", "ısmar", "ismar", "filiz", "hav", "hor"}
_TUREV_KOKEN = {"ar", "fa", "ar-fa", "fa-ar", "hayrat", "sozlukler"}


def _turev(r: str):
    if os.environ.get("OSM_TUREV", "1") == "0":
        return None
    from . import dictionary
    for ek, yaz in _TUREV:
        if r.endswith(ek) and len(r) - len(ek) >= 3:
            isim = r[:-len(ek)]
            if isim in _TUREV_DEGIL:
                continue
            h = dictionary.DICTIONARY.get(isim)
            if not h or h[1] not in _TUREV_KOKEN or " " in h[0] or "\u060c" in h[0] or "N" not in KOK.get(isim, {"N": 1}):
                continue
            if h[1] == "sozlukler" and isim not in KOK:
                continue                   # şapkası düşmüş sözlük kaydı (zıp زب، süs): Hayrat'ta isim olarak görülmeli (hoş, hatır)
            if isim[-1] in _UNLU and not h[0].endswith(("\u0647", "\u0627")):
                continue                   # ünlüyle biten isim, yazımı ünlü harfiyle bitmiyor: belirsiz
            ara = "\u200c" if h[0].endswith("\u0647") else ""
            return {"V": (h[0] + ara + yaz, 1)}
    return None


def _aday(w: str, r: str, kalan: str, f):
    h = KOK.get(r) or _turev(r)
    if not h or not _uyum(r, kalan):
        return None
    if re.search("[aeıioöuü][mn]$", r) and re.match("[ıiuü]z", kalan):
        return None                        # içim+iz mi iç+imiz mi belli değil: kural motoru kalır
    if kalan[:1] == "n" and (r + "n") in ZKOK:
        return None                        # oran+la, safran: ora+n, safra+n (2. tekil iyelik) değil
    sira = ("V",) if (f or _FIIL_IPUCU.match(kalan)) else ("N", "V")
    for tur in sira:
        if tur in h and _ek_gecerli(r, kalan, tur):
            if tur == "N" and _uzun_kok_engeli(w, len(r)):
                return None                # isim kökü daha uzun bir kökün başı (ham+am "hamam", orta+m "ortam"); fiilde
            return r, h[tur][0], tur, h[tur][1]   # uygulanmaz (anla-mış'ta "anlam", işle-me'de "işlem" engel değil)
    return None


def kok_bul(w: str):
    """Aday kökler listesi [(kök, yazım, tür), ...] (en az 3 harf, arkasında gerçek bir ek) ya da None. En uzun kök önce (Hayrat'taki kanıt
    sayısına göre seçmek denendi: kap, kar, kay, sır gibi kısa kökler yanlış yere girdi, bozulan arttı).
    Kural motoru kelimeyi fiil çekimi diye ayırıyorsa (atacağız -> at + acağız) yalnız o gövdenin içindeki fiil kökleri
    aday olur. İsim ve fiil yazımı ayrı (dal دال / dal- طال)."""
    if "N" in KOK.get(w, {}):
        return None                        # kelimenin kendisi kök sözlüğünde: bölünmez (aşırı آشیری، aşır+ı değil)
    f = rules._fiil_ayir(w)
    sinir = len(f[0]) if f else len(w) - 1
    adaylar = [a for L in range(min(sinir, len(w) - 1), 2, -1) for a in [_aday(w, w[:L], w[L:], f)] if a]
    if not adaylar:
        return None
    for a in adaylar[1:]:
        if _IYELIK_COGUL.match(w[len(a[0]):]):
            return [a[:3]]                 # kısa kök + -ımız/-ınız: dil+imize (dilim+ize değil), iç+imiz
    return [a[:3] for a in adaylar]        # sırayla denenir: yerine koyma tutmazsa bir sonraki (hizmetçi -> hizmet)


def kokle(word: str, o: str):
    """Kural motorunun çıktısı o; kökü sözlükteki yazımla değiştirilmiş hâli ya da None."""
    if not KOK:
        return None
    from .alphabet import turkish_lower
    w = turkish_lower(word).strip()
    for b in kok_bul(w) or []:
        sonuc = _kokle1(w, o, *b)
        if sonuc:
            return sonuc
    return None


def _kokle1(w: str, o: str, r: str, yazim: str, tur: str):
    kalan = w[len(r):]
    if tur == "V" and yazim.endswith("\u0647") and len(yazim) > 1 and kalan[0] in "rnt":
        yazim = yazim[:-1]                 # Hayrat: ه ile biten fiil kökü r/n/t önünde yazılmaz (bekler بكلر، beslen- بسلن، benzet- بڭزت)
    adaylar = []
    for kok_l in (rules._tarihi_kok(r), r):
        for son in (False, True):
            adaylar.append(rules.transliterate_word(kok_l, treat_last_as_final=son, devam=kalan))
    for a in sorted(set(adaylar), key=len, reverse=True):
        if a and o.startswith(a):
            ek = o[len(a):]
            if yazim.endswith("\u0647") and ek.startswith("\u0647"):
                ek = ek[1:]                # kural motoru kök sonu ünlüsünü ekin başında yazmış (gizle-yen)
            if yazim.endswith("\u0627") and ek.startswith("\u0627"):
                ek = ek[1:]
            if not ek:
                return None
            if tur == "N" and r[-1] in _UNLU and re.match("n($|l[ae]$)", kalan) and ek[:1] in ("\u0646", "\u06ad"):
                ek = "\u06ad" + ek[1:]      # ünlüyle biten isim + 2. tekil iyelik -n: elbise+n البسه‌ڭ، anne+n+le آننه‌ڭله
            if yazim.endswith("\u0647") and not ek.startswith("\u200c"):
                ek = "\u200c" + ek         # bitişmeyen he + ek: كیزله‌مز
            return yazim + ek
    return None
