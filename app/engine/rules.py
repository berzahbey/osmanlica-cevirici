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
import re
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
    "tekvîr": "تكویر",
    "tekvir": "تكویر",
    "küvvirat": "كورت",
    "küvviret": "كورت",
    "kuvvirat": "كورت",
    "succirat": "سجرت",
    "kuşitat": "كشطت",
    "küşitat": "كشطت",
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
    "iki": "ایكی",
    "üç": "اوچ",
    "dört": "دورت",
    "beş": "بش",
    "altı": "آلتی",
    "yedi": "یدی",
    "sekiz": "سكز",
    "dokuz": "طوقوز",
    "on": "اون",
    "otuz": "اوتوز",
    "kırk": "قرق",
    "elli": "اللی",
    "altmış": "آلتمش",
    "yetmiş": "یتمش",
    "seksen": "سكسان",
    "doksan": "طوقسان",
    "yüz": "یوز",
    "bin": "بیڭ",
    "etmek": "ایتمك",
    "vermek": "ویرمك",
    "ermek": "ایرمك",
    "demek": "دیمك",
    "gece": "گیجه",
    "güveyi": "گوكی",
    "üveyi": "اوكی",
    "dövmek": "دوكمك",
    "güvercin": "گوكرجین",
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


def _kg_uyum(word: str, i: int, varsayilan: str) -> str:
    """k/g/ğ'nin kalın/inceliği yanındaki ünlüden (kelimenin son ünlüsünden değil): bugün -> بوگون, günah -> گناه,
    çıkabilir -> چیقابیلیر. Önce hemen sonraki ünlü (k/g'den sonra â/û inceltir: kâr, gâh), sonra önceki ünlü,
    o da yoksa sonraki ilk ünlü."""
    nxt = word[i + 1] if i + 1 < len(word) else ""
    if word[i] in ("k", "g") and nxt in ("â", "û"):
        return "ince"
    if nxt in KALIN_UNLULER:
        return "kalin"
    if nxt in INCE_UNLULER:
        return "ince"
    for c in reversed(word[:i]):
        if c in KALIN_UNLULER:
            return "kalin"
        if c in INCE_UNLULER:
            return "ince"
    for c in word[i + 1:]:
        if c in KALIN_UNLULER:
            return "kalin"
        if c in INCE_UNLULER:
            return "ince"
    return varsayilan


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




def _historicize_et_ver(word: str) -> str:
    """etmek/vermek aileleri: fiil kok+ek birlesimlerini tarihsel
    (Osmanlica) forma cevirir: et->it, ed->id (unsuz/unlu once/sonra
    kurallarina gore), ver->vir. SADECE tam kelime eslesmesiyle calisir
    (regex/prefix DEGIL) - boylece 'etraf', 'etki', 'edebiyat', 'vergi'
    gibi alakasiz kelimeler asla etkilenmez. Kapsamadigi nadir cekim
    bicimlerini karsilastikca genisletiriz."""
    et_suffixes = ["mek", "meden", "meyen", "meyip", "meksizin", "meli",
                   "melisin", "meliyim", "meliyiz", "meliler",
                   "tig", "tigi", "tigin", "tigim", "tigimiz",
                   "sin", "sinler", "ti", "tim", "tin", "tik", "tiniz", "tiler"]
    for suf in et_suffixes:
        if word == "et" + suf:
            return "it" + suf
    ed_suffixes = ["iyor", "iyorum", "iyorsun", "iyoruz", "iyorsunuz", "iyorlar",
                   "er", "erim", "ersin", "eriz", "ersiniz", "erler",
                   "ecek", "ecegim", "eceksin", "ecegiz", "ecekler",
                   "ilen", "ilmis", "ilmistir", "ilecek", "ilir"]
    for suf in ed_suffixes:
        if word == "ed" + suf:
            return "id" + suf
    ver_suffixes = ["mek", "meden", "meyen", "meyip", "meksizin", "meli", "melisin",
                    "dig", "digi", "digin", "digim", "digimiz",
                    "sin", "sinler", "di", "dim", "din", "dik", "diniz", "diler",
                    "iyor", "iyorum", "iyorsun", "iyoruz", "iyorsunuz", "iyorlar",
                    "ir", "irim", "irsin", "iriz", "irsiniz", "irler",
                    "ecek", "ecegim", "eceksin", "ecegiz", "ecekler",
                    "ilen", "ilmis", "ilmistir", "ilecek", "ilir"]
    for suf in ver_suffixes:
        if word == "ver" + suf:
            return "vir" + suf
    return word



# ---- Arapça kelime kuralı (sözlükte olmayan, şapkalı ya da ayın/hemze işaretli gövdeler) ----
_ARAP_ISARET = re.compile("[âîûāīū\u2018\u2019\u02bf']")
_UZUN_UNLU = {"â": "ا", "ā": "ا", "î": "ی", "ī": "ی", "û": "و", "ū": "و"}
_KISA_UNLU = set("aeıioöuü")


