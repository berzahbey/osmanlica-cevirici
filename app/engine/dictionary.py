# -*- coding: utf-8 -*-
"""
Osmanlica kelime sozlugu.

NOT: Kanar sozlugunden (referans/kontrol amacli) cikarilan ~10.000 kelime
ile buyutulmustur. Ayrica ekli kelimeler (orn. "rabbi" = "rab" + "-i") icin
basit bir ek ayirma (suffix stripping) katmani eklenmistir.

TSV format: latin_kelime<TAB>osmanlica_yazim<TAB>koken(ar/fa/tr/other)
"""
import csv
from pathlib import Path
from .alphabet import turkish_lower

DATA_FILE = Path(__file__).parent.parent / "data" / "ottoman_dict.tsv"

SEED_DICTIONARY = {
    "kitap": ("كتاب", "ar"), "kalem": ("قلم", "ar"), "insan": ("انسان", "ar"),
    "kalp": ("قلب", "ar"), "ilim": ("علم", "ar"), "dünya": ("دنيا", "ar"),
    "hayat": ("حيات", "ar"), "ruh": ("روح", "ar"), "nur": ("نور", "ar"),
    "aşk": ("عشق", "ar"), "zaman": ("زمان", "fa"), "mektup": ("مكتوب", "ar"),
    "kelam": ("كلام", "ar"), "kelime": ("كلمه", "ar"), "devlet": ("دولت", "ar"),
    "millet": ("ملت", "ar"), "hukuk": ("حقوق", "ar"), "adalet": ("عدالت", "ar"),
    "cumhuriyet": ("جمهوريت", "ar"), "vatan": ("وطن", "ar"), "hürriyet": ("حريت", "ar"),
    "medeniyet": ("مدنيت", "ar"), "tarih": ("تاريخ", "ar"), "mektep": ("مكتب", "ar"),
    "muallim": ("معلم", "ar"), "kütüphane": ("كتابخانه", "ar-fa"), "sabah": ("صباح", "ar"),
    "akşam": ("اقشام", "tr"), "selam": ("سلام", "ar"), "merhaba": ("مرحبا", "ar"),
    "dost": ("دوست", "fa"), "düşman": ("دشمن", "fa"), "padişah": ("پادشاه", "fa"),
    "şehir": ("شهر", "fa"), "hane": ("خانه", "fa"), "name": ("نامه", "fa"),
    "gül": ("گل", "fa"), "bahar": ("بهار", "fa"), "yıldız": ("ییلدز", "tr"),
    "güneş": ("گونش", "tr"), "ay": ("آی", "tr"), "su": ("صو", "tr"),
    "ateş": ("آتش", "fa"), "toprak": ("طوپراق", "tr"), "hava": ("هوا", "ar"),
    "âlem": ("عالم", "ar"), "kâinat": ("كائنات", "ar"), "hakikat": ("حقيقت", "ar"),
    "hikaye": ("حكايه", "ar"), "kıssa": ("قصه", "ar"), "rüya": ("رويا", "ar"),
    "sevgi": ("سوگی", "tr"), "sevgili": ("سوگیلی", "tr"), "gönül": ("گونل", "tr"),
    "can": ("جان", "fa"), "cihan": ("جهان", "fa"), "yar": ("یار", "fa"),
    "derya": ("دریا", "fa"), "deniz": ("دكز", "tr"), "dağ": ("طاغ", "tr"),
    "taş": ("طاش", "tr"), "ağaç": ("آغاج", "tr"), "çiçek": ("چیچك", "tr"),
    "kuş": ("قوش", "tr"), "ev": ("اى", "tr"), "kapı": ("قاپو", "tr"),
    "yol": ("یول", "tr"), "gece": ("گیجه", "tr"), "gündüz": ("گوندوز", "tr"),
    "sene": ("سنه", "ar"), "yıl": ("ییل", "tr"), "ay(takvim)": ("ماه", "fa"),
    "kadın": ("قادین", "tr"), "erkek": ("ایركك", "tr"), "çocuk": ("چوجق", "tr"),
    "anne": ("آنه", "tr"), "baba": ("بابا", "fa"), "kardeş": ("قرنداش", "tr"),
    "arkadaş": ("آرقاداش", "tr"), "hoca": ("خواجه", "fa"), "efendi": ("افندی", "tr"),
    "bey": ("بك", "tr"), "paşa": ("پاشا", "tr"), "sultan": ("سلطان", "ar"),
    "şeyh": ("شیخ", "ar"), "derviş": ("درویش", "fa"), "âşık": ("عاشق", "ar"),
    "maşuk": ("معشوق", "ar"), "hasret": ("حسرت", "ar"), "hüzün": ("حزن", "ar"),
    "sevinç": ("سوینج", "tr"), "keder": ("كدر", "ar"), "gam": ("غم", "fa"),
    "elem": ("الم", "ar"), "vuslat": ("وصال", "ar"), "firkat": ("فرقت", "ar"),
    "beka": ("بقا", "ar"), "fena": ("فنا", "ar"), "ezel": ("ازل", "ar"),
    "ebed": ("ابد", "ar"), "kader": ("قدر", "ar"), "nasip": ("نصیب", "ar"),
    "rızık": ("رزق", "ar"), "şükür": ("شكر", "ar"), "sabır": ("صبر", "ar"),
}

