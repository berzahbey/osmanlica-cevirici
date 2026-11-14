"""Tur TV (14 Kasım 2026): sözlükte olmayan, Arapça/Farsça kökten türemiş kelime kökün aslî yazılışıyla kurulur.
Örnek (Stüdyo ölçümü): mucizevi موجیزوی yazılıyordu -> mucize معجزه + -vî = معجزوی (medresevî مدرسوی، midevî معدوی gibi).
Tur TV2 (14 Kasım, kitap sayımından): kök harf uyumu (yz_kayit.harf_uyumu), "kadar" ve Türkçe geniş zaman (ışıldar) kurulmaz,
-vî: Latin -a + ه kök kurulmaz (Tahâvî), -iyet: i ile biten ی kök + ت (kat'iyyet قطعیت).
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


def _kok_al3(r, bul):
    """3 harfli Arapça kök (küll, ilm) yalnız nisbe denetimi için."""
    h = bul(r)
    return h[0].strip() if h and h[1] in KOKEN and h[0].strip() else None


def _kok_al(r, bul):
    if len(r) < 4:
        return None
    h = bul(r)
    if not h or h[1] not in KOKEN or " " in h[0].strip() or not h[0].strip() or h[0].strip()[-1] in "ڭ‌" \
            or re.search("[A-Za-z]", h[0]):
        return None
    from . import yz_kayit
    if not yz_kayit.harf_uyumu(r, h[0].strip()):
        return None          # bozuk sözlük kaydı (müste -> مستحاثه): kök kullanılmaz
    return h[0].strip()


def _turet(k, bul):
    if k.endswith("kadar") or (k[-2:] in ("ar", "er") and _turkce_soz(k[:-1])):
        return None              # bukadar (bu kadar), ışıldar / yazar (Türkçe fiil + geniş zaman -r)
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
                if g.endswith("a") and o[-1:] in "هة":
                    return None              # Latin -a, Osmanlıca ه: özel ad nisbesi olabilir (Tahâvî طحاوی ≠ طه+وی)
                if g[-1:] in "ea" and o[-1:] in "هةىیت":
                    return o[:-1] + "وی"     # mucize معجزه -> معجزوی، luğat لغت -> لغوی
            return None
    # -iyet / -iyyet: kök + یت; -yet: ی ile biten kök + ت (medenî+yet)
    for ek in ("iyyet", "iyet"):
        if k.endswith(ek):
            g = k[: -len(ek)]
            o = _kok_al(g, bul)
            if o and o.endswith("ی") and g[-1:] in "iî":
                return o + "ت"               # kat'î قطعی + iyet = قطعیت (قطعییت değil)
            if o and o[-1] not in "هةا":
                return o + "یت"
    if k.endswith("yet") and k[-4:-3] in "iî":
        o = _kok_al(k[:-3], bul)
        if o and o.endswith("ی"):
            return o + "ت"
    # Tur IY: -iye / -iyye (Arapça nisbe sıfatının müennesi): nisbe kökü ی ile biter, sonuna ه gelir:
    # Arabî عربی -> Arabiye عربیه (عربی یه değil), küllî كلّی -> külliye كلّیه, fi'lî -> fi'liye. Kök gerçekten nisbe olmalı:
    # ی'siz hâli de sözlükte Arapça ve aynı yazımla (arab عرب، küll كل) — böylece veli+ye (ولی یه) gibi yönelme hâli kurulmaz.
    # Yalnız -iyye: tek başına -iye çoğu kez yönelme hâlidir (ciddiye ال-, birinciye, hakîkîye); tamlama sıfatındaki şapkasız -iye'yi
    # transliterator._izafet_iye -iyye'ye çevirir (şapkalı -îye yönelmedir: maksad-ı hakîkîye مقصد حقیقی یه).
    for ek in ("iyye",):
        if k.endswith(ek) and not bul(k + "t"):      # keyfiyye+ten aslında keyfiyyet+en (كیفیّتًا): kurulmaz
            g = k[: -len(ek)] + "i"
            h = bul(g)
            o = h[0].strip() if h and h[0].strip() else None    # nisbenin köken etiketi önemsiz (nûrî "tr" etiketli): yapı denetlenir
            if o and o.endswith("ی"):
                hb = bul(g[:-1]) if len(g) >= 4 else None
                b = hb[0].strip() if hb else None              # yapı: nisbe = kök + ی (ikisi de sözlükte; köken etiketi önemsiz)
                if b and _sade(b) == _sade(o[:-1]):
                    return o + "ه"
            if (not o or not o.endswith("ی")) and ek == "iyye":
                b = _kok_al3(g[:-1], bul) if len(g) >= 4 else None
                if b and b[-1] not in "هةاوی":
                    return b + "یه"      # nisbesi sözlükte olmayan kök (fi'l فعل -> fi'liyye فعلیه); -iyye yalnız tamlama sıfatında üretilir
            break
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


def _sade(o):
    return re.sub("[\u064B-\u0652\u0670\u200c]", "", o).replace("ي", "ی")


@lru_cache(maxsize=50000)
def _onbellekli(k, bul):
    return _turet(k, bul)


def turet(k, bul):
    """(osm, köken) ya da None. bul: türetmesiz sözlük araması (kök için)."""
    if not ACIK or not k or len(k) < 6 or not (k.isalpha() or (k.endswith("iyye") and k.replace("'", "").isalpha())):
        return None
    o = _onbellekli(k, bul)
    return (o, "turev") if o else None