def _arapca_kok(word: str) -> str:
    """ma‘lûmiyet -> معلومیت, teâvün -> تعاون, mu‘cize -> معجزه: uzun ünlüler harfle, kısa ünlüler yazılmaz,
    ayın ع, hemze أ/ؤ/ئ, sondaki kısa ünlü ه/ی/و, ikiz ünsüz tek harf."""
    w, out, n = word, [], len(word)
    arka = bool(re.search("[aıouâûāū]", w))
    for i, ch in enumerate(w):
        once = w[i - 1] if i else ""
        sonra = w[i + 1] if i + 1 < n else ""
        son = i == n - 1
        if ch in "\u2018\u02bf":
            out.append("ع")
        elif ch in "\u2019'":
            out.append("ؤ" if once in "uü" else ("أ" if once in "ae" and sonra and sonra not in _KISA_UNLU else "ئ"))
        elif ch in _UZUN_UNLU:
            if i == 0:
                out.append("آ" if ch in "âā" else ("ای" if ch in "îī" else "او"))
            else:
                if once in _KISA_UNLU:
                    out.append("ع")          # iki ünlü yan yana: araya ayın (teâvün تعاون، müddeâ مدعا)
                out.append(_UZUN_UNLU[ch])
        elif ch in _KISA_UNLU:
            if i == 0:
                out.append("ا")
            elif son:
                out.append("ه" if ch in "ae" else ("ی" if ch in "ıi" else "و"))
        elif ch == once:
            continue                         # ikiz ünsüz (şedde) tek harf
        elif ch == "k":
            out.append("ق" if arka else "ك")
        elif ch in ("g", "ğ"):
            out.append("غ")
        elif ch == "h":
            out.append("ح")
        elif ch in CONSONANT_MAP_TURKISH and CONSONANT_MAP_TURKISH[ch]:
            out.append(CONSONANT_MAP_TURKISH[ch])
        elif ch.isalpha():
            out.append(ch)
    return "".join(out)


def transliterate_word(word: str, treat_last_as_final: bool = True, devam: str = "") -> str:
    """Tek bir Turkce kelimeyi (Latin harfli, kucuk harfli) Osmanlica
    yazimina cevirir. Once EXCEPTIONS sozlugune bakar."""
    word = turkish_lower(word).strip()
    word = _historicize_participle(word)
    word = _historicize_et_ver(word)
    if not word:
        return ""

    if word in EXCEPTIONS:
        return EXCEPTIONS[word]
    _fs = _farsca_son(word)
    if _fs:
        return _fs
    if _ARAP_ISARET.search(word):
        return _arapca_kok(word)

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
            if i == 0 and ch in ("a", "â"):
                letter = "آ"  # kelime başındaki a medli elifle: آلمق، آچیق، آنلام (Türkçe kelimelerin imlâsı)
            elif is_first:
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
            resolved = _resolve_k_g(ch, _kg_uyum(word + devam, i, harmony))  # devam: ayrılan ek (bug+ün)
            if ch == "ğ" and is_last:
                # kelime sonu yumusak g genelde onceki unluyu uzatir,
                # ayri harf olarak yazilmayabilir - yaklasik olarak yine yaziyoruz
                out.append(resolved)
            else:
                out.append(resolved)
        elif ch in ("s", "t", "d") and _kalin_unsuz(word, i, ch):
            out.append("ص" if ch == "s" else "ط")
        elif ch in CONSONANT_MAP_TURKISH and CONSONANT_MAP_TURKISH[ch]:
            out.append(CONSONANT_MAP_TURKISH[ch])
        elif ch.isalpha():
            out.append(ch)
        else:
            out.append(ch)

    return "".join(out)


_KALIN_SET = set("aıouâû")
_UNLU_SET = set("aeıioöuüâîû")
# Türkçede olmayan ses kalıpları: kelime başında iki ünsüz, "sy/ks/ps", sonda "-ns/-nk/-ks"
_YABANCI_RE = __import__("re").compile(r"^[^aeıioöuüâîû]{2}|sy|ks|ps|ns$|nk$")
# Türkçe olmayan kelime işaretleri: şapkalı harf, şedde (çift ünsüz), yan yana iki ünlü (saat, tatbik, sâbit)
# "sus-" fiili (sus, susmak, sustu): ardından ünsüz gelir; "susam" gibi isimler değil
_SUS_FIIL_RE = __import__("re").compile(r"^sus($|[^aeıioöuü])")
_TURKCE_DEGIL_RE = __import__("re").compile(r"[âîû]|([^aeıioöuü])\1|[aeıioöuü]{2}")


