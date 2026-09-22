# -*- coding: utf-8 -*-
"""
Kural tabanli harf cevirici (fallback engine) - SAF TURKCE kelimeler icin.

Osmanlica imlasinin KELIME POZISYONUNA gore degisen unlu yazim kurallarini
uygular (kaynak: Fikriyat Osmanlica dersleri, Vikikitap Osmanlica/Eklerin
Yazimi ve Arapca Ses Bilgisi maddeleri):

  KELIME BASI:
    e, a  -> elif (ا)
    i, i  -> ye (ی)
    o,o,u,u -> elif+vav (او) [vav tek basina kelime basinda unsuz sayilir]

  KELIME ORTASI:
    a, e, i -> YAZILMAZ (kisa unlu, Arapca imla gelenegi)
    i       -> ye (ی)
    o,o,u,u -> vav (و)

  KELIME SONU (her zaman yazilir):
    e       -> he (ه)   [ELIF DEGIL - "ece" gibi kelimelerde gorulen kural]
    a       -> elif (ا)
    i, i    -> ye (ی)
    o,o,u,u -> vav (و)

  IKI UNLU YAN YANA (hiatus): her zaman yazilir, pozisyonuna gore ayni
  taşıyıcı kurallari uygulanir.

ISTISNALAR: Bu kurallara uymayan, imlasi yerlesmis birkac kelime icin
EXCEPTIONS sozlugu kullanilir - kural motoruna dusmeden dogrudan sonuc
dondurulur. Bu liste zaman icinde, karsilasildikca genisletilmelidir;
simdilik bilinen birkac ornekle baslar (TAM/KESIN degildir).
"""
from .alphabet import (
    ELIF, VAV, YE, HE, MEDD_ELIF, turkish_lower,
    KALIN_KEF, KALIN_GEF, INCE_KEF, INCE_GEF,
    CONSONANT_MAP_TURKISH, KALIN_UNLULER, INCE_UNLULER, TUM_UNLULER,
)

# Kesin olarak bilinen, kural motoruna uymayan yerlesik yazimlar.
# Format: latin -> osmanlica
# NOT: Bu liste TAM DEGILDIR, karsilasilan istisnalar buraya eklenmelidir.
EXCEPTIONS = {
    "su": "صو",
    "var": "وار",
    "bir": "بر",
    "ben": "بن",
    "sen": "سن",
    "biz": "بز",
    "bu": "بو",
    "şu": "شو",
    "ne": "نه",
    "gibi": "گبی",
    "için": "ايچون",
    "ile": "ایله",
    "ve": "و",
    "neden": "ندن",
    "tekvîr": "تکویر",
    "tekvir": "تکویر",
    "küvvirat": "کورت",
    "küvviret": "کورت",
    "kuvvirat": "کورت",
    "succirat": "سجرت",
    "kuşitat": "کشطت",
    "küşitat": "کشطت",
    "hunnes": "خنس",
    "baş": "باش",
    "başıboş": "باشیبوش",
    "kadir": "قادر",
    "kadîr": "قادر",
    "hesap": "حساب",
    "hesabı": "حسابی",
    "hesabını": "حسابنی",
    "hesabına": "حسابنا",
    "kaya": "قایا",
    "yirmi": "یگرمی",
    "iki": "ایکی",
    "üç": "اوچ",
    "dört": "دورت",
    "beş": "بش",
    "altı": "آلتی",
    "yedi": "یدی",
    "sekiz": "سکز",
    "dokuz": "طوقوز",
    "on": "اون",
    "otuz": "اوتوز",
    "kırk": "قرق",
    "elli": "اللی",
    "altmış": "آلتمش",
    "yetmiş": "یتمش",
    "seksen": "سکسان",
    "doksan": "طوقسان",
    "yüz": "یوز",
    "bin": "بیڭ",
    "etmek": "ایتمك",
    "vermek": "ویرمك",
    "ermek": "ایرمك",
    "demek": "دیمك",
    "gece": "گیجه",
    "güveyi": "گوکی",
    "üveyi": "اوکی",
    "dövmek": "دوکمك",
    "güvercin": "گوکرجین",
    "kuzu": "قوزی",
    "kuru": "قوری",
    "doğru": "طوغری",
    "bun": "بون",
    "ı": "ی",
    "i": "ی",
    "u": "و",
    "ü": "و",
}


def _harmony_class(word: str) -> str:
    for ch in reversed(word):
        if ch in KALIN_UNLULER:
            return "kalin"
        if ch in INCE_UNLULER:
            return "ince"
    return "kalin"


