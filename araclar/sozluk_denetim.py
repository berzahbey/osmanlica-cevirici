"""Sözlük kaydının Latin yazımı ile Osmanlıca yazımı birbirini tutuyor mu (ünsüz iskeleti hizalaması).
Hata sayısı 0 değilse kayıt şüpheli (OCR bozukluğu, fazladan kelime, yanlış harf)."""
import re, unicodedata
IZIN = {
 "b": "بپ", "c": "جچ", "ç": "چج", "d": "دضذطت", "f": "ف", "g": "گغكق", "ğ": "غگكی", "h": "حهخ",
 "j": "ژج", "k": "كقگ", "l": "ل", "m": "م", "n": "نڭم", "p": "پب", "r": "ر", "s": "سصث", "ş": "ش",
 "t": "تطثدة", "v": "وف", "y": "ی", "z": "زذضظ", "x": "كس", "q": "ق", "w": "و",
}
SESSIZ_ATLANIR = set("اویهعءة")   # okutucu harfler ve ayın/hemze Latin'de karşılıksız olabilir
def lat_iskelet(s):
    s = s.lower().replace("â","a").replace("î","i").replace("û","u").replace("ı","ı")
    s = re.sub(r"[^a-zçğışöü]", "", s)
    out = []
    onceki = ""
    for ch in s:
        if ch not in "aeıioöuü" and ch == onceki:
            onceki = ch
            continue                             # yan yana çift ünsüz = şedde (tek harf)
        if ch not in "aeıioöuü":
            out.append(ch)
        onceki = ch
    return out
def ar_norm(s):
    s = unicodedata.normalize("NFC", s)
    s = re.sub(r"[\u064B-\u065F\u0670\u0651\u200c\u200d\u0640 ]", "", s)
    tr = str.maketrans({"ي":"ی","ى":"ی","ک":"ك","أ":"ا","إ":"ا","آ":"ا","ؤ":"و","ئ":"ی","ۀ":"ه"})
    s = s.translate(tr)
    s = re.sub(r"[^\u0600-\u06FF]", "", s)
    return s
def hata(latin, osm):
    h = _hata(lat_iskelet(latin), ar_norm(osm))
    lat = latin.lower().replace("â", "a")
    if h and re.search(r"[aeı]n$", lat) and ar_norm(osm).endswith("ا"):   # tenvin: ahîren -> اخیرا
        h = min(h, _hata(lat_iskelet(lat[:-1]), ar_norm(osm)))
    return h


def _hata(L, A):
    n, m = len(L), len(A)
    INF = 10**9
    d = [[INF]*(m+1) for _ in range(n+1)]
    d[0][0] = 0
    for i in range(n+1):
        for j in range(m+1):
            v = d[i][j]
            if v == INF: continue
            if i < n and j < m and A[j] in IZIN.get(L[i], ""):
                d[i+1][j+1] = min(d[i+1][j+1], v)
                if j + 1 < m and A[j+1] == A[j]:          # Arapçada iki ayrı harf (الله)
                    d[i+1][j+2] = min(d[i+1][j+2], v)
            if j < m:
                atla = A[j] in SESSIZ_ATLANIR or (A[j] == "ل" and j > 0 and A[j-1] == "ا")
                d[i][j+1] = min(d[i][j+1], v + (0 if atla else 1))
            if i < n:
                d[i+1][j] = min(d[i+1][j], v + 1)
    return d[n][m]