def _kalin_unsuz(word: str, i: int, ch: str) -> bool:
    """Türkçe kelimelerde kalın ünsüz yazımı: s -> ص (kalın ünlüyle birlikteyse; sor- صور, kısa قیصه),
    kelime başında t/d -> ط (ardından kalın ünlü geliyorsa; taş طاش, dur- طور)."""
    if ch in ("t", "d") and i != 0:
        return False
    if _YABANCI_RE.search(word):  # Avrupa kökenli kelimeler: sosyal, standart, dans, taksi, psikoloji
        return False
    if _TURKCE_DEGIL_RE.search(word):  # sözlükte olmayan Arapça/Farsça kelimeler
        return False
    if ch == "s" and word.startswith("sars") and i == 3:  # istisna: sars- -> صارص
        return True
    if ch == "s" and i != 0 and word[0] == "s" and not _SUS_FIIL_RE.match(word):
        return False  # aynı kelimedeki 2. kalın s -> س (sıska, susam, saksı); istisna: sus- fiili -> صوص
    if ch == "s" and i != 0:
        # Sadece kökteki s: ilk ünlünün hemen ardındaki (basmak, kısa, yosun). Daha ilerideki s çoğunlukla
        # ektir (-sa, -sınız, -sı) ve ekler kalın ünsüz almaz: olursanız, arasını -> س
        ilk = next((k for k, c in enumerate(word) if c in _UNLU_SET), None)
        if ilk is None or i != ilk + 1:
            return False
    sonraki = next((c for c in word[i + 1:] if c in _UNLU_SET), None)
    if sonraki is None:  # kelime sonundaki s: önceki ünlüye bak
        sonraki = next((c for c in reversed(word[:i]) if c in _UNLU_SET), None)
    return sonraki in _KALIN_SET


# --- Ek (suffix) farkinda transliterasyon ---
from .dictionary import SUFFIXES  # noqa: E402


SUFFIX_NO_VOWEL = {"ler": "لر", "lar": "لر"}


SUFFIX_NO_VOWEL = {"ler": "لر", "lar": "لر"}


# ---------------- Osmanlıca ek imlası ----------------
# Osmanlıcada ekler ses uyumundan bağımsız SABİT yazılır (-dır/-dir/-tır... -> در, -dan/-den -> دن,
# -da/-de -> ده, ilgi -ın/-in -> ڭ, belirtme -ı/-i -> ی, yönelme -a/-e -> ه). Ama sözlükteki ek
# ayırma bazen yanlıştır (has+tan+e, dur+um); o yüzden sabit yazım SADECE güvenilir ayırmada
# uygulanır, aksi hâlde eski (okunuşa göre) yazım sürer.
OTTOMAN_SUFFIX = {}
for _forms, _yazim in [
    ("dir dır dur dür tir tır tur tür", "در"),
    ("dirler dırlar durlar dürler tirler tırlar turlar türler", "درلر"),
    ("den dan ten tan", "دن"), ("nden ndan", "ندن"), ("de da te ta", "ده"),
    ("nin nın nun nün", "نڭ"), ("in ın un ün", "ڭ"),
    ("i ı u ü", "ی"), ("yi yı yu yü", "یی"), ("e a", "ه"), ("ye ya", "یه"),
    ("si sı su sü", "سی"), ("sin sın sun sün", "سڭ"),
    ("leri ları", "لری"), ("lerini larını", "لرینی"), ("lerine larına", "لرینه"),
    ("lerinin larının", "لرینڭ"), ("lerinden larından", "لریندن"),
    ("lerde larda", "لرده"), ("lerden lardan", "لردن"),
    ("la le", "له"), ("yla yle", "یله"),
    ("lık luk", "لق"), ("lik lük", "لك"), ("lı li", "لی"), ("lu lü", "لو"),
    ("lığı luğu", "لغی"), ("liği lüğü", "لگی"), ("lığını luğunu", "لغنی"), ("liğini lüğünü", "لگنی"),
    ("lığa luğa", "لغه"), ("liğe lüğe", "لگه"),
    ("cı ci cu cü", "جی"), ("çı çi çu çü", "جی"), ("sız siz suz süz", "سز"),
    ("sızlık suzluk", "سزلق"), ("sizlik süzlük", "سزلك"), ("sızlığı", "سزلغی"), ("sizliği", "سزلگی"),
    # imlâ turu 2: iyelik çokluk ekleri, -ki, n'li hâl ekleri (matbaa yazımı: قلبمز، قلبڭز، شكلندكی)
    ("imiz ımız umuz ümüz miz mız muz müz", "مز"), ("iniz ınız unuz ünüz niz nız nuz nüz", "ڭز"),
    ("im ım um üm", "م"),   # 1. tekil iyelik/ek-fiil: نفسم، نفسمه (Risale)
    ("ki", "كی"), ("deki daki teki taki", "دهكی"), ("ndeki ndaki", "ندهكی"),   # Risale: اصلندهكی
    ("tan ten", "دن"), ("ta te", "ده"),
    ("nde nda", "نده"), ("ne na", "نه"), ("ni nı nu nü", "نی"),
]:
    OTTOMAN_SUFFIX.update({f: _yazim for f in _forms.split()})

_SERT = set("çfhkpsşt")
_T_EKLER = set("tir tır tur tür tirler tırlar turlar türler ten tan te ta".split())
_ONLY_FINAL = set("in ın un ün sin sın sun sün".split())   # ortadaysa iyelik + kaynaştırma n'si
_GUVENLI_BILINMEYEN = set("dir dır dur dür dirler dırlar durlar dürler tir tır tur tür tirler tırlar "
                          "turlar türler nden ndan nin nın nun nün leri ları lerini larını lerine larına "
                          "lerinin larının lerinden larından lerde larda lerden lardan".split())

