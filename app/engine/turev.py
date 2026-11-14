"""Tur TV (14 Kasım 2026): sözlükte olmayan, Arapça/Farsça kökten türemiş kelime kökün aslî yazılışıyla kurulur.
Örnek (Stüdyo ölçümü): mucizevi موجیزوی yazılıyordu -> mucize معجزه + -vî = معجزوی (medresevî مدرسوی، midevî معدوی gibi).
Kural sözlüğün kendi türemiş kelimelerinden çıkarıldı ve onlarla sınandı (her kelime kendisi sözlükten çıkarılarak kurulur):
-iyet %96, -âne %96, -kâr/-dâr %92-97, -nâk %100, -vî yalnız ه/ت ile biten kökte (elifle biten kökte iki yol var: semâvî سماوی / kuravî قروی, kurulmaz); sayılar tests/test_tur_tv.py. Yanlışların çoğu sözlükte zaten
bulunan kalıplaşmış kelimeler (masdar, haydar, revnak): kural yalnız kelime HİÇBİR sözlükte yoksa çalışır.
Şartlar: kök (Latin) en az 4 harf, sözlükte Arapça/Farsça kökenli, tek kelime. OSM_TUREV=0 kapatır."""
import os
import re
from functools import lru_cache

ACIK = os.environ.get("OSM_TUREV", "1") != "0"
KOKEN = {"ar", "fa", "ar-fa", "fa-ar", "sozlukler"}

# (ek, [(kökün Latin sonuna eklenecek, tür)]); uzun ek önce
_FARSCA = [("perest", "پرست"), ("hâne", "خانه"), ("hane", "خانه"), ("istân", "ستان"), ("istan", "ستان"),
           ("kâr", "كار"), ("kar", "كار"), ("dâr", "دار"), ("dar", "دار"), ("nâk", "ناك"), ("zâr", "زار"), ("gâh", "كاه"), ("gah", "كاه")]
_SESSIZ_SON = "هة"          # bu harfle biten kökten sonra Farsça ek ayrı yazılır (علاقه دار، بسته كار)


_ZK = None
_H_DUSEN = {"ders", "hapis", "post", "past", "ecz", "has", "hast", "kahv", "çayh"}   # -hane'nin h'si düşen bugünkü yazımlar


def _turkce_soz(x):
    """Zemberek (Türkçe kullanım sözlüğü) kökü mü; son ünsüz yumuşaması da (kitab -> kitap)."""
    global _ZK
    if _ZK is None:
        yol = os.path.join(os.path.dirname(__file__), "..", "data", "zemberek_kok.txt")
        try:
            _ZK = {l.split()[0].lower() for l in open(yol, encoding="utf-8") if l.strip()}
        except OSError:
            _ZK = set()
    sert = {"b": "p", "c": "ç", "d": "t", "ğ": "k"}
    return len(x) >= 2 and (x in _ZK or (x[-1:] in sert and x[:-1] + sert[x[-1]] in _ZK))


def _kok_al(r, bul):
    if len(r) < 4:
        return None
    h = bul(r)
    if not h or h[1] not in KOKEN or " " in h[0].strip() or not h[0].strip() or h[0].strip()[-1] in "ڭ‌" \
            or re.search("[A-Za-z]", h[0]):
        return None
    return h[0].strip()


def _turet(k, bul):
    # -vî / -vi (nisbe): kök -e/-a ile biter (mucize+vî, kura+vî) ya da -at (luğat+vî); -âvî'de elif kalır (safrâvî صفراوی)
    for ek in ("vî", "vi"):
        if k.endswith(ek) and len(k) > 5:
            g = k[: -len(ek)]
            if g.endswith("e") and _turkce_soz(g[:-1]):
                return None          # Türkçe "ev" birleşiği: kitabevi, imamevi, canevi (Zemberek'te kitap/imam/can var; mucizevi: muciz yok)
            for ad in (("",) if g[-1:] in "eaâ" else ()) + (("t",) if g[-1:] == "a" else ()):
                o = _kok_al(g + ad, bul)
                if not o:
                    continue
                if o.endswith("ا"):
                    return None              # elifle biten kökte iki yol var (semâvî سماوی / kuravî قروی): kurulmaz
                if g[-1:] in "ea" and o[-1:] in "هةىیت":
                    return o[:-1] + "وی"     # mucize معجزه -> معجزوی، luğat لغت -> لغوی
            return None
    # -iyet / -iyyet: kök + یت; -yet: ی ile biten kök + ت (medenî+yet)
    for ek in ("iyyet", "iyet"):
        if k.endswith(ek):
            o = _kok_al(k[: -len(ek)], bul)
            if o and o[-1] not in "هةا":
                return o + "یت"
    if k.endswith("yet") and k[-4:-3] in "iî":
        o = _kok_al(k[:-3], bul)
        if o and o.endswith("ی"):
            return o + "ت"
    # -âne / -ane (zarf/sıfat): kök + انه (ه ile biten kökte kurulmaz: bendegâne)
    for ek in ("âne", "ane"):
        if k.endswith(ek) and not k.endswith("hane") and not k.endswith("hâne") and k[: -len(ek)] not in _H_DUSEN:
            # h'si düşmüş -hane (dersane, hapisane, postane, eczane, pastane): -âne değil, kurulmaz
            o = _kok_al(k[: -len(ek)], bul)
            if o and o[-1] not in "هةا":
                return o + "انه"
    for ek, fa in _FARSCA:
        if k.endswith(ek):
            o = _kok_al(k[: -len(ek)], bul)
            if o:
                return o + (" " if o[-1] in _SESSIZ_SON else "") + fa
            return None
    return None


@lru_cache(maxsize=50000)
def _onbellekli(k, bul):
    return _turet(k, bul)


def turet(k, bul):
    """(osm, köken) ya da None. bul: türetmesiz sözlük araması (kök için)."""
    if not ACIK or not k or len(k) < 6 or not k.isalpha():
        return None
    o = _onbellekli(k, bul)
    return (o, "turev") if o else None
