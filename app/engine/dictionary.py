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
# Türkçe kelime düzeltmeleri: sözlükten sonra okunur (sözlük kaydı Türkçe kelimeyle çakışınca Türkçe kazanır)
DUZELTME_FILE = Path(__file__).parent.parent / "data" / "duzeltmeler.tsv"

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
    "nin", "nın", "nun", "nün",
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


# Sadece sözlük aramasında kullanılan ek ekler: -la/-le (ile), yapım ekleri -lık/-lı ve birleşimleri
EXTRA_LOOKUP_SUFFIXES = ("la le yla yle lık lik luk lük lı li lu lü lığı liği luğu lüğü "
                         "lığını liğini luğunu lüğünü lığa liğe luğa lüğe cı ci cu cü çı çi çu çü sız siz suz süz sızlık sizlik suzluk süzlük sızlığı sizliği").split()
LOOKUP_SUFFIXES = SUFFIXES + [x for x in EXTRA_LOOKUP_SUFFIXES if x not in SUFFIXES]

def _load_extra_from_tsv() -> dict:
    extra = {}
    for dosya in (DATA_FILE, DUZELTME_FILE):
        if not dosya.exists():
            continue
        with open(dosya, "r", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter="\t")
            for row in reader:
                if len(row) >= 3 and not row[0].startswith("#") and row[1].strip():
                    latin, osmanli, origin = row[0].strip(), row[1].strip(), row[2].strip()
                    if osmanli[:1] in "إأ":
                        osmanli = "ا" + osmanli[1:]   # Osmanlıcada kelime başında hemze yazılmaz (إنعام -> انعام)
                    extra[turkish_lower(latin)] = (osmanli, origin)
    return extra


def load_dictionary() -> dict:
    combined = dict(SEED_DICTIONARY)
    combined.update(_load_extra_from_tsv())
    return combined


DICTIONARY = load_dictionary()

# Osmanlıca yazımda tutarlılık: Arapça ye (ي) yerine Osmanlıca/Farsça ye (ی), Farsça kef (ک) yerine kef (ك)
DICTIONARY = {k: (v[0].replace("\u064a", "\u06cc").replace("\u06a9", "\u0643"), v[1]) for k, v in DICTIONARY.items()}

# ---------------- Şedde (ّ) ----------------
# Arapça/Farsça kökenli kelimelerde ikizleşen harfin üzerine şedde konur: muallim -> معلّم, cennet -> جنّت.
# İkizleşme Latin yazımdaki çift harften anlaşılır. Harfin karşılığı belirsizse şedde konmaz.
# Türkçe kelimelerde şedde kullanılmaz. Kapatmak için: OSM_SEDDE=0
import os as _os
_SEDDE = "\u0651"
_HARF_KARSILIK = {"b": "ب", "c": "ج", "ç": "چ", "d": "دض", "f": "ف", "g": "غگ", "h": "حهخ", "j": "ژ",
                  "k": "كق", "l": "ل", "m": "م", "n": "ن", "p": "پ", "r": "ر", "s": "سصث", "ş": "ش",
                  "t": "تط", "v": "و", "y": "ی", "z": "زذضظ"}
_SEDDE_KOKEN = {"ar", "ar-fa", "fa-ar", "sozlukler"}
_TURKCE_CIFT = {"elli", "anne", "yassı", "belli", "bellik", "bellek", "belli", "ille", "dokkuz"}


def _sedde_koy(latin: str, osm: str) -> str:
    if _SEDDE in osm or " " in osm.strip():  # iki kelimelik kayıtlar (emretti -> امر ایتدی): Türkçe kısma şedde konmaz
        return osm
    for i in range(len(latin) - 1):
        ch = latin[i]
        if ch != latin[i + 1] or ch not in _HARF_KARSILIK or (i > 0 and latin[i - 1] == ch):
            continue
        adaylar = _HARF_KARSILIK[ch]
        # Latin'de bu ünsüzün kaç "grubu" var (çift harf tek grup sayılır) ve bizimki kaçıncı?
        gruplar, sira, j = 0, None, 0
        while j < len(latin):
            if latin[j] == ch:
                if j == i:
                    sira = gruplar
                gruplar += 1
                while j + 1 < len(latin) and latin[j + 1] == ch:
                    j += 1
            j += 1
        konumlar = [k for k, c in enumerate(osm) if c in adaylar]
        if sira is None or len(konumlar) != gruplar:
            continue  # belirsiz: şedde koyma
        k = konumlar[sira]
        osm = osm[:k + 1] + _SEDDE + osm[k + 1:]
    return osm