# Ek sırası: 1 çoğul, 2 iyelik, 3 hâl, 4 ek-fiil. (başlangıç, olası bitişler)
_SIRA = {}
for _forms, _bas, _bit in [
    ("ler lar", 1, {1}), ("leri ları", 1, {2}),
    ("lerini larını lerine larına lerinin larının lerinden larından lerde larda lerden lardan", 1, {3}),
    ("si sı su sü im ım um üm", 2, {2}), ("i ı u ü in ın un ün", 2, {2, 3}),
    ("e a ye ya yi yı yu yü de da te ta den dan ten tan nden ndan nin nın nun nün", 3, {3}),
    ("dir dır dur dür tir tır tur tür dirler dırlar durlar dürler tirler tırlar turlar türler sin sın sun sün",
     4, {4}),
    ("lık lik luk lük lı li lu lü", 0.5, {0.5}),
    ("lığı liği luğu lüğü", 0.5, {2}),
    ("lığını liğini luğunu lüğünü lığa liğe luğa lüğe", 0.5, {3}),
    ("la le yla yle", 3, {3}),
    ("cı ci cu cü çı çi çu çü sız siz suz süz sızlık sizlik suzluk süzlük", 0.5, {0.5}),
    ("sızlığı sizliği", 0.5, {2}),
    ("imiz ımız umuz ümüz miz mız muz müz iniz ınız unuz ünüz niz nız nuz nüz", 2, {2}),
    ("nde nda ne na ni nı nu nü", 3, {3}),
    ("ki", 3.5, {3.5}), ("deki daki teki taki ndeki ndaki", 3, {3.5}),
]:
    for _f in _forms.split():
        _SIRA[_f] = (_bas, _bit)


def ek_sirasi_gecerli(sufs) -> bool:
    son = 0
    for s in sufs:
        bas, bit = _SIRA.get(s, (None, None))
        if bas is None:
            return False
        # iyelik-hâl çift anlamlı ekler (i, ın): iyelikten sonra hâl eki sayılır (âyet+ler+imiz+i)
        uygun = sorted(b for b in bit if b > son and (b == bas or bas > son or (len(bit) > 1 and bas == son)))
        if not uygun:
            return False
        son = uygun[0]
    return True


def ek_guvenilir(root: str, sufs) -> bool:
    """Sözlükten gelen kök + ek ayırması sabit ek yazımına güvenecek kadar sağlam mı?"""
    if not sufs:
        return True
    if not ek_sirasi_gecerli(sufs):
        return False
    return len(root) >= 4 or (len(root) == 3 and all(len(s) >= 2 for s in sufs))


def _sabit_uygun(suf, last, known_root, prev) -> bool:
    if suf not in OTTOMAN_SUFFIX:
        return False
    if suf in _T_EKLER and (not prev or prev[-1] not in _SERT):
        return False
    if suf in _ONLY_FINAL and not last:
        return False
    if not known_root and suf not in _GUVENLI_BILINMEYEN:
        return False
    return True


def _ekleri_bol(tails):
    """Kesme işaretinden sonraki ek tanınmıyorsa iki bilinen eke bölmeyi dener (ındır -> ın + dır)."""
    out = []
    for t in (tails or []):
        if not t:
            continue
        if t in OTTOMAN_SUFFIX or t in SUFFIX_NO_VOWEL:
            out.append(t)
            continue
        bolum = _ek_bolumu(t, 3)
        out += bolum if bolum else [t]
    return out


def _ek_bolumu(t, n):
    """t'yi en çok n bilinen eke böler (lerdir -> ler + dir, sine -> si + ne); bulunamazsa None."""
    bilinen = lambda x: x in OTTOMAN_SUFFIX or x in SUFFIX_NO_VOWEL
    if bilinen(t):
        return [t]
    if n <= 1:
        return None
    for i in range(len(t) - 1, 0, -1):
        a = t[:i]
        if bilinen(a):
            kalan = _ek_bolumu(t[i:], n - 1)
            if kalan and ek_sirasi_gecerli([a] + kalan):
                return [a] + kalan
    return None


# İyelik (3. tekil) + n'li hâl eki matbaada yesiz yazılır: hükmünde حكمنده, arkasından آرقهسندن, sikkesini سكّهسنی
_IYELIK_HAL = {}
for _formlar, _yazim in [
    ("sında sinde sunda sünde", "سنده"), ("ında inde unda ünde", "نده"),
    ("sından sinden sundan sünden", "سندن"), ("ından inden undan ünden", "ندن"),
    ("sını sini sunu sünü", "سنی"), ("ını ini unu ünü", "نی"),
    ("sına sine suna süne", "سنه"), ("ına ine una üne", "نه"),
    ("sının sinin sunun sünün", "سنڭ"),   # -ının ise yeli kalır: برینڭ، فهملرینڭ (matbaa)
    ("sındaki sindeki sundaki sündeki", "سندهكی"), ("ındaki indeki undaki ündeki", "ندهكی"),
]:
    _IYELIK_HAL.update({f: _yazim for f in _formlar.split()})


