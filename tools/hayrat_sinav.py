"""Osmanlıca çevirici SINAVI: sözlük yalnız eğitim eserlerinden kurulur, ölçüm çeviricinin hiç görmediği sınav eserlerinde.
Osmanlıca çevirici konteynerinde: python3 /tmp/hayrat_sinav.py
Girdi: /data/hayrat_egitim_kelime.tsv, /data/hayrat_sinav_kelime.tsv   Çıktı: /data/hayrat_sinav.txt
İki sayı: genel doğruluk ve KURAL MOTORU doğruluğu (sözlükte hiç olmayan kelimeler: Risale dışı kitapların belirleyicisi)."""
import collections, os, re, sys, time, unicodedata

ESIK_YENI, ESIK_DEGIS, ORAN = 2, 3, 0.7
CIFT_ANLAMLI = {"et", "alem", "adet", "kalıp"}
HAREKE_S = re.compile("[\u064B-\u0650\u0652-\u065F\u0670\u06D6-\u06ED\u0640\u200c\u200d\u200e\u200f]")
HAREKE_K = re.compile("[\u064B-\u0653\u0655-\u065F\u0670\u06D6-\u06ED\u0640\u200c\u200d\u200f\u200e]")
ARAP_OZEL = re.compile("[عحطظصضثذقغ]")
SAPKA = str.maketrans({"â": "a", "î": "i", "û": "u", "ā": "a", "ī": "i", "ū": "u", "ō": "o"})
LATIN = re.compile("[A-Za-zÇĞİÖŞÜçğıöşüÂÎÛâîû]")


def harf(o):
    o = unicodedata.normalize("NFC", o or "")
    o = o.replace("\u06C0", "\u0647\u0654").replace("\u06D5", "\u0647").replace("\u064A", "\u06CC").replace("\u0649", "\u06CC")
    return o.replace("\u06A9", "\u0643").replace("\u06AF", "\u0643").replace("\u06C1", "\u0647")


def sozluk_yazim(o):
    return re.sub(r"[\s،؛؟.,;:!?«»\"()\[\]]", "", HAREKE_S.sub("", harf(o)))


def kiyas(o):
    o = HAREKE_K.sub("", harf(o))
    return re.sub(r"\s+", " ", re.sub(r"[،؛؟.,;:!?«»\"'()\[\]\-]", " ", o)).strip()


def kucuk(w):
    return w.replace("I", "ı").replace("İ", "i").lower().replace("’", "'").replace("`", "'").replace("ʼ", "'")


def sapkasiz(k):
    return k.translate(SAPKA).replace("‘", "").replace("ʿ", "").replace("ʻ", "")


EK_AYRAC = set("ın in un ün nın nin nun nün a e ya ye ı i u ü yı yi yu yü da de ta te dan den tan ten la le yla yle "
               "dır dir dur dür tır tir tur tür ca ce ça çe ki dır".split())


def hemzesiz(k):
    """mes'ele -> mesele, te'min -> temin (kesme işareti ek ayıracıysa değil: allah'ın)."""
    p = k.split("'")
    return k.replace("'", "") if len(p) == 2 and p[0] and p[1] and p[1] not in EK_AYRAC else None


def oku(yol):
    for s in open(yol, encoding="utf-8"):
        p = s.rstrip("\n").split("\t")
        if len(p) == 3:
            yield p[0].strip(), p[1].strip(), int(p[2])


# ---- 1) eğitim sözlüğü (yama_hayrat_tam ile aynı kurallar, yalnız eğitim eserlerinden) ----
mevcut = {}
for yol in ("/app/data/ottoman_dict.tsv", "/app/data/duzeltmeler.tsv"):
    for s in open(yol, encoding="utf-8"):
        p = s.rstrip("\n").split("\t")
        if len(p) >= 2 and p[0]:
            mevcut[p[0]] = p[1]
sayim = collections.defaultdict(collections.Counter)
for l, o, n in oku("/data/hayrat_egitim_kelime.tsv"):
    if not l or " " in l or "-" in l or re.search(r"[\d\u0600-\u06FF]", l) or not LATIN.search(l):
        continue
    o2 = sozluk_yazim(o)
    if o2 and not re.search(r"[^\u0600-\u06FF]", o2):
        sayim[kucuk(l)][o2] += n
