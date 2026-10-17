"""Tur L: Hayrat'ta az gecen (1 kez) ya da sozluge girmemis kelimelerden app/data/hayrat_tek.tsv uretir.
Kullanim (osmanlica deposunun kokunde, imajda):  OSM_HAYRAT_TEK=0 python tools/hayrat_tek_uret.py <kelime_ciftleri.tsv> [cikti]
Kural: anahtar hicbir sozlukte yoksa (ottoman_dict, duzeltmeler, hayrat, hayrat_az) ve Hayrat'ta tek yazimla
geciyorsa (en cok gecen yazim %70 ve ustu) ve ceviricinin bugunku yazimi Hayrat'tan farkliysa eklenir.
Alinmaz: (1) fark yalniz kef-i nuni / nun ise (senin/onun eki: kendini كندیڭی ~ كندینی), (2) es sesli ve baglam
listelerindeki kelimeler, (3) ek parcalari ve tek harf, (4) Latin'i rakam ya da Arap harfi iceren kayitlar,
(5) Hayrat'in olasi dizgi hatalari ve azinlik yazimlari (tools/hayrat_tek_supheli.tsv'ye yazilir, Zahir'in denetimi icin):
harf uyumu yok (Latin unsuzleri Osmanlica unsuzlerle uyusmuyor), kokun Hayrat'ta sik yazimiyla ya da ceviricinin kok yazimiyla
celisiyor (kitapta ayni kok iki turlu yazilmasin), Osmanlicada ayni kelime tekrari; ayrica -lar ile biten cogul/fiil belirsizligi.
Bu kayitlar sozlukte yalniz kelimenin tamami eslesince kullanilir (dictionary.HAYRAT_TEK), kok olarak kullanilmaz."""
import sys, os, re, collections, unicodedata
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app"))
os.environ["OSM_HAYRAT_TEK"] = "0"
import logging
logging.disable(logging.CRITICAL)
from engine import dictionary as D
from engine.transliterator import transliterate_text as tt

GIRDI = sys.argv[1]
CIKTI = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app", "data", "hayrat_tek.tsv")
VERI = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app", "data")
HAREKE = re.compile("[ً-ِْٕٓ-ٰٟۖ-ۭـ‍‎‏ؐ-ؚ؈]")


def osm(o):
    o = unicodedata.normalize("NFC", o)
    o = o.replace("ۀ", "هٔ").replace("ي", "ی").replace("ى", "ی")
    o = re.sub("ە(?=[ء-ۿ])", "ه‌", o).replace("ە", "ه")
    o = o.replace("ک", "ك").replace("گ", "ك")
    o = re.sub(r"[،؛؟.,;:!?«»\"()\[\]]", "", HAREKE.sub("", o))
    return re.sub(r"\s+", " ", o).strip()


def kiyas_bosluklu(o):
    o = osm(o).replace("\u0651", "").replace("\u200c", "").replace("\u0654", "")
    return o.replace("\u0623", "\u0627").replace("\u0625", "\u0627")


def kiyas(o):
    o = osm(o).replace("ّ", "").replace("‌", "").replace("ٔ", "").replace(" ", "")
    return o.replace("أ", "ا").replace("إ", "ا")


def kucuk(w):
    w = w.replace("I", "ı").replace("İ", "i").lower()
    for c in "’‘`ʼʻ":
        w = w.replace(c, "'")
    return w


# ---- Hayrat'in kendi dizgi hatalarini ayiklamak (Tur L, Zahir'in istegi) ----
# (a) Harf uyumu: Osmanlicanin unsuz harfleri (unlu harfleri ا و ی ه، ayin/hemze ve harf-i tarifin lam'i haric), Latin'in
# unsuzlarindan sirayla uretilebilmeli (z: ز ذ ض ظ، s: س ص ث، t/d: ت ط د ض، k/g: ك ق غ گ ...). ğ ve h istege bagli; y, v sayilmaz.
_L = {"b": "بپ", "p": "پب", "c": "جچ", "\u00e7": "چج", "d": "دطضت", "t": "تطدث", "f": "ف", "g": "كگغق", "k": "كقغگ",
      "l": "ل", "m": "م", "n": "نڭ", "r": "ر", "s": "سصث", "\u015f": "ش", "z": "زذضظ", "j": "ژج"}
_O_UNSUZ = set("".join(_L.values())) | set("حخ")
def _iskelet_o(o):
    out = []
    for parca in kiyas_bosluklu(o).split(" "):
        if parca.startswith("\u0627\u0644") and len(parca) > 3:
            parca = parca[2:]
        for c in parca:
            if c in _O_UNSUZ:
                out.append(c)
    return "".join(out)
def _desen_l(l):
    out, onceki = [], None
    tenvin = bool(re.search("[ea]n$", l)) and len(l) > 4
    for i, c in enumerate(l):
        if tenvin and i == len(l) - 1:
            out.append("[نڭ]?")
            break
        if c == onceki:
            continue
        onceki = c
        if c in _L:
            out.append("[" + _L[c] + "]+")
        elif c == "\u011f":
            out.append("[غكگق]*")
        elif c == "h":
            out.append("[حخ]*")
        elif c == "y":
            out.append("[كغ]?")
    return "".join(out)
def harf_uyumlu(l, o):
    try:
        return bool(re.fullmatch(_desen_l(l), _iskelet_o(o)))
    except re.error:
        return False