def ekleri_yaz(root: str, sufs, tails, harmony: str, guvenilir: bool = True) -> str:
    """Sözlükten gelen ekleri (sufs) ve kesme işaretiyle ayrılmış ekleri (tails) yazar."""
    birlesik = "".join(list(sufs or []) + [t for t in (tails or []) if t])
    if birlesik in _IYELIK_HAL:
        return _IYELIK_HAL[birlesik]
    ekler = [(s, guvenilir) for s in (sufs or [])] + [(t, True) for t in _ekleri_bol(tails)]
    if [e for e, _ in ekler] in (["u"], ["ü"]) and root[-1:] not in "aeıioöuü":
        return "ی"   # iyelik/belirtme -u/-ü matbaada ی: یولی، كوزی (Risale)
    out, prev = "", root
    for i, (s, known) in enumerate(ekler):
        sonraki = ekler[i + 1][0] if i + 1 < len(ekler) else None
        son_gibi = sonraki is None or _SIRA.get(sonraki, (0,))[0] == 4
        out += _transliterate_suffix(s, harmony, last=son_gibi, known_root=known, prev=prev)
        prev += s
    return out


def _transliterate_suffix(suf: str, harmony: str, last: bool = True, known_root: bool = True,
                          prev: str = "") -> str:
    if suf in SUFFIX_NO_VOWEL:
        return SUFFIX_NO_VOWEL[suf]
    # prev (bağlam) verilmişse ve ayırma güvenilirse Osmanlıca sabit yazım; yoksa eski davranış
    if prev and _sabit_uygun(suf, last, known_root, prev):
        return OTTOMAN_SUFFIX[suf]
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


# ---------------- Fiil çekimi (Osmanlıca ek imlası) ----------------
# Sözlükte bulunmayan kelimelerde fiil ekleri tanınır; kök kendi ses uyumuyla yazılır,
# ek Osmanlıcadaki yerleşik yazımıyla eklenir (durup -> طوروب, gelecek -> گله‌جك).
_ZW = "\u200c"
_INCE = set("eiöü")
_UNLU = set("aeıioöuü")
_SERT_F = set("çfhkpsşt")


def _v(form):
    """Ekin kendi ünlüsüne göre kalın/ince: ك/گ (ince) ya da ق/غ (kalın)."""
    for ch in form:
        if ch in _UNLU:
            return ch in _INCE
    return True