if _os.environ.get("OSM_SEDDE", "1") != "0":
    DICTIONARY = {k: ((_sedde_koy(k, v[0]), v[1]) if (v[1] in _SEDDE_KOKEN and k not in _TURKCE_CIFT
                                                      and any(k[i] == k[i + 1] and k[i] in _HARF_KARSILIK
                                                              for i in range(len(k) - 1))) else v)
                  for k, v in DICTIONARY.items()}


def _flat(s: str) -> str:
    """Şapkaları kaldırır: âhiret -> ahiret, îman -> iman, ûlâ -> ula."""
    return s.replace("â", "a").replace("î", "i").replace("û", "u")


# Şapkası farklı olunca anlamı değişen, günlük Türkçede şapkasız yazılan kelimeler:
# bunlarda şapkasız eşleştirme YAPILMAZ (kar≠kâr, hala≠hâlâ ...).
_FLAT_EXCLUDE = {"hala", "kar", "ama", "yar", "hal", "alem", "adet", "asik", "aşık", "dahi",
                 "rahim", "alim", "katil", "hakim", "sura", "şura", "yarim", "yaran"}

# Sözlükte şapkalı kayıtlı kelimeler için şapkasız ek anahtarlar (âhiret -> ahiret).
FLAT = {}
for _k, _v in DICTIONARY.items():
    _fk = _flat(_k)
    if _fk != _k and len(_fk) >= 4 and _fk not in DICTIONARY and _fk not in _FLAT_EXCLUDE:
        FLAT.setdefault(_fk, _v)


def _get(key: str):
    """Tam eşleşme; yoksa şapkasız eşleşme (ahiret -> âhiret, ya da tersi)."""
    return DICTIONARY.get(key) or FLAT.get(key) or DICTIONARY.get(_flat(key))


_SERTLES = {"ğ": "k", "b": "p", "c": "ç"}
_YUMUSAMA_KOKEN = {"ar", "fa", "ar-fa", "fa-ar"}


def _get_soft(stem: str):
    """Kök sözlükte yoksa, ek önünde yumuşamış son ünsüzü geri sertleştirip dener: mantığ -> mantık.
    Sadece Arapça/Farsça kökenli kelimelerde: Osmanlıcada onlarda yumuşama yazıya yansımaz (منطقی),
    Türkçe kelimelerde ise yansır (çocuğu -> چوجوغی), o yüzden Türkçe kelimelere uygulanmaz."""
    hit = _get(stem)
    if hit or len(stem) < 3 or stem[-1] not in _SERTLES:
        return hit
    alt = _get(stem[:-1] + _SERTLES[stem[-1]])
    return alt if alt and alt[1] in _YUMUSAMA_KOKEN else None


_T_EKLER_SES = set("tir tır tur tür ten tan te ta tirler tırlar turlar türler".split())


def _ek_ses_uygun(stem: str, suf: str) -> bool:
    """t'li ekler sadece sert ünsüzden (ç f h k p s ş t) sonra gelir."""
    return not (suf in _T_EKLER_SES and stem[-1:] not in "çfhkpsşt")


def lookup_exact(word: str):
    """Ek ayırmadan, sadece kelimenin kendisini arar."""
    return _get(turkish_lower(word).strip())


def _lookup_with_suffix_stripping(word: str):
    """Dogrudan bulunamayan kelime icin, yaygin Turkce eklerini sondan
    tek tek deneyerek kok halini sozlukte arar. (kok_hit, ek) dondurur -
    ek bilgisi kaybolmasin diye ayri dondurulur, cagiran taraf ekin
    Osmanlica karsiligini kendisi ekler."""
    for suf in LOOKUP_SUFFIXES:
        if word.endswith(suf):
            stem = word[: -len(suf)]
            if len(stem) < 2:
                continue
            hit = _get(stem)
            if hit:
                return hit, suf
    return None, None


