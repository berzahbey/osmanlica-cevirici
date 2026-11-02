"""Tur W (2 Kasım 2026): sözlükte olmayan, Arapça görünümlü kelime OpenITI sıklık listesindeki yazımla yazılır.
Kural motoru böyle kelimeleri harf harf yazıyordu (nübüvve نوبوووه, kayyım قایییم, musannef موساننف, Heysemî حیسمی).
Liste: data/arapca_siklik.tsv.gz (araclar/oneri.py ile aynı; 14 müellifin 172 eseri, 21 milyon kelime).
Kural genel: kök Arapça görünümlü olmalı (şapka, çift ünsüz, ünlü uyumu bozuk, mü-/te- başı, -iyet), aday iskeleti Latin
yazımla hizalanmalı (oneri.uyum < 1) ve listede en az ESIK kez geçmeli; yoksa kural motorunun yazımı kalır.
OSM_TUR_W=0 ile kapanır (ölçüm için)."""
import functools
import gzip
import math
import os
import re
import sys

ESIK = int(os.environ.get("OSM_TUR_W_ESIK", "100"))
_YOL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "arapca_siklik.tsv.gz")
_oneri = None
_INCE, _KALIN = set("eiöüî"), set("aıouâû")


def acik():
    return os.environ.get("OSM_TUR_W", "1") != "0" and os.path.exists(_YOL)


def arapca_gibi(k):
    """araclar/kitap_raporu.py ile aynı ölçüt."""
    if re.search("[çğö]", k):
        return False
    if re.search("[âîû]", k) or re.search(r"([bcdfghjklmnprsştvyz])\1", k):
        return True
    vs = [c for c in k if c in _INCE | _KALIN]
    if vs and not (all(c in _INCE for c in vs) or all(c in _KALIN for c in vs)):
        return True
    return bool(re.match(r"(mü|mu|te|ta)", k) and len(k) >= 6) or bool(re.search(r"(iyet|iyat)$", k))


def _yukle():
    global _oneri
    if _oneri is None:
        import importlib.util
        yol = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_oneri_cekirdek.py")
        spec = importlib.util.spec_from_file_location("_oneri_cekirdek", yol)
        _oneri = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_oneri)
        _oneri.yukle(_YOL)
    return _oneri


@functools.lru_cache(maxsize=50000)
def yazim(kok):
    """Kökün OpenITI yazımı ya da None."""
    if len(kok) < 4 or re.search("[oö]", kok) or not arapca_gibi(kok):   # Arapçada o/ö yok (diyalog تلك olmasın)
        return None
    # Tur W2: yalnız güçlü Arapça işareti olan kök: şapka, ünlü arası şedde (musannef, kayyım), aynı iki ünlü (kıraat), -iye/-iyet.
    # Ünlü uyumu bozukluğu tek başına yetmez: OCR'da ş/ğ/ı'sı düşmüş Türkçe (yaptigi یبتغی, asagidaki, berbat) ve yabancı ad karışır.
    guclu = re.search("[âîû]", kok) or re.search(r"[aeıiuüâîû]([bcdfghjkmnprsştvyz])\1([aeıiuüâîû]|$)", kok) \
        or re.search(r"(aa|ee|ii|uu|üü)", kok) or re.search(r"iy+[ae]t?$", kok)
    if not guclu or (len(kok) < 5 and not re.search("[âîû]", kok)):
        return None
    if kok.startswith("ı"):
        return None          # ı ile başlayan kelime Türkçedir (ıssı; اثنین değil)
    if re.search(r"(ie|ea|ai|au|ou|ei|eu|oi)", kok):
        return None          # Türkçe/Arapça yazımda olmayan ünlü çifti: yabancı ad (Pierre, Maurice, Essai)
    if "p" in kok:
        return None          # Arapçada p yok: yabancı ad (Lapanne, Patrik)
    if re.search(r"[uü][tn]$", kok) and not re.search("[âîû]", kok):
        return None          # Arapça hâl eki parçası (Muhibbüt-): eksik kelime
    for y, n in _yukle().oner(kok) or []:     # Tur W2: ilk uygun aday (kaziye: قاضی elenir, قضیه alınır)
        if n >= ESIK and _uygun(kok, y):
            return y
    return None


