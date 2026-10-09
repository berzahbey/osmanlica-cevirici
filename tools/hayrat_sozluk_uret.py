"""Canlı Hayrat sözlüğünü (/app/data/hayrat.tsv) bütün Hayrat verisinden yeniden üretir. Konteynerde root olarak:
    python3 /tmp/hayrat_sozluk_uret.py
Kurallar (hayrat_sinav.py ile aynı): mevcut kaydı geçmek için en az 3 kez ve %70; eksik kelime için en az 2 kez ve %70.
Hayrat'ın kendi anahtarı her zaman; türetilmiş anahtarlar (şapkasız, hemzesiz) yalnız sözlükte yoksa.
Çift anlamlı et/alem/adet/kalıp eski kayıtta kalır. Rapor: /data/hayrat_degisen.tsv"""
import collections, re, unicodedata

GIRDI = "/data/hayrat_kelime.tsv"
CIKTI = "/app/data/hayrat.tsv"
KAYNAKLAR = {"sözlük": "/app/data/ottoman_dict.tsv", "düzeltme": "/app/data/duzeltmeler.tsv"}
ESIK_YENI, ESIK_DEGIS, ORAN = 2, 3, 0.7
CIFT_ANLAMLI = {"et", "alem", "adet", "kalıp"}
HAREKE = re.compile("[\u064B-\u0650\u0652\u0653\u0655-\u065F\u0670\u06D6-\u06ED\u0640\u200d\u200e\u200f]")   # ara boşluk (\u200c) korunur
ARAP_OZEL = re.compile("[عحطظصضثذقغ]")
SAPKA = str.maketrans({"â": "a", "î": "i", "û": "u", "ā": "a", "ī": "i", "ū": "u", "ō": "o"})
EK_AYRAC = set("ın in un ün nın nin nun nün a e ya ye ı i u ü yı yi yu yü da de ta te dan den tan ten la le yla yle "
               "dır dir dur dür tır tir tur tür ca ce ça çe ki".split())


def osm(o):
    o = unicodedata.normalize("NFC", o)
    o = o.replace("\u06C0", "\u0647\u0654").replace("\u064A", "\u06CC").replace("\u0649", "\u06CC")
    o = re.sub("\u06D5(?=[\u0621-\u06FF])", "\u0647\u200c", o).replace("\u06D5", "\u0647")   # kelime içi ە: bitişmeyen he (ه + ara boşluk)
    o = o.replace("\u06A9", "\u0643").replace("\u06AF", "\u0643")
    o = re.sub(r"[،؛؟.,;:!?«»\"()\[\]]", "", HAREKE.sub("", o))
    return re.sub(r"\s+", " ", o).strip()   # içteki boşluk korunur (بدیع الزمان)


def kiyas(o):
    return osm(o).replace("\u0651", "").replace("\u200c", "")


def kucuk(w):
    return w.replace("I", "ı").replace("İ", "i").lower().replace("’", "'").replace("`", "'").replace("ʼ", "'")


def sapkasiz(k):
    return k.translate(SAPKA).replace("‘", "").replace("ʿ", "").replace("ʻ", "")


def hemzesiz(k):
    p = k.split("'")
    return k.replace("'", "") if len(p) == 2 and p[0] and p[1] and p[1] not in EK_AYRAC else None


def ifade_anahtar(s):
    s = s.replace("I", "ı").replace("İ", "i").lower()
    for c in "\u2019\u2018\u02bc\u02bb`":
        s = s.replace(c, "'")
    return re.sub(r"\s+", " ", s.replace("\u2010", "-")).strip()


def ifade_uret(satirlar, cikti):
    """Çok kelimeli Hayrat ifadeleri (en az 3 kez, %70 aynı yazım): Aleyhissalâtü Vesselâm -> علیه الصلاة والسلام"""
    say = collections.defaultdict(collections.Counter)
    for l, o, n in satirlar:
        if not (" " in l.strip() or "-" in l) or re.search(r"[\d\u0600-\u06FF]", l) or not re.search(r"[A-Za-zÇĞİÖŞÜçğıöşüâîû]", l):
            continue
        o2 = osm(o)
        if o2 and not re.search(r"[^\u0600-\u06FF ]", o2):
            say[ifade_anahtar(l)][o2] += n
    yaz = {}
    for k, c in say.items():
        top = sum(c.values()); o, n = c.most_common(1)[0]
        if top >= 3 and n / top >= 0.7:
            for a in (k, k.translate(SAPKA)):
                yaz.setdefault(a, o)
    with open(cikti, "w", encoding="utf-8") as f:
        for k in sorted(yaz):
            f.write(f"{k}\t{yaz[k]}\n")
    return len(yaz)


mevcut = {}
for kaynak, yol in KAYNAKLAR.items():
    for s in open(yol, encoding="utf-8"):
        p = s.rstrip("\n").split("\t")
        if len(p) >= 2 and p[0]:
            mevcut[p[0]] = (p[1], kaynak)

sayim = collections.defaultdict(collections.Counter)
for satir in open(GIRDI, encoding="utf-8"):
    p = satir.rstrip("\n").split("\t")
    if len(p) != 3:
        continue
    l, o, n = p[0].strip(), p[1].strip(), int(p[2])
    if not l or " " in l or "-" in l or re.search(r"[\d\u0600-\u06FF]", l) or not re.search(r"[A-Za-zÇĞİÖŞÜçğıöşüâîû]", l):
        continue
    o2 = osm(o)
    if o2 and not re.search(r"[^\u0600-\u06FF ]", o2):
        sayim[kucuk(l)][o2] += n

yeni, degisen = {}, []
for k, c in sayim.items():
    top = sum(c.values())
    o, n = c.most_common(1)[0]
    if n / top < ORAN:
        continue
    koken = "ar" if ARAP_OZEL.search(o) else "tr"
    h = hemzesiz(k)
    for anahtar, turetilmis in ((k, False), (sapkasiz(k), True), (h, True), (h and sapkasiz(h), True)):
        if not anahtar or anahtar in yeni or anahtar in CIFT_ANLAMLI:
            continue
        eski = mevcut.get(anahtar)
        if eski is None:
            if top >= ESIK_YENI:
                yeni[anahtar] = (o, koken)
        elif not turetilmis and top >= ESIK_DEGIS and kiyas(eski[0]) != kiyas(o):
            yeni[anahtar] = (o, koken)
            degisen.append((top, anahtar, eski[0], o, eski[1]))

with open(CIKTI, "w", encoding="utf-8") as f:
    for k in sorted(yeni):
        f.write(f"{k}\t{yeni[k][0]}\t{yeni[k][1]}\n")
with open("/data/hayrat_degisen.tsv", "w", encoding="utf-8") as f:
    for top, k, e, o, kay in sorted(degisen, reverse=True):
        f.write(f"{k}\t{e}\t{o}\t{kay}\t{top}\n")
def _satirlar():
    for s_ in open(GIRDI, encoding="utf-8"):
        p_ = s_.rstrip("\n").split("\t")
        if len(p_) == 3:
            yield p_[0].strip(), p_[1].strip(), int(p_[2])


print(f"Hayrat ifadeleri: {ifade_uret(_satirlar(), '/app/data/hayrat_ifade.tsv')}")
print(f"Hayrat sözlüğü: {len(yeni)} kayıt | eklenen: {sum(1 for k in yeni if k not in mevcut)} | değişen: {len(degisen)}")