def lookup(word: str):
    """Verilen Latin harfli Turkce kelimeyi sozlukte arar. Once tam
    eslesmeyi dener, bulamazsa ek ayirma ile kok halini dener.
    UYARI: ek bilgisini atar - suffix'i de istiyorsan lookup_with_suffix
    kullan."""
    w = turkish_lower(word).strip()
    hit = _get(w)
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
    hit = _get(w)
    if hit:
        return hit, []

    peeled = []
    current = w
    for _ in range(3):  # en fazla 3 ek ust uste (guvenlik siniri)
        hit = _get(current)
        if hit:
            return hit, list(reversed(peeled))
        # Tek bir ek ayrılınca sözlükte bulunan kökler varsa, kökü EN UZUN olanı seç
        # (ahirete -> ahiret + e; "ahire + te" değil).
        direct = [(suf, _get_soft(current[: -len(suf)])) for suf in LOOKUP_SUFFIXES
                  if current.endswith(suf) and len(current) - len(suf) >= 2
                  and _ek_ses_uygun(current[: -len(suf)], suf)]
        direct = [(suf, h) for suf, h in direct if h]
        if direct:
            suf, h = min(direct, key=lambda x: len(x[0]))
            return h, list(reversed(peeled + [suf]))
        best_suf = None
        for suf in LOOKUP_SUFFIXES:
            if current.endswith(suf) and len(current) - len(suf) >= 2 and _ek_ses_uygun(current[: -len(suf)], suf):
                if best_suf is None or len(suf) > len(best_suf):
                    best_suf = suf
        if not best_suf:
            break
        peeled.append(best_suf)
        current = current[: -len(best_suf)]

    hit = _get(current)
    if hit:
        return hit, list(reversed(peeled))
    return _derin_kok(w)


# İsim ekleri (iyelik, çoğul, hâl, ilgi, -ki): üst üste bindiklerinde kökü bulmak için (âyetlerimizi -> âyet + ler+imiz+i)
_ISIM_EKLERI = {e for e in LOOKUP_SUFFIXES if not e.startswith(("c", "ç"))} | {
    "imiz", "ımız", "umuz", "ümüz", "iniz", "ınız", "unuz", "ünüz", "miz", "mız", "muz", "müz", "niz", "nız", "nuz",
    "nüz", "ki", "nde", "nda", "ne", "na", "ni", "nı", "nu", "nü", "deki", "daki", "teki", "taki", "ndeki", "ndaki"}
_DERIN_KOKEN = {"ar", "fa", "ar-fa", "fa-ar"}


def _derin_kok(w: str):
    """Greedy ayırma bulamazsa: en uzun Arapça/Farsça sözlük kökünü, kalanı en çok beş isim ekine (iyelik, çoğul, hâl,
    -ki) bölünebilecek şekilde arar (âyetlerimizi -> âyet + leri+miz+i). Üç ve daha fazla ekte kök en az 4 harf."""
    from . import rules  # döngüsel içe aktarma olmasın diye burada

    def bol(x, n):
        """x'in bütün geçerli ek bölümleri (ek sırası kurallara uyan)."""
        if not x:
            yield []
            return
        if n == 0:
            return
        for i in range(min(len(x), 5), 0, -1):
            e = x[:i]
            if e in _ISIM_EKLERI:
                for kalan in bol(x[i:], n - 1):
                    yield [e] + kalan

    if rules._fiil_ayir(w):          # Türkçe fiil çekimi (yaratan, saydınız, dediniz): kural motoru yazar
        return None, []
    for L in range(len(w) - 1, 2, -1):
        kok = w[:L]
        hit = _get_soft(kok)
        if not hit or hit[1] not in _DERIN_KOKEN:   # yalnız Arapça/Farsça kökler (Türkçe kelimeler kural motorunda)
            continue
        ekler = next((e for e in bol(w[L:], 5) if rules.ek_sirasi_gecerli(e)), None)
        if ekler is None or not _ek_ses_uygun(kok, ekler[0]):
            continue
        if kok[-1] in "aeıioöuüâîû" and ekler[0][0] in "tç":   # ünlüden sonra sert ek olmaz (yara+tır değil)
            continue
        if len(ekler) >= 3 and len(kok) < 4:
            continue
        if len(ekler) <= 2 and len(kok) < 3:
            continue
        return hit, ekler
    return None, []