def _resolve_k_g(ch: str, harmony: str) -> str:
    if ch == "k":
        return KALIN_KEF if harmony == "kalin" else INCE_KEF
    if ch in ("g", "ğ"):
        return KALIN_GEF if harmony == "kalin" else INCE_GEF
    return None


def _vowel_letter(ch: str, position: str) -> str:
    """position: 'initial' | 'medial' | 'final'
    Kelime pozisyonuna gore dogru tasiyici harfi dondurur.
    Medial'de a/e/i icin bos string (yazilmaz) donebilir.
    UZUN unluler (a,i,u) pozisyona bakilmaksizin HER ZAMAN yazilir -
    Osmanlica imlasinda uzun unluler kisa unluler gibi dusurulmez."""
    if ch == "â":
        return ELIF
    if ch == "î":
        return YE
    if ch == "û":
        return VAV
    if position == "final":
        if ch == "e":
            return HE
        if ch == "a":
            # Kelime sonu "a" sesi: ISIM (ve isme gelen -a datif eki
            # dahil) icin HE, FIIL (ve fiile gelen -a eki) icin ELIF
            # kullanilir (kaynak: Vikikitap Osmanlica dersleri). Isimler
            # coplu fiil koklerinden COK daha yaygin oldugu icin varsayilan
            # HE - fiil kokleri (basla-, ara-, oyna- gibi) karsilastikca
            # EXCEPTIONS sozlugune elif olarak eklenir.
            return HE
        if ch in ("i", "ı"):
            return YE
        if ch in ("o", "ö", "u", "ü"):
            return VAV
    elif position == "initial":
        if ch in ("e", "a"):
            return ELIF
        if ch in ("i", "ı"):
            return ELIF + YE
        if ch in ("o", "ö", "u", "ü"):
            return ELIF + VAV
    else:  # medial
        if ch in ("o", "ö", "u", "ü"):
            return VAV
        if ch in ("i", "ı"):
            return YE
        if ch == "a":
            return ELIF
        if ch == "e":
            return ""
    return ELIF  # beklenmeyen durum icin guvenli varsayilan


def _historicize_participle(word: str) -> str:
    """Modern Turkce -dugu/-dugu/-tugu/-tugu (ortaç eki) yuvarlak
    unluyle yazilir, ama gercek/tarihsel Osmanlica telaffuzu duz
    unluyledir (-digi/-digi) - bu yuzden bu Latin girdiyi donusturmeden
    once "tarihsel" forma ceviriyoruz. Kanit: 3. cogul hali hala duz
    unluyle "gordukleri" (gorduguleri degil)."""
    word = word.replace("duğu", "dığı").replace("düğü", "diği")
    word = word.replace("tuğu", "tığı").replace("tüğü", "tiği")
    return word


def transliterate_word(word: str, treat_last_as_final: bool = True) -> str:
    """Tek bir Turkce kelimeyi (Latin harfli, kucuk harfli) Osmanlica
    yazimina cevirir. Once EXCEPTIONS sozlugune bakar."""
    word = turkish_lower(word).strip()
    word = _historicize_participle(word)
    if not word:
        return ""

    if word in EXCEPTIONS:
        return EXCEPTIONS[word]

    harmony = _harmony_class(word)
    n = len(word)
    out = []

    seen_vowel = False
    for i, ch in enumerate(word):
        # SADECE "a" harfi, kelimenin ilk unlusu oldugunda (onunde tek
        # bir unsuz olsa bile) "kelime basi" kuralina gore yazilir -
        # orn. "yaz-" -> yaz, "yarat-" -> yarat. Diger unluler (e, i,
        # i, o, o, u, u) eski (index==0) davranisini korur - ozellikle
        # yuvarlak unluler onlerinde bir unsuz varsa elif+vav ALMAMALI,
        # sadece tek vav yeterlidir (orn. "gog-e" -> tek vav, elif
        # gerekmez cunku "g" zaten kelimeyi baslatiyor).
        is_first = (not seen_vowel) if ch == "a" else (i == 0)
        is_last = (i == n - 1) and treat_last_as_final
        prev_is_vowel = i > 0 and word[i - 1] in TUM_UNLULER

        if ch in TUM_UNLULER:
            if is_first:
                letter = _vowel_letter(ch, "initial")
            elif is_last:
                letter = _vowel_letter(ch, "final")
            elif prev_is_vowel:
                # hiatus: iki unlu yan yana - "final" kuraliyla yaz (her zaman gorunur olsun)
                letter = _vowel_letter(ch, "final")
            else:
                letter = _vowel_letter(ch, "medial")
            # "ilk unlu" sayilmak icin GERCEKTEN bir harf uretilmis
            # olmasi gerekir - sadece "bir unluye denk gelindi" yetmez.
            # Aksi halde dusen (medial, sessiz) bir "e" gibi, kendisinden
            # sonraki asil onemli unluyu (orn. "hesaBI" -> "a") yanlislikla
            # "ilk degil" sayip dusurebilir.
            if letter:
                seen_vowel = True
            out.append(letter)
        elif ch in ("k", "g", "ğ"):
            resolved = _resolve_k_g(ch, harmony)
            if ch == "ğ" and is_last:
                # kelime sonu yumusak g genelde onceki unluyu uzatir,
                # ayri harf olarak yazilmayabilir - yaklasik olarak yine yaziyoruz
                out.append(resolved)
            else:
                out.append(resolved)
        elif ch in CONSONANT_MAP_TURKISH and CONSONANT_MAP_TURKISH[ch]:
            out.append(CONSONANT_MAP_TURKISH[ch])
        elif ch.isalpha():
            out.append(ch)
        else:
            out.append(ch)

    return "".join(out)