from engine import kok as _KOK
_ZKOK = getattr(_KOK, 'ZKOK', set())
_KOK_ONBELLEK = {}
def kok_cevirici(k):
    """kelimenin sozlukteki en uzun koku (en az 4 harf, kelimenin %60'i): ceviricinin o koku nasil yazdigi"""
    for i in range(len(k) - 1, 3, -1):
        p = k[:i]
        if i < 0.5 * len(k):
            break
        if p in D.DICTIONARY or p in _ZKOK:
            if p not in _KOK_ONBELLEK:
                _KOK_ONBELLEK[p] = kiyas(tt(p))
            return _KOK_ONBELLEK[p]
    return None


# (b) Kok tutarliligi: kelimenin en uzun koku Hayrat'ta sik geciyorsa (>= 5 kez) yazimi o kokle baslamali (son harf degisebilir).
def kok_tutarli(k, o, sik):
    for i in range(len(k) - 1, 2, -1):
        p = k[:i]
        if p in sik:
            r = sik[p]
            if len(r) <= 2:
                return True
            return kiyas(o).startswith(r[:-1])
    return True


def liste(ad, sutun=0):
    s = set()
    yol = os.path.join(VERI, ad)
    if os.path.exists(yol):
        for x in open(yol, encoding="utf-8"):
            if x.strip() and not x.startswith("#"):
                s.add(kucuk(x.split("\t")[sutun].strip()))
    return s


ESSESLI = {"et", "alem", "adet", "kalıp"} | liste("anlam_farki_kelimeler.tsv") | liste("baglam_kurallari.tsv") | liste("hayrat_baglam.tsv")
MEVCUT = set(D.DICTIONARY)

say = collections.defaultdict(collections.Counter)
for satir in open(GIRDI, encoding="utf-8"):
    p = satir.rstrip("\n").split("\t")
    if len(p) != 3:
        continue
    l, o, n = p[0].strip(), p[1].strip(), int(p[2])
    if not l or " " in l or "-" in l or re.search(r"[\d؀-ۿ]", l) or not re.search(r"[A-Za-zÇĞİÖŞÜçğıöşüâîû]", l):
        continue
    o2 = osm(o)
    if o2 and not re.search(r"[^؀-ۿ‌ ]", o2):
        say[kucuk(l)][o2] += n

SIK = {}
for _k, _c in say.items():
    _o, _m = _c.most_common(1)[0]
    if _m >= 5 and _m / sum(_c.values()) >= 0.7:
        SIK[_k] = kiyas(_o)

aday = []
for k, c in say.items():
    top = sum(c.values())
    o, m = c.most_common(1)[0]
    if k in MEVCUT or m / top < 0.7 or len(k) < 3 or k in ESSESLI:
        continue
    if D.turkish_lower(k) in D._EK_ANAHTAR:
        continue
    aday.append((k, o, top))

cikan = collections.Counter()
yaz, supheli = [], []
for k, o, top in aday:
    simdi = tt(k).strip()
    if kiyas(simdi) == kiyas(o):
        cikan["zaten ayni"] += 1
        continue
    if kiyas(simdi).replace("ڭ", "ن") == kiyas(o).replace("ڭ", "ن"):
        cikan["senin/onun (kef-i nuni)"] += 1
        continue
    if kiyas(o).count("ڭ") > kiyas(simdi).count("ڭ") and not re.search("n[gk]", k):
        cikan["senin eki olabilir (fazla kef-i nuni)"] += 1
        continue
    if k.endswith(("lar", "ler")) and kiyas(o).endswith("لار") and kiyas(simdi).endswith("لر"):
        cikan["cogul mu fiil mi belirsiz (-lar)"] += 1
        continue
    kk = kok_cevirici(k)
    if kk and not kiyas(o).startswith(kk[:-1]):
        supheli.append((k, o, top, simdi, "kokun cevirici yazimiyla celisiyor (kitapta tutarsizlik olur)"))
        continue
    if " " in o and len(set(o.split())) < len(o.split()):
        supheli.append((k, o, top, simdi, "Osmanlicada ayni kelime tekrar"))
        continue
    if kiyas(o).startswith("\u0626\u0648") and kiyas(simdi).startswith("\u0627\u0648") and kiyas(o)[2:] == kiyas(simdi)[2:]:
        cikan["yalniz basta hemze (ئو/او)"] += 1
        continue
    if not harf_uyumlu(k, o):
        supheli.append((k, o, top, simdi, "harf uyumu yok"))
        continue
    if not kok_tutarli(k, o, SIK):
        supheli.append((k, o, top, simdi, "kokun Hayrat yazimiyla celisiyor"))
        continue
    yaz.append((k, o, top))
with open(CIKTI, "w", encoding="utf-8") as f:
    f.write("# Tur L: Hayrat'ta az gecen ya da sozluge girmemis kelimeler (tools/hayrat_tek_uret.py). Hayrat kelimesi gibi korunur.\n")
    for k, o, top in sorted(yaz):
        f.write(f"{k}\t{o}\thayrat\t{top}\n")
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "hayrat_tek_supheli.tsv"), "w", encoding="utf-8") as f:
    f.write("latince\thayrat\tcevirici_bugun\tsayi\tsebep\n")
    for k, o, top, simdi, neden in sorted(supheli, key=lambda x: (x[4], x[0])):
        f.write(f"{k}\t{o}\t{simdi}\t{top}\t{neden}\n")
print(f"aday {len(aday)} | eklenen {len(yaz)} | supheli (alinmadi) {len(supheli)} {dict(collections.Counter(x[4] for x in supheli))} | alinmayan: {dict(cikan)}")