def _fiil_ekleri():
    L = []  # (ek, yazım, şart)  şart: any | sert | yumusak | unlu | unsuz | r
    def add(forms, yazim_ince, yazim_kalin=None, sart="any"):
        for f in forms.split():
            L.append((f, yazim_ince if (yazim_kalin is None or _v(f)) else yazim_kalin, sart))
    # zarf-fiil -ıp/-ip
    add("ıp ip up üp", "وب", sart="unsuz")
    add("yıp yip yup yüp", "یوب", sart="unlu")
    # -arak/-erek
    # kalında elif, incede he (Risale matbaa nüshası: اولارق، ایده‌رك)
    add("erek arak", "ه" + _ZW + "رك", "ارق", sart="unsuz")   # kalında elif (اولارق); ederek ایدرك ayrıca
    add("yerek yarak", "یه" + _ZW + "رك", "یارق", sart="unlu")
    # gelecek zaman
    for y, sart in (("", "unsuz"), ("y", "unlu")):
        b = "یه" if y else "ه"
        k = "یا" if y else "ا"   # kalında elif: اولاجق، آڭلایاجق، بیراقاجغم (Risale matbaa nüshası); incede he: كوره‌جك
        add(f"{y}ecek {y}acak", b + _ZW + "جك", k + "جق", sart)
        add(f"{y}ecekler {y}acaklar", b + _ZW + "جكلر", k + "جقلر", sart)
        add(f"{y}ecektir {y}acaktır", b + _ZW + "جكدر", k + "جقدر", sart)
        add(f"{y}eceklerdir {y}acaklardır", b + _ZW + "جكلردر", k + "جقلردر", sart)
        add(f"{y}ecekti {y}acaktı", b + _ZW + "جكدی", k + "جقدی", sart)
        add(f"{y}eceksin {y}acaksın", b + _ZW + "جكسڭ", k + "جقسڭ", sart)
        add(f"{y}eceksiniz {y}acaksınız", b + _ZW + "جكسڭز", k + "جقسڭز", sart)
        add(f"{y}eceğim {y}acağım", b + _ZW + "جگم", k + "جغم", sart)
        add(f"{y}eceğiz {y}acağız", b + _ZW + "جگز", k + "جغز", sart)
    # öğrenilen geçmiş -mış/-miş
    m = "mış miş muş müş"
    add(m, "مش")
    add(" ".join(x + "lar" if not _v(x) else x + "ler" for x in m.split()), "مشلر")
    add(" ".join(x + t for x in m.split() for t in ("tır", "tir", "tur", "tür")), "مشدر")
    add(" ".join(x + t for x in m.split() for t in ("lardır", "lerdir")), "مشلردر")
    add(" ".join(x + t for x in m.split() for t in ("tı", "ti", "tu", "tü")), "مشدی")
    add(" ".join(x + t for x in m.split() for t in ("tık", "tik", "tuk", "tük")), "مشدك", "مشدق")
    add(" ".join(x + t for x in m.split() for t in ("tınız", "tiniz", "tunuz", "tünüz")), "مشدڭز")
    add(" ".join(x + t for x in m.split() for t in ("sınız", "siniz", "sunuz", "sünüz")), "مشسڭز")
    add(" ".join(x + t for x in m.split() for t in ("sın", "sin", "sun", "sün")), "مشسڭ")
    # şimdiki zaman -ıyor/-iyor (kökün ünlüsü düşmüş hâliyle: anl-ıyor, sor-uyor)
    for son, yaz in (("", "یور"), ("lar", "یورلر"), ("um", "یورم"), ("sun", "یورسڭ"), ("uz", "یورز"),
                     ("sunuz", "یورسڭز"), ("du", "یوردی"), ("dum", "یوردم"), ("duk", "یوردق"),
                     ("dunuz", "یوردڭز"), ("lardı", "یورلردی"), ("sa", "یورسه"), ("muş", "یورمش"),
                     ("sanız", "یورسه" + _ZW + "ڭز"), ("larsa", "یورلرسه")):
        add(" ".join(v + "yor" + son for v in "ıiuü"), yaz, sart="unsuz")
    # görülen geçmiş -dı/-di (t'li hâller sert ünsüzden sonra)
    for son, yaz, yaz_k in (("", "دی", None), ("lar", "دیلر", None), ("ler", "دیلر", None), ("m", "دم", None),
                            ("n", "دڭ", None), ("k", "دك", "دق"), ("nız", "دڭز", None), ("niz", "دڭز", None),
                            ("nuz", "دڭز", None), ("nüz", "دڭز", None)):
        for d, sart in (("d", "yumusak"), ("t", "sert")):
            forms = [d + v + son for v in "ıiuü"]
            if son in ("lar", "ler"):
                forms = [d + v + son for v in ("ı", "u")] if son == "lar" else [d + v + son for v in ("i", "ü")]
            if son in ("nız", "niz", "nuz", "nüz"):
                forms = [d + {"nız": "ı", "niz": "i", "nuz": "u", "nüz": "ü"}[son] + son]
            add(" ".join(forms), yaz, yaz_k, sart)
    # ortaç -dığı/-diği (Latin -duğu/-düğü önceden -dığı/-diği'ye çevriliyor)
    for son, yaz in (("", "ی"), ("nı", "نی"), ("ni", "نی"), ("na", "نه"), ("ne", "نه"), ("nda", "نده"),
                     ("nde", "نده"), ("ndan", "ندن"), ("nden", "ندن"), ("mız", "مز"), ("miz", "مز"),
                     ("nız", "ڭز"), ("niz", "ڭز"), ("m", "م"), ("n", "ڭ")):
        for d, sart in (("d", "yumusak"), ("t", "sert")):
            for kok, harf in (("ığı", "غ"), ("iği", "گ")):
                f = d + kok + son
                if son and ((harf == "غ") != (not _v(son) if any(c in _UNLU for c in son) else harf == "غ")):
                    continue
                add(f, "دی" + harf + yaz, sart=sart)
    for son, yi, yk in (("ları", "دكلری", "دقلری"), ("larını", "دكلرینی", "دقلرینی"),
                        ("larına", "دكلرینه", "دقلرینه"), ("larından", "دكلریندن", "دقلریندن"),
                        ("ça", "دكجه", "دقجه")):
        son_i = son.replace("a", "e").replace("ı", "i")
        for d, sart in (("d", "yumusak"), ("t", "sert")):
            add(f"{d}ık{son} {d}uk{son}", yk, sart=sart)
            add(f"{d}ik{son_i} {d}ük{son_i}", yi, sart=sart)
    # şart
    add("seydi saydı", "سه" + _ZW + "یدی")
    add("se sa", "سه", sart="r")
    add("seniz sanız", "سه" + _ZW + "ڭز", sart="r")
    add("seler salar", "سه" + _ZW + "لر", sart="r")
    # zarf-fiil -ınca/-ince
    add("ınca ince unca ünce", "نجه", sart="unsuz")
    add("yınca yince yunca yünce", "ینجه", sart="unlu")
    # mastar
    add("mek mak", "مك", "مق")
    add("mekte makta", "مكده", "مقده")
    add("mektedir maktadır", "مكده" + _ZW + "در", "مقده" + _ZW + "در")
    # ortaç -acağı/-eceği (anlaşılacağını -> آڭلاشیله‌جغنی)
    for y, sart in (("", "unsuz"), ("y", "unlu")):
        b = ("یه" if y else "ه") + _ZW + "ج"
        bk = ("یا" if y else "ا") + "ج"   # kalında elif (اولاجغنی)
        for son, yaz in (("", "ی"), ("nı", "نی"), ("na", "نه"), ("nda", "نده"), ("ndan", "ندن"),
                         ("mız", "مز"), ("nız", "ڭز"), ("m", "م")):
            son_i = son.replace("ı", "i").replace("a", "e")
            add(f"{y}acağı{son}", bk + "غ" + yaz, sart=sart)
            add(f"{y}eceği{son_i}", b + "گ" + yaz, sart=sart)
    # olumsuz emir (çoğul)
    add("meyin mayın", "میڭ")
    return sorted(L, key=lambda x: -len(x[0]))


_FIIL_EKLERI = _fiil_ekleri()
_IKINCI_TEKIL = set("dın din dun dün tın tin tun tün".split())


