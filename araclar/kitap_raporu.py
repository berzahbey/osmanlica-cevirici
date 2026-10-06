"""Bir kitabın Türkçe metninde Osmanlıca imlâ açısından bakılması gereken kelimeleri listeler (sekmeyle ayrılmış).
1) ŞÜPHELİ: sözlükte bulunan ama sözlük kaydının Latin ve Osmanlıca yazımı birbirini tutmayan kelimeler (OCR bozukluğu, fazla kelime).
2) SÖZLÜKTE YOK: sözlükte bulunamayıp kural motoruyla yazılan kelimeler (Arapça/Farsça olanlar düzeltme dosyasına eklenmeli);
   Arapça görünümlü olanlara OpenITI sıklık listesinden yazım önerisi (araclar/oneri.py) — öneriler gözden geçirilmeden eklenmez.
Kullanım (kod klasöründe):
  docker run --rm -v "$PWD":/k -w /k -v /yol/kitap.txt:/kitap.txt:ro berzahbey/osmanlica-cevirici:latest \
      python araclar/kitap_raporu.py /kitap.txt > rapor.tsv
"""
import collections, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import dictionary as D, transliterator as T          # noqa: E402
from engine.alphabet import turkish_lower                         # noqa: E402
from sozluk_denetim import hata                                   # noqa: E402
import re                                                         # noqa: E402
try:
    import oneri                                                  # OpenITI sıklık listesiyle öneri
except Exception:                                                 # liste yoksa öneri sütunu boş kalır
    oneri = None

_INCE, _KALIN = set("eiöüî"), set("aıouâû")


def arapca_gibi(k):
    """Kök Arapça/Farsça görünümlü mü (şapka, çift ünsüz, ünlü uyumu bozuk, mü-/te- başı, -iyet/-at sonu)."""
    if re.search("[çğö]", k):
        return False
    if re.search("[âîû]", k) or re.search(r"([bcdfghjklmnprsştvyz])\1", k):
        return True
    vs = [c for c in k if c in _INCE | _KALIN]
    if vs and not (all(c in _INCE for c in vs) or all(c in _KALIN for c in vs)):
        return True
    return bool(re.match(r"(mü|mu|te|ta)", k) and len(k) >= 6) or bool(re.search(r"(iyet|iyat)$", k))


def oner(w):
    """Kelimenin kendisi ya da eki ayrılmış kökü için öneri: (kök, [(yazım, sıklık)...]) ya da None."""
    if oneri is None:
        return None
    if re.search(r"(ıyor|iyor|uyor|üyor|yor)", w) or re.search(r"[dt][ıiuü](m|n|k|nız|niz|lar|ler)?$", w):
        return None   # Türkçe fiil çekimi
    ekler = D._ISIM_EKLERI | {"dir", "dır", "dur", "dür", "tir", "tır", "tur", "tür"}

    def bol(x, n):
        return not x or (n > 0 and any(x.startswith(e) and bol(x[len(e):], n - 1) for e in ekler))
    for L in range(len(w), 3, -1):
        k = w[:L]
        if (L == len(w) or bol(w[L:], 4)) and arapca_gibi(k):
            o = oneri.oner(k)
            if o and o[0][1] >= 100:
                return k, o
    return None

metin = open(sys.argv[1], encoding="utf-8").read()
sayac = collections.Counter(turkish_lower(w).replace("’", "'") for w in T.WORD_RE.findall(metin))
supheli, yok = collections.Counter(), collections.Counter()
ornek, kayit = {}, {}
for w, n in sayac.items():
    b = w.split("'")[0]
    hit, sufs = D.lookup_with_suffix(b)
    if hit:
        kok = b[: len(b) - len("".join(sufs))] if sufs else b
        if hata(kok, hit[0]) > 0:
            supheli[kok] += n
            kayit[kok] = hit
            ornek.setdefault(kok, w)
    else:
        yok[w] += n
print("tür\tkelime\tkaç kez\tşu anki yazım\tköken\töneri (kök: yazım/sıklık; gözden geçirilmeli)")
for k, n in supheli.most_common():
    print(f"ŞÜPHELİ\t{k}\t{n}\t{kayit[k][0]}\t{kayit[k][1]}")
for w, n in yok.most_common(int(os.environ.get("RAPOR_SINIR", "500"))):
    o = oner(w.split("'")[0])
    o = f"{o[0]}: " + ", ".join(f"{a}/{b}" for a, b in o[1]) if o else ""
    print(f"SÖZLÜKTE YOK\t{w}\t{n}\t{T.draft_transliterate_sentence(w)}\tkural\t{o}")
