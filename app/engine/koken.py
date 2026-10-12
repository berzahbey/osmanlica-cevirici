# -*- coding: utf-8 -*-
"""Hayrat sozlugunde kelimenin kokeni (ar / tr). Eski kural yalniz harfe bakiyordu: Osmanlica yazimda ع ح ط ظ ص ض ث ذ ق غ varsa "ar".
Ama ق ط ص غ Turkce kelimelerde de yazilir (kork قورق، toplu طوپلی، sağlam صاغلام). Kural (genel, kelime listesi yok):
  - Yalniz Arapcada olan harf (ع ح ث ذ ظ ض خ), Latin'de Arapca isareti (â î û ' ʿ), sedde ya da isaretli ikizi olan kelime: Arapca.
  - Ilk hecedeki unlu kendi harfiyle yazilmamissa (kader قدر، kusur قصور، kayıt قید، tavır طور): Arapca (Turkce kelimede ilk unlu yazilir).
  - Arapca fâil kalibi (sâbık سابق، nâtık ناطق، vâkıf واقف): ikinci unlu yazilmamis 4 harf: Arapca.
  - Latin'de o/ö varsa: Turkce (Arapca kelimede o/ö yok; lokma لقمه, Sokrat سقراط ilk unlu yazilmadigi icin Arapca kalir).
  - Unlu uyumu bozuksa (kader, peygamber): Arapca/Farsca kalir; uyumluysa Turkce.
Yalniz "ar" -> "tr" duzeltmesi icin kullanilir; ق ط ص غ olmayan kayitlara dokunulmaz."""
import re

GUCLU = re.compile("[\u0639\u062d\u062b\u0630\u0638\u0636\u062e]")      # ع ح ث ذ ظ ض خ
ZAYIF = re.compile("[\u0642\u0637\u0635\u063a]")                        # ق ط ص غ
ISARET = re.compile("[\u00e2\u00ee\u00fb\u0101\u012b\u016b'\u2019\u02bf\u02be\u2018]")
_KALIN, _INCE = set("aıou"), set("eiöü")
_TR_SONEK = re.compile(r"(yor|ken|ki|leyin|mtırak|mtrak)")


def _uyumlu(w):
    v = [c for c in _TR_SONEK.sub("", w) if c in _KALIN or c in _INCE]
    return not (any(c in _KALIN for c in v) and any(c in _INCE for c in v))


_UNLU_HARFI = {"a": "\u0627", "ı": "\u06cc", "i": "\u06cc", "o": "\u0648", "u": "\u0648", "ö": "\u0648", "ü": "\u0648"}
_FAIL = re.compile(r"^[^aeıioöuü]a[^aeıioöuü][ıiu][^aeıioöuün]$")


def _ilk_unlu_yazili(w, o):
    """Latin'in ilk unlusu Osmanlicada kendi harfiyle yazilmis mi: a -> ا، ı/i -> ی، o/u/ö/ü -> و (kayıt قید، tavır طور: ی/و unsuz, unlu
    yazilmamis). Unluyle baslayan kelime آ ya da او/ای ile baslamali (Arapca اصرار، اقامت degil). e ile baslayan hece: Turkce kelimede
    ق ط ص غ ile gelmez."""
    o = o.replace("\u0651", "")
    if not o:
        return False
    if w[:1] in _KALIN or w[:1] in _INCE:
        return o[0] == "\u0622" or o[1:2] in ("\u0648", "\u06cc")
    v = next((c for c in w[1:] if c in _KALIN or c in _INCE), "")
    return w[1:2] == v and o[1:2] == _UNLU_HARFI.get(v, "-")


def turkce_mi(latin, osm, isaretli_ikiz=False):
    """Hayrat kaydi (Latin anahtar, Osmanlica yazim) Turkce kelime mi."""
    w = latin.strip()
    if isaretli_ikiz or GUCLU.search(osm) or ISARET.search(w) or "\u0651" in osm:
        return False
    if not ZAYIF.search(osm) or not _ilk_unlu_yazili(w, osm):
        return False
    if _FAIL.match(w) and len(osm.replace("\u200c", "").replace("\u0651", "")) == 4:
        return False                                  # Arapca fâil kalibi, ikinci unlu yazilmamis: sâbık سابق، nâtık ناطق، kâlıb قالب
    if "o" in w or "ö" in w:
        return True
    return _uyumlu(w)


_SAPKA = str.maketrans({"â": "a", "î": "i", "û": "u", "ā": "a", "ī": "i", "ū": "u"})


def isaretli_ikizler(satirlar):
    """Sapkasi/kesmesi atilarak turetilmis anahtarlar (sâdık -> sadık, ayni yazim): Arapca kelimenin ikizi."""
    def duz(s):
        return re.sub("['\u2019\u02bf\u02be\u2018]", "", s.translate(_SAPKA))
    isaretli = {(duz(l), o) for l, o in satirlar if ISARET.search(l)}
    return {l for l, o in satirlar if not ISARET.search(l) and (l, o) in isaretli}