# Sondan denenecek ekler, UZUNDAN KISAYA siralanmis olmali
SUFFIXES = [
    "ler", "lar",
    "lerinden", "larından", "lerinin", "larının", "lerine", "larına",
    "lerini", "larını", "lerde", "larda", "lerden", "lardan",
    "leri", "ları", "nden", "ndan",
    "nin", "nın", "nun", "nün", "min", "mın", "mun", "mün",
    "sin", "sın", "sun", "sün",
    "dirler", "dırlar", "durlar", "dürler",
    "tirler", "tırlar", "turlar", "türler",
    "dir", "dır", "dur", "dür", "tir", "tır", "tur", "tür",
    "den", "dan", "ten", "tan", "de", "da", "te", "ta",
    "ye", "ya", "yi", "yı", "yu", "yü",
    "si", "sı", "su", "sü",
    "im", "ım", "um", "üm",
    "in", "ın", "un", "ün",
    "i", "ı", "u", "ü", "e", "a",
]


def _load_extra_from_tsv() -> dict:
    extra = {}
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter="\t")
            for row in reader:
                if len(row) >= 3 and not row[0].startswith("#"):
                    latin, osmanli, origin = row[0].strip(), row[1].strip(), row[2].strip()
                    extra[turkish_lower(latin)] = (osmanli, origin)
    return extra


def load_dictionary() -> dict:
    combined = dict(SEED_DICTIONARY)
    combined.update(_load_extra_from_tsv())
    return combined


DICTIONARY = load_dictionary()


def _lookup_with_suffix_stripping(word: str):
    """Dogrudan bulunamayan kelime icin, yaygin Turkce eklerini sondan
    tek tek deneyerek kok halini sozlukte arar. (kok_hit, ek) dondurur -
    ek bilgisi kaybolmasin diye ayri dondurulur, cagiran taraf ekin
    Osmanlica karsiligini kendisi ekler."""
    for suf in SUFFIXES:
        if word.endswith(suf):
            stem = word[: -len(suf)]
            if len(stem) < 2:
                continue
            hit = DICTIONARY.get(stem)
            if hit:
                return hit, suf
    return None, None


def lookup(word: str):
    """Verilen Latin harfli Turkce kelimeyi sozlukte arar. Once tam
    eslesmeyi dener, bulamazsa ek ayirma ile kok halini dener.
    UYARI: ek bilgisini atar - suffix'i de istiyorsan lookup_with_suffix
    kullan."""
    w = turkish_lower(word).strip()
    hit = DICTIONARY.get(w)
    if hit:
        return hit
    hit, _ = _lookup_with_suffix_stripping(w)
    return hit


def lookup_with_suffix(word: str):
    """(hit, ekler_listesi) dondurur. hit tam eslesme ise ekler_listesi
    bos listedir. Birden fazla ek ust uste binmisse (orn. yildiz+lar+a)
    EKLERI TEK TEK, en uzun eslesenden baslayarak ardisik soyar - boylece
    'yildizlara' -> 'yildiz' + ['lar','a'] gibi coklu ek de yakalanir."""
    w = turkish_lower(word).strip()
    hit = DICTIONARY.get(w)
    if hit:
        return hit, []

    peeled = []
    current = w
    for _ in range(3):  # en fazla 3 ek ust uste (guvenlik siniri)
        hit = DICTIONARY.get(current)
        if hit:
            return hit, list(reversed(peeled))
        best_suf = None
        for suf in SUFFIXES:
            if current.endswith(suf) and len(current) - len(suf) >= 2:
                if best_suf is None or len(suf) > len(best_suf):
                    best_suf = suf
        if not best_suf:
            break
        peeled.append(best_suf)
        current = current[: -len(best_suf)]

    hit = DICTIONARY.get(current)
    if hit:
        return hit, list(reversed(peeled))
    return None, []
