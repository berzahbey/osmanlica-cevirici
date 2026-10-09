# -*- coding: utf-8 -*-
"""Hayrat'tan EK SONU KURALLARI öğrenir (sözlükte olmayan kelimeler için).
Her Hayrat kelimesi sözlükten geçici olarak çıkarılır (5 parça, sırayla), çeviricinin o kelimeyi "hiç görmemiş gibi"
yazdığı biçim Hayrat'ınkiyle karşılaştırılır. Kelime sonundaki tutarlı farklar kural olur:
  Latin son ek S + çeviricinin yazdığı son t1  ->  Hayrat'ın yazdığı son t2   (en az ENAZ farklı kelimede; bozduğu doğru kelime iyileştirdiğinin %5ini geçmez)
Ölçüm dürüst olsun diye 5 katlı çapraz doğrulama: kurallar 4 parçadan öğrenilir, 5. parçada denenir.
Çalıştırma (kod klasöründe):  OSM_EK_KURAL=0 PYTHONPATH=app python3 tools/hayrat_ek_ogren.py [kelime_ciftleri.tsv]
Çıktı: app/data/hayrat_ek_kurallari.tsv  (S, t1, t2, iyi, uygulanan)"""
import sys, os, re, collections, unicodedata, zlib
os.environ["OSM_EK_KURAL"] = "0"
import logging; logging.disable(logging.WARNING)
from engine import transliterator as T, dictionary as D
from engine.alphabet import turkish_lower

ZW = "\u200c"
ENAZ = int(os.environ.get("ENAZ", "3"))
BOZAN = float(os.environ.get("BOZAN", "0.05"))
GIRDI = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "hayrat_kelime_ciftleri.tsv")
CIKTI = os.path.join(os.path.dirname(__file__), "..", "app", "data", "hayrat_ek_kurallari.tsv")


def norm(o):
    o = unicodedata.normalize("NFC", o).replace("\u06d5", "\u0647").replace("\u06c0", "\u0647") \
        .replace("\u06af", "\u0643").replace("\u06a9", "\u0643").replace("\u064a", "\u06cc").replace("\u0649", "\u06cc") \
        .replace("\u0623", "\u0627")
    return re.sub("[\u064b-\u065f\u0670\u0640\u0654\u200c\u200d ]", "", o)


def cevir_hayrat(o):
    """Hayrat yazımını çeviricinin harf düzenine getirir; kelime içindeki ە (bitişmeyen he) -> ه + ara boşluk."""
    o = unicodedata.normalize("NFC", o).replace("\u06c0", "\u0647\u0654").replace("\u064a", "\u06cc") \
        .replace("\u0649", "\u06cc").replace("\u06af", "\u0643").replace("\u06a9", "\u0643")
    o = re.sub("[\u064b-\u0650\u0652\u0653\u0655-\u065f\u0670\u0640\u200d]", "", o)
    o = re.sub("\u06d5(?=[\u0621-\u06ff])", "\u0647" + ZW, o).replace("\u06d5", "\u0647")
    return o


def oku():
    H = collections.defaultdict(collections.Counter)
    for l in open(GIRDI, encoding="utf-8"):
        p = l.rstrip("\n").split("\t")
        if len(p) < 3 or " " in p[0] or "'" in p[0] or "\u2019" in p[0] or "-" in p[0]:
            continue
        H[turkish_lower(p[0])][cevir_hayrat(p[1])] += int(p[2])
    veri = {}
    for w, c in H.items():
        n = sum(c.values())
        d, dn = c.most_common(1)[0]
        if n >= 2 and dn / n >= 0.7 and len(w) >= 4:
            veri[w] = d
    return veri


def gorulmemis(veri):
    """Her kelimenin, kendisi sözlükte yokken çıkan yazımı (5 parça)."""
    parca = {w: zlib.crc32(w.encode()) % 5 for w in veri}
    cikti = {}
    for k in range(5):
        kel = [w for w in veri if parca[w] == k]
        sakla = {}
        for w in kel:
            for anahtar in {w, D._flat(w)}:
                for tablo in (D.DICTIONARY, D.FLAT):
                    if anahtar in tablo:
                        sakla[(id(tablo), anahtar)] = (tablo, tablo.pop(anahtar))
            D.HAYRAT_ANAHTAR.discard(w)
        for w in kel:
            cikti[w] = T.transliterate_text(w)
        for (_, anahtar), (tablo, deger) in sakla.items():
            tablo[anahtar] = deger
        for w in kel:
            D.HAYRAT_ANAHTAR.add(w)
        print("parca", k + 1, "/5:", len(kel), "kelime", flush=True)
    return cikti, parca