def _uygun(kok, y):
    if re.search("[\u0639\u0621\u0623\u0626\u0624]", y[1:-1]) and not re.search("[aeıiuüâîû]{2}", kok):
        return None          # kelime içi ayın/hemze Latin'de ünlü çifti olarak görünür (nümâ نما; Melâmet ملامت, ملائمت değil)
    if re.search(r"([bcdfghjklmnprsştvyz])\1a[^aeıiuüâîû]$", kok) and "\u0627" not in y[-3:]:
        return None          # fa''âl kalıbının a'sı yazılır (Hammad حماد, Sellam سلام; حمد/سلم değil)
    if re.match("k[aıu]", kok) and y.startswith("\u0643"):
        return None          # kısa kalın ünlülü k- ق (kafiye قافیه, كافیه değil; kâfir şapkalıdır)
    if "g" in kok and not re.search("[\u063a\u06af]", y):
        return None          # g Arapça kelimede غ (Râgıb راغب, راكب değil)
    if y.startswith("\u0627\u0644"):
        return None          # harf-i tarifli aday (elma -> الماء): Latin yazımda el- yoksa alınmaz
    if re.search("[ae]$", kok) and y[-1] not in "\u0647\u0629\u0627\u0621\u06cc\u064a\u0649\u0639":
        return None          # sondaki a/e yazılır (kaziye قضیه, قاضی değil; fâzılâne فاضلانه)
    if kok.endswith("e") and y[-1] not in "\u0647\u0629":
        return None          # sondaki e ه ile (Hanîfe حنیفه; Lapanne لبنی, Hanffe حنفی değil)
    if re.search("[ae][âîû]", kok) and not re.search("[\u0639\u0622]", y):
        return None          # kısa+uzun ünlü arası ayındır (feûlün فعولن, فأول değil)
    if kok[0] not in "aeıioöuüâîû" and y[0] in "\u0627\u0623\u0622\u0625\u0639":
        return None          # ünsüzle başlayan kelimeye baştan elif/ayın eklenmez (nümâ نما, انما değil)
    if re.match("[\u0627\u0623\u0622][\u0639\u0621]", y):
        return None          # âver آور (أعور değil)
    yn = y.replace("\u064a", "\u06cc").replace("\u0649", "\u06cc")
    if "iy" in kok and "\u06cc" not in yn:
        return None          # -iy- ی ile yazılır (maddiye مادیه, مطعم değil)
    if re.search("iy+[ae]t$", kok) and not re.search("\u06cc[\u062a\u0629]$", yn):
        return None          # -iyet یت (şebâbiyet شبابیت, شبابت değil)
    if kok.count("\u00ee") > yn.count("\u06cc") or kok.count("\u00fb") > yn.count("\u0648") \
            or kok.count("\u00e2") > sum(yn.count(c) for c in "\u0627\u0622\u06cc\u0623"):
        return None          # uzun ünlüler (â î û) yazılır (takvîm تقویم, تقوم değil)
    if re.search("iy+e$", kok) and not re.search("\u06cc[\u0647\u0629]$", yn):
        return None          # -iye: ی + ه (asliye اصلیه, اصله değil)
    if re.search("[aeıiuüâîû]{2}", kok) and not re.search("[\u0639\u0621\u0623\u0626\u0624]", y):
        return None          # yan yana iki ünlü arasında ayın/hemze vardır (maâlî معالی, مالی değil)
    return y


_FIIL = re.compile(r"(ıyor|iyor|uyor|üyor|yor|mak|mek|m[ıi]ş|acak|ecek|[dt][ıiuü]k(?=.))|[dt][ıiuü](m|n|k|nız|niz|lar|ler)?$")


_ANLAMLI = None


def _anlamli():
    """Anlamı bağlama göre yazılan kelimeler (havâs حواس/خواص): kendi karar düzenleri var, OpenITI karışmaz."""
    global _ANLAMLI
    if _ANLAMLI is None:
        _ANLAMLI = set()
        d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
        for ad in ("anlam_farki_kelimeler.tsv", "baglam_kurallari.tsv"):
            try:
                for s in open(os.path.join(d, ad), encoding="utf-8"):
                    if s.strip() and not s.startswith("#"):
                        _ANLAMLI.add(s.split("\t")[0].strip())
            except OSError:
                pass
    return _ANLAMLI


def kelime(word, tireden_sonra=False):
    """Sözlükte ve kök sözlüğünde olmayan kelime: OpenITI kökü + Türkçe ekler; uygun değilse None.
    tireden_sonra: birleşik kelimenin ikinci parçası (saadet-âver, haşmet-nümâ: Farsça ek) -> kullanılmaz."""
    if tireden_sonra or not acik():
        return None
    from . import dictionary as D, rules as R
    from .alphabet import turkish_lower
    if re.search("[^A-Za-zÇĞİÖŞÜçğıöşüÂÎÛâîû]|[wxqWXQ]", word):
        return None          # yabancı harf (daß, w, x, q): yabancı kelime
    w = turkish_lower(word)
    if not re.fullmatch("[a-zçğıöşüâîû]+", w) or _FIIL.search(w):
        return None

    def bol(x, n, ilk=True):
        # n'li hâl ekleri (-ne, -nde, -ndeki...) yalnız iyelikten sonra gelir; kökün hemen ardından gelmez (fâzılâ+neleri değil)
        return not x or (n > 0 and any(x.startswith(e) and not (ilk and re.match("n[aeıiuü]|nd", e)) and bol(x[len(e):], n - 1, False)
                                       for e in D._ISIM_EKLERI))
    for L in range(len(w), 3, -1):
        k, ek = w[:L], w[L:]
        if ek and not bol(ek, 3):
            continue
        if not ek and re.search(r"([bcdfghjklmnprsştvyz])\1$", k):
            continue         # ek almamış sondaki şedde eksik kelimedir (Neseff, Bakiyy); müstakarr-ı olur
        if "iy" in w and w.rfind("iy") + (3 if w[w.rfind("iy") + 2:w.rfind("iy") + 3] in "aeıiuü" and w.rfind("iy") + 2 < len(w) else 2) > L:
            continue         # -iye kökte kalır (asliyemizde اصلیه‌مزده; umûmiyedeki)
        if k in _anlamli():
            return None
        y = yazim(k)
        if y:
            return y + (R.ekleri_yaz(k, [], [ek], R._harmony_class(w)) if ek else "")
    return None