def _fiil_ayir(word):
    """(kök, ek_yazımı, kök_sonu_yazılsın_mı) ya da None."""
    for ek, yazim, sart in _FIIL_EKLERI:
        if not word.endswith(ek) or len(word) - len(ek) < 2:
            continue
        kok = word[: -len(ek)]
        if not any(c in _UNLU for c in kok):
            continue
        son = kok[-1]
        if sart == "unlu" and son not in _UNLU:
            continue
        if sart == "unsuz" and son in _UNLU:
            continue
        if sart == "sert" and son not in _SERT_F:
            continue
        if sart == "yumusak" and son in _SERT_F:
            continue
        if sart == "r" and son != "r":
            continue
        # "-dın/-din" (sen ...-dın) sadece olumsuzla: görmedin mi? (Haldun, Nureddin gibi isimler karışmasın)
        if ek in _IKINCI_TEKIL and not kok.endswith(("me", "ma")):
            continue
        if ek in ("tik", "tık") and kok.endswith("ek") and len(kok) >= 5:  # diyalektik, eklektik
            continue
        return kok, yazim, ek[0] == "y" and kok[-1] != "e" and not kok.endswith("ma")
    return None


def _tarihi_kok(kok: str) -> str:
    """Osmanlıca imlâda bazı fiil kökleri eski söylenişiyle yazılır: etmek ایتمك, vermek ویرمك, demek دیمك, yemek ییمك
    (ettiği -> ایتدیگی, edilmiştir -> ایدیلمشدر, verdiği -> ویردیگی, demiştir -> دیمشدر, dediğimiz -> دیدیگمز)."""
    if kok == "et" or kok in ("ed", "edil", "edin"):
        return "i" + kok[1:]
    if kok in ("ver", "veril"):
        return "vir" + kok[3:]
    if kok in ("de", "denil"):
        return "di" + kok[2:]
    if kok == "ye":
        return "yi"
    return kok



# ---- Kökü bilinmeyen kelimede yaygın son ekler ve -lık (Risale dışı kitaplar; Hayrat imlâsı) ----
_KURAL_SABIT_EK = {"sı": "سی", "si": "سی", "su": "سی", "sü": "سی",
                   "ın": "ڭ", "in": "ڭ", "un": "ڭ", "ün": "ڭ", "nın": "نڭ", "nin": "نڭ", "nun": "نڭ", "nün": "نڭ",
                   "ı": "ی", "i": "ی", "u": "ی", "ü": "ی"}
_FARSCA_SON = (("zâde", "زاده"), ("zade", "زاده"), ("hâne", "خانه"), ("nâme", "نامه"), ("istân", "ستان"))


def _farsca_son(word):
    for son, yazi in _FARSCA_SON:          # paşazâde پاشازاده: kök kendi yazımıyla + Farsça ek
        if word.endswith(son) and len(word) - len(son) >= 3:
            from . import dictionary as _D
            h = _D._get(word[: -len(son)])
            return (h[0] if h else transliterate_word(word[: -len(son)])) + yazi
    return None


def _ek_uyumlu(stem, suf):
    """Ekin ünlüsü kökün son ünlüsüyle uyumlu mu (Martin, Darwin gibi adlar ilgi eki sayılmasın)."""
    son = [c for c in stem if c in "aeıioöuüâîû"]
    eku = [c for c in suf if c in "ıiuü"]
    if not son or not eku:
        return False
    return (son[-1] in "aıouâû") == (eku[0] in "ıu")


def _sabit_son_ek(stem, suf):
    yazi = _KURAL_SABIT_EK.get(suf)
    if yazi is None or len(stem) < 3 or not _ek_uyumlu(stem, suf):
        return None
    sonu_unlu = stem[-1] in "aeıioöuüâîû"
    if suf in ("ın", "in", "un", "ün", "ı", "i", "u", "ü") and sonu_unlu:
        return None          # ünlüden sonra -nın/-sı gelir; bu biçim başka bir şeydir
    if suf in ("nın", "nin", "nun", "nün", "sı", "si", "su", "sü") and not sonu_unlu and suf[0] != "s":
        return None
    return yazi


def _govde_yaz(stem, son_unlu, devam):
    """-lık/-lik/-luk/-lük (ve -lığ/-liğ) ünlüsüz: özel+lik اوزللك، gerçek+lik كرچكلك."""
    m = re.search(r"l([ıiuü])([kğ])$", stem)
    if m and len(stem) > 5:
        arka = m.group(1) in "ıu"
        ek = ("لق" if arka else "لك") if m.group(2) == "k" else ("لغ" if arka else "لك")
        return transliterate_word(stem[:-3], treat_last_as_final=False, devam=stem[-3:] + devam) + ek
    return transliterate_word(stem, treat_last_as_final=son_unlu, devam=devam)