egitim = {}
for k, c in sayim.items():
    top = sum(c.values()); o, n = c.most_common(1)[0]
    if n / top < ORAN:
        continue
    h = hemzesiz(k)
    for anahtar, turetilmis in ((k, False), (sapkasiz(k), True), (h, True), (h and sapkasiz(h), True)):
        if not anahtar or anahtar in egitim or anahtar in CIFT_ANLAMLI:
            continue
        eski = mevcut.get(anahtar)
        if (eski is None and top >= ESIK_YENI) or (eski is not None and not turetilmis and top >= ESIK_DEGIS
                                                   and kiyas(eski).replace("\u0651", "") != kiyas(o).replace("\u0651", "")):
            egitim[anahtar] = (o, "ar" if ARAP_OZEL.search(o) else "tr")
with open("/tmp/hayrat_egitim.tsv", "w", encoding="utf-8") as f:
    for k in sorted(egitim):
        f.write(f"{k}\t{egitim[k][0]}\t{egitim[k][1]}\n")
os.environ["HAYRAT_DOSYA"] = "/tmp/hayrat_egitim.tsv"

# ---- 2) çevirici (eğitim sözlüğüyle) ----
sys.path.insert(0, "/app")
import logging
logging.disable(logging.CRITICAL)
from engine import dictionary as D
from engine.transliterator import transliterate_text as tt
if str(D.HAYRAT_FILE) != "/tmp/hayrat_egitim.tsv":
    print("HATA: çevirici eğitim sözlüğünü yüklemedi (dictionary.py'de HAYRAT_DOSYA desteği yok)"); sys.exit(1)

# ---- 3) sınav ----
yazim = collections.defaultdict(collections.Counter)
for l, o, n in oku("/data/hayrat_sinav_kelime.tsv"):
    if LATIN.search(l) and not re.search(r"[\d\u0600-\u06FF]", l) and re.search(r"[\u0600-\u06FF]", o):
        yazim[l][kiyas(o)] += n
sonuc = collections.defaultdict(lambda: [0, 0])     # tür -> [doğru, toplam] (geçme sıklığına göre)
hatalar = collections.defaultdict(list)
t0 = time.time()
for i, (l, c) in enumerate(sorted(yazim.items(), key=lambda x: -sum(x[1].values()))):
    adet = sum(c.values())
    if " " in l or "-" in l:
        tur = "çok kelimeli"
    else:
        k = kucuk(l)
        tur = "sözlükte var" if (k in D.DICTIONARY or sapkasiz(k) in D.DICTIONARY) else "KURAL MOTORU"
    try:
        bizim = kiyas(tt(l, use_ollama_refine=False))
    except Exception as e:
        bizim = f"HATA:{type(e).__name__}"
    sonuc[tur][1] += adet
    sonuc["GENEL"][1] += adet
    if bizim in c:
        sonuc[tur][0] += adet
        sonuc["GENEL"][0] += adet
    else:
        hatalar[tur].append((adet, l, bizim, c.most_common(1)[0][0]))
    if i % 3000 == 0:
        print(f"  {i}/{len(yazim)}  {time.time() - t0:.0f} sn", flush=True)

with open("/data/hayrat_sinav.txt", "w", encoding="utf-8") as f:
    f.write(f"HAYRAT SINAVI — eğitim sözlüğü {len(egitim)} kayıt; sınav: {len(yazim)} kelime grubu\n")
    for tur in ("GENEL", "KURAL MOTORU", "sözlükte var", "çok kelimeli"):
        d, t = sonuc[tur]
        f.write(f"  {tur:14s} %{100 * d / max(1, t):6.2f}   ({t} kez)\n")
    for tur, sinir in (("KURAL MOTORU", 400), ("sözlükte var", 150), ("çok kelimeli", 80)):
        f.write(f"\n== {tur}: en sık {sinir} hata (kez | Latin | bizim | Hayrat)\n")
        for adet, l, b, h in sorted(hatalar[tur], reverse=True)[:sinir]:
            f.write(f"{adet:>5}  {l:26s}  {b:22s}  {h}\n")
print(open("/data/hayrat_sinav.txt", encoding="utf-8").read().split("\n== ")[0], flush=True)
