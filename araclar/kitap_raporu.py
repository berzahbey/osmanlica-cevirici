"""Bir kitabın Türkçe metninde Osmanlıca imlâ açısından bakılması gereken kelimeleri listeler (sekmeyle ayrılmış).
1) ŞÜPHELİ: sözlükte bulunan ama sözlük kaydının Latin ve Osmanlıca yazımı birbirini tutmayan kelimeler (OCR bozukluğu, fazla kelime).
2) SÖZLÜKTE YOK: sözlükte bulunamayıp kural motoruyla yazılan kelimeler (Arapça/Farsça olanlar düzeltme dosyasına eklenmeli).
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
print("tür\tkelime\tkaç kez\tşu anki yazım\tköken")
for k, n in supheli.most_common():
    print(f"ŞÜPHELİ\t{k}\t{n}\t{kayit[k][0]}\t{kayit[k][1]}")
for w, n in yok.most_common(int(os.environ.get("RAPOR_SINIR", "500"))):
    print(f"SÖZLÜKTE YOK\t{w}\t{n}\t{T.draft_transliterate_sentence(w)}\tkural")