def transliterate_word_with_suffix(word: str) -> str:
    """Kelimeyi mumkunse kok+ek olarak ayirir. Kok normal (pozisyon
    farkinda) kurallarla, ek ise kendi kurallariyla cevrilir."""
    word = turkish_lower(word).strip()
    word = _historicize_participle(word)
    word = _historicize_et_ver(word)
    if not word:
        return ""

    if word in EXCEPTIONS:
        return EXCEPTIONS[word]
    _fs = _farsca_son(word)
    if _fs:
        return _fs

    _f = _fiil_ayir(word)
    if _f and len(_f[0]) >= 4 and _f[0][-2:] in ("me", "ma") and _f[0][-3] not in "aeıioöuü":
        # olumsuzluk eki -ma/-me ünlüsüyle yazılır: etmemek ایتمه‌مك, vermeyip ویرمه‌یوب, olmamakla اولمامقله
        taban = _f[0][:-2]
        govde = transliterate_word(_tarihi_kok(taban), treat_last_as_final=False, devam=_f[0][-2:])
        if _f[1].startswith("د"):
            return govde + "م" + _f[1]        # geçmiş zaman: etmedi ایتمدی، kalmadı قالمدی (Risale)
        return govde + ("مه" if _f[0].endswith("me") else "ما") + _f[1]
    if re.match(r"^(et[mst]|ed[eiı])", word) and len(word) >= 4 \
            and (word.startswith("edebil") or not word.startswith(("edeb", "edep", "edib", "edip", "etki", "etra"))) \
            and (not _f or _f[0] not in ("et", "ed", "edil", "edin")):
        if word.startswith(("edeme", "edebil")):
            return "ایده\u200c" + transliterate_word_with_suffix("y" + word[3:])[1:]   # edemez -> ایده‌مز, edebilir -> ایده‌بیلیر
        return transliterate_word_with_suffix("i" + word[1:])   # etmez -> ایتمز, etse -> ایتسه
    fiil = _fiil_ayir(word)
    if fiil:
        kok, yazim, kok_sonu = fiil
        devam = word[len(kok):]
        return transliterate_word(_tarihi_kok(kok), treat_last_as_final=kok_sonu, devam=devam) + yazim

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
                result += {"lık": "لق", "luk": "لق", "lik": "لك", "lük": "لك"}.get(suf) or _transliterate_suffix(suf, harmony)
            return result

    # EXCEPTIONS'a ulasilamadi - guvenli, eski (tek ek) davranisa don
    best_suf = None
    for suf in SUFFIXES:
        if word.endswith(suf) and len(word) - len(suf) >= 2:
            if best_suf is None or len(suf) > len(best_suf):
                best_suf = suf

    if best_suf:
        stem = word[: -len(best_suf)]
        # a/e ile biten isim ek alınca sondaki ه korunur: duruşma+nın طوروشمهنڭ، ülke+sinde اولكهسنده (Hayrat)
        son_unlu = stem[-1:] in ("a", "e") and len(stem) >= 3
        if len(stem) >= 4 and stem[-2:] in ("ma", "me") and stem[-3] not in "aeıioöuü" and best_suf[:1] == "s":
            stem, son_unlu = stem[:-1], False     # -mAsI: kurulması قورولمسی، getirilmesi كتیریلمسی (Hayrat)
        sabit = _sabit_son_ek(stem, best_suf)
        if sabit is not None:
            return _govde_yaz(stem, son_unlu, best_suf) + sabit
        return _govde_yaz(stem, son_unlu, best_suf) + _transliterate_suffix(
            best_suf, harmony, known_root=False, prev=stem)

    return _govde_yaz(word, True, "")


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



# ---- Hayrat (Risale-i Nur orijinal nüshası): iyelik + (n) + hâl eki dizileri ----
# "in" ilgi eki sanılıp ڭ yazılmasın: vahdetine وحدتنه، cevabının جوابنڭ، Gazetesi'nin غزتهسنڭ، cinâyetlerini جنایتلرینی
def _iyelik_hayrat():
    d = {}
    def ekle(bicimler, yazim):
        for b in bicimler.split():
            d[b] = yazim
    ekle("ine ına une üne", "نه")
    ekle("inde ında unda ünde", "نده")
    ekle("inden ından undan ünden", "ندن")
    ekle("indeki ındaki undaki ündeki", "نده\u200cكی")
    ekle("ini ını unu ünü", "نی")
    ekle("inin ının unun ünün", "نڭ")
    ekle("sine sına suna süne", "سنه")
    ekle("sinde sında sunda sünde", "سنده")
    ekle("sinden sından sundan sünden", "سندن")
    ekle("sini sını sunu sünü", "سنی")
    ekle("sinin sının sunun sünün", "سنڭ")
    ekle("lerine larına", "لرینه")
    ekle("lerini larını", "لرینی")
    ekle("lerinin larının", "لرینڭ")
    ekle("lerinde larında", "لرنده")
    ekle("lerinden larından", "لرندن")
    ekle("leriniz larınız", "لریڭز")
    ekle("lerinizi larınızı", "لریڭزی")
    ekle("lerinizin larınızın", "لریڭزڭ")
    ekle("iniz ınız unuz ünüz", "ڭز")
    ekle("inizi ınızı unuzu ünüzü", "ڭزی")
    ekle("inizin ınızın unuzun ünüzün", "ڭزڭ")
    return d


IYELIK_HAL_HAYRAT = _iyelik_hayrat()
_IYELIK_HAL.update(IYELIK_HAL_HAYRAT)
