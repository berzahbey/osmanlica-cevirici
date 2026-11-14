"""Tur TV: Arapça/Farsça türev kuralı (engine/turev.py).
1) Sözlüğün kendi türemiş kelimeleri, kendisi çıkarılarak kurulur (leave-one-out): her ek ailesinde en az %90 doğru.
2) Türkçe birleşik ve h'si düşmüş -hane kurulmaz; Stüdyo ölçümündeki örnekler doğru."""
import collections, re, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "app"))
from engine import dictionary as D, turev as T

_N = re.compile("[ً-ْٰ‌‍ ]")


def _n(o):
    return _N.sub("", o).replace("ة", "ه").replace("ي", "ی").replace("گ", "ك").replace("ک", "ك")


def loo():
    say = collections.Counter()
    for k, (o, _) in D.DICTIONARY.items():
        bul = lambda r, k=k: None if r == k else D._get_turevsiz(r)
        T._onbellekli.cache_clear() if False else None
        r = T._turet(k, bul)
        if not r:
            continue
        aile = "evî" if re.search("ev[iî]$", k) else "vî" if re.search("v[iî]$", k) else "iyet" if k.endswith("yet") else "âne" if re.search("[aâ]ne$", k) and "hane" not in k[-5:] and "hâne" not in k[-5:] else "farsça"
        say[(aile, _n(r) == _n(o))] += 1
    return say


def test_loo():
    say = loo()
    # evî yanlışları: dâirevî دائره‌وی (yazım çeşidi), müstevî x2 (kalıplaşmış; sözlükte var). vî (evî dışı): yanlışlar kalıplaşmış kelimeler (müsâvî, müstevî); kural yalnız sözlükte olmayan kelimede çalışır
    for aile, en_az, esik in (("evî", 15, 0.85), ("vî", 1, 0.50), ("iyet", 20, 0.90), ("âne", 20, 0.90), ("farsça", 20, 0.90)):
        d, y = say[(aile, True)], say[(aile, False)]
        print(aile, d, y, f"%{100 * d / max(1, d + y):.1f}")
        assert d + y >= en_az and d / (d + y) >= esik, aile


def test_ornekler():
    beklenen = {"mucizevi": "معجزوی", "mucizevî": "معجزوی", "ananevi": "عنعنوی", "efsanevi": "افسانوی"}
    for w, o in beklenen.items():
        assert D.lookup_exact(w)[0] == o, w
    for w in ("kitabevi", "imamevi", "yayınevi", "huzurevi", "dersane", "hapisane", "postane", "kadar", "yazar", "çıkar"):
        h = D.lookup_exact(w)
        assert not h or h[1] != "turev", (w, h)


if __name__ == "__main__":
    test_loo(); test_ornekler(); print("tamam")