# --- Ek (suffix) farkinda transliterasyon ---
from .dictionary import SUFFIXES  # noqa: E402


SUFFIX_NO_VOWEL = {"ler": "لر", "lar": "لر"}


SUFFIX_NO_VOWEL = {"ler": "لر", "lar": "لر"}


def _transliterate_suffix(suf: str, harmony: str) -> str:
    if suf in SUFFIX_NO_VOWEL:
        return SUFFIX_NO_VOWEL[suf]
    n = len(suf)
    out = []
    for i, ch in enumerate(suf):
        is_last = (i == n - 1)
        if ch in TUM_UNLULER:
            position = "final" if is_last else "medial"
            letter = _vowel_letter(ch, position)
            out.append(letter)
        elif ch in ("k", "g", "ğ"):
            out.append(_resolve_k_g(ch, harmony))
        elif ch in CONSONANT_MAP_TURKISH and CONSONANT_MAP_TURKISH[ch]:
            out.append(CONSONANT_MAP_TURKISH[ch])
        else:
            out.append(ch)
    return "".join(out)

def transliterate_word_with_suffix(word: str) -> str:
    """Kelimeyi mumkunse kok+ek olarak ayirir. Kok normal (pozisyon
    farkinda) kurallarla, ek ise kendi kurallariyla cevrilir."""
    word = turkish_lower(word).strip()
    word = _historicize_participle(word)
    if not word:
        return ""

    if word in EXCEPTIONS:
        return EXCEPTIONS[word]

    harmony = _harmony_class(word)

    # Once, EXCEPTIONS sozlugune ulasana kadar ust uste ek soymayi
    # dene (maks 3 ek, orn. "kadir"+"ler"+"dir"). SADECE boyle bir kok
    # gercekten bulunursa bu yol kullanilir - aksi halde asagidaki
    # eski (tek ek) davranisina donulur, boylece mevcut dogru
    # calisan kelimelerde regresyon riski alinmaz.
    remaining = word
    suffixes_found = []
    for _ in range(3):
        best_suf = None
        for suf in SUFFIXES:
            if remaining.endswith(suf) and len(remaining) - len(suf) >= 2:
                if best_suf is None or len(suf) > len(best_suf):
                    best_suf = suf
        if not best_suf:
            break
        suffixes_found.append(best_suf)
        remaining = remaining[: -len(best_suf)]
        if remaining in EXCEPTIONS:
            result = EXCEPTIONS[remaining]
            for suf in reversed(suffixes_found):
                result += _transliterate_suffix(suf, harmony)
            return result

    # EXCEPTIONS'a ulasilamadi - guvenli, eski (tek ek) davranisa don
    best_suf = None
    for suf in SUFFIXES:
        if word.endswith(suf) and len(word) - len(suf) >= 2:
            if best_suf is None or len(suf) > len(best_suf):
                best_suf = suf

    if best_suf:
        stem = word[: -len(best_suf)]
        return transliterate_word(stem, treat_last_as_final=False) + _transliterate_suffix(best_suf, harmony)

    return transliterate_word(word)


def transliterate_text_fallback(text: str) -> str:
    import re
    tokens = re.findall(r"[\wâîû]+|[^\w\s]|\s+", text, flags=re.UNICODE)
    result = []
    for tok in tokens:
        if tok.strip() and tok[0].isalpha():
            result.append(transliterate_word_with_suffix(tok))
        else:
            result.append(tok)
    return "".join(result)