def son_bul(o, t1):
    """o'nun ara boşluk hariç t1 ile biten en kısa sonu (uzunluk) ya da None."""
    for k in range(len(t1), len(t1) + 4):
        if k <= len(o) and o[-k:].replace(ZW, "") == t1:
            return k
    return None


def uygula(kurallar, w, o):
    """kurallar: {S: [(t1, t2), ...]} — en uzun S, sonra en uzun t1."""
    for L in range(min(8, len(w) - 2), 1, -1):
        for t1, t2 in kurallar.get(w[-L:], ()):
            k = son_bul(o, t1)
            if k:
                return o[:-k] + t2
    return o


def ogren(kelimeler, veri, cikti):
    aday = set()
    for w in kelimeler:
        o, h = cikti[w], veri[w]
        no, nh = norm(o), norm(h)
        if no == nh:
            continue
        p = 0
        while p < min(len(no), len(nh)) and no[p] == nh[p]:
            p += 1
        for e in range(0, 3):
            q = p - e
            if q < 0 or len(no) - q > 6 or len(nh) - q > 7:
                continue
            t1 = no[q:]
            if not t1:
                continue
            # t2'yi Hayrat'ın (ara boşluklu) yazımından al
            hedef = nh[q:]
            t2 = None
            for k in range(len(hedef), len(hedef) + 4):
                if k <= len(h) and norm(h[-k:]) == hedef:
                    t2 = h[-k:]
                    break
            if t2 is None:
                continue
            for L in range(2, min(8, len(w) - 2) + 1):
                aday.add((w[-L:], t1, t2))
    sonek = collections.defaultdict(list)
    for w in kelimeler:
        for L in range(2, min(8, len(w) - 2) + 1):
            sonek[w[-L:]].append(w)
    kural = collections.defaultdict(list)
    for S, t1, t2 in aday:
        iyi = bozan = uyg = 0
        for w in sonek[S]:
            o = cikti[w]
            k = son_bul(o, t1)
            if not k:
                continue
            uyg += 1
            yeni = norm(o[:-k] + t2)
            if yeni == norm(veri[w]):
                iyi += 1
            elif norm(o) == norm(veri[w]):
                bozan += 1
        if iyi >= ENAZ and bozan <= BOZAN * iyi and iyi / uyg >= 0.6:
            kural[S].append((t1, t2, iyi, uyg))
    for S in kural:
        kural[S].sort(key=lambda x: (-len(x[0]), -x[2]))
    return kural


def olc(kural, kelimeler, veri, cikti):
    k2 = {S: [(a, b) for a, b, *_ in v] for S, v in kural.items()}
    once = sonra = 0
    for w in kelimeler:
        nh = norm(veri[w])
        once += norm(cikti[w]) == nh
        sonra += norm(uygula(k2, w, cikti[w])) == nh
    return once, sonra, len(kelimeler)


if __name__ == "__main__":
    veri = oku()
    print("Hayrat kelimesi:", len(veri))
    cikti, parca = gorulmemis(veri)
    for k in range(5):
        egitim = [w for w in veri if parca[w] != k]
        sinav = [w for w in veri if parca[w] == k]
        kural = ogren(egitim, veri, cikti)
        o, s, n = olc(kural, sinav, veri, cikti)
        print(f"capraz {k + 1}: gorulmemis kelime dogrulugu %{o / n * 100:.2f} -> %{s / n * 100:.2f}  ({n} kelime)", flush=True)
    kural = ogren(list(veri), veri, cikti)
    with open(CIKTI, "w", encoding="utf-8") as f:
        f.write("# Hayrat'tan öğrenilen ek sonu kuralları (tools/hayrat_ek_ogren.py). S\tçeviricinin_sonu\tHayrat_sonu\tiyi\tuygulanan\n")
        for S in sorted(kural, key=lambda s: (-len(s), s)):
            for t1, t2, iyi, uyg in kural[S]:
                f.write(f"{S}\t{t1}\t{t2}\t{iyi}\t{uyg}\n")
    print("kural sayisi:", sum(len(v) for v in kural.values()), "->", CIKTI)
