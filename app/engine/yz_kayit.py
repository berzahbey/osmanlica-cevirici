"""Tur YZ1 (12 Kasım 2026): yapay zekâ köken kaydı (Zahir'in tasarımı).
Sözlükte bulunmayan kelimenin kökenini Stüdyo yapay zekâya (Gemini) BİR KEZ sorar; cevap burada kalıcı kaydedilir, aynı kelime bir daha
sorulmaz. Çeviri sırasında yapay zekâ çalışmaz: çevirici kaydı sözlük gibi okur (aynı metin hep aynı Osmanlıcayı verir).
  - köken tr: Türkçe kurallar (kayıt yalnız "sorulmuş" demektir)
  - köken ar/fa: kökün aslî yazılışı (مهمیز، قهرمان، درد) sözlüğe kök olarak eklenir; ekleri çevirici yazar. Yazılış Latin harflerle
    uyuşmazsa (harf_uyumu) kayıt "kontrol" olur ve kullanılmaz.
  - öteki diller: okunuş (Charakter -> Karakter) yabancı okunuş tablosuna eklenir; Türkçe kurallar yazar.
Hayrat ve sözlükler her zaman önce gelir (kök sözlükte varsa eklenmez).
Dosyalar: app/data/yz_sozluk.tsv (GitHub'daki birikmiş kayıt) + $YZ_SOZLUK (sunucuda kalıcı, varsayılan /data/yz_sozluk.tsv)."""
import os
import re
import threading
import time
from pathlib import Path

from . import dictionary
from . import yabanci
from .alphabet import turkish_lower

ALANLAR = ["kelime", "koken", "kok", "yazilis", "okunus", "anlam", "durum", "model", "tarih"]
PAKET = Path(__file__).parent.parent / "data" / "yz_sozluk.tsv"
KALICI = Path(os.environ.get("YZ_SOZLUK", "/data/yz_sozluk.tsv"))
KAYIT = {}          # kelime (küçük harf) -> satır sözlüğü
_kilit = threading.Lock()

# Latin ünsüz -> Osmanlıcada karşılığı olabilecek harfler (harf uyumu denetimi için)
_UNSUZ = {"b": "بپ", "c": "جچ", "ç": "چج", "d": "دذضط", "f": "ف", "g": "غگكق", "ğ": "غگك", "h": "حهخ", "j": "ژج", "k": "كقخ",
          "l": "ل", "m": "م", "n": "نڭ", "p": "پب", "r": "ر", "s": "سصث", "ş": "ش", "t": "تطثدض", "v": "و", "y": "ی", "z": "زذضظ"}
_HARF_DISI = set("اوىیهعءأإآؤئةًٌٍَُِّْٰ‌")     # ünlü harfleri, ayın, hemze, harekeler: karşılaştırmada atlanır


def _unsuzler_latin(w):
    s = turkish_lower(w)
    s = re.sub(r"[^a-zçğıöşü]", "", s.translate(str.maketrans("âîû", "aiu")))
    out = [c for c in s if c in _UNSUZ]
    return [c for i, c in enumerate(out) if i == 0 or c != out[i - 1] or c in "y"]       # çift ünsüz (şedde) tek sayılır


def harf_uyumu(latin: str, osm: str) -> bool:
    """Arap harfli yazılışın ünsüzleri Latin yazımın ünsüzleriyle sırayla uyuşuyor mu (mahmuz ~ مهمیز: m-h-m-z).
    ا و ی ه ع ء ünlü harfi ya da fazladan harf olarak atlanabilir; atlanmazsa ünsüz (v, y, h) karşılığı sayılır."""
    if not osm or not re.fullmatch(r"[\u0600-\u06ff\u200c ]+", osm):
        return False
    a = [c for c in osm.replace(" ", "").replace("\u200c", "") if c not in "ًٌٍَُِّْٰ"]
    a = [c for i, c in enumerate(a) if i == 0 or c != a[i - 1]]
    lat = _unsuzler_latin(latin)
    atlanir = set("اوىیهعءأإآؤئة")
    from functools import lru_cache

    @lru_cache(maxsize=None)
    def es(i, j):
        if j == len(lat):
            return all(c in atlanir for c in a[i:])
        if i == len(a):
            return all(c == "y" for c in lat[j:])
        if a[i] in _UNSUZ.get(lat[j], "") and es(i + 1, j + 1):
            return True
        if lat[j] == "y" and es(i, j + 1):              # y ünlü harfiyle (ی) karşılanmış olabilir
            return True
        return a[i] in atlanir and es(i + 1, j)
    return es(0, 0)


def guvenilir(model: str) -> bool:
    """Tur YZ3 (13 Kasım 2026, model denemesi): Flash-Lite modelleri köken işinde güvenilmez (Türkçeyi Arapça sayıyor, yazılış
    yerine anlamdaş veriyor); gemini-4-hydrogen ve gemini-3.5-flash 35 kelimelik denemede hepsini doğru bildi. Lite kaydı
    uygulanmaz ve kelime güçlü modelle yeniden sorulur."""
    m = (model or "").lower()
    return bool(m) and "lite" not in m and "sahte" not in m


def _ar_fa_uygula(r):
    """Güvenilir modelin onaylı Arapça/Farsça kaydı: kök, aslî yazılışıyla sözlüğe eklenir (sözlükte varsa dokunulmaz;
    ekleri çevirici yazar: kahramanları -> قهرمانلری)."""
    kok = turkish_lower(r.get("kok") or "")
    osm = (r.get("yazilis") or "").replace("\u064a", "\u06cc").replace("\u06a9", "\u0643")
    if len(kok) < 3 or not osm or dictionary._get(kok):
        return
    dictionary.DICTIONARY[kok] = (osm, r["koken"])
    duz = dictionary._flat(kok)
    if duz != kok and duz not in dictionary.DICTIONARY:
        dictionary.DICTIONARY[duz] = (osm, r["koken"])


def _uygula(r):
    """Kaydı çeviriciye işler. Tur YZ2 (12 Kasım 2026, ilk gerçek deneme: Fransız Devrimine Bakış, 1186 kayıt):
    ücretsiz Flash-Lite modeli modern Türkçe kelimeleri (dönem, olay, toplum, etki, katkı) Arapça sayıyor, yazılış yerine eş anlamlı
    veriyordu (deprem -> زلزله، ilgi -> علق، karşın -> قرص). Bu yüzden:
      - ar/fa kaydı ÇEVİRİYE UYGULANMAZ, yalnız saklanır (her kelime yine bir kez sorulur; ileride daha güçlü modelle yeniden bakılır)
      - Batı dili okunuşu yalnız şu durumda uygulanır: kelime = kök (ekli değil), Türkçe harf (çğıöşü) yok, Türkçe sözlükte yok,
        okunuş kelimeden farklı ve bir kelime (çeviri değil: uluslararası -> internasyonal reddedilir)."""
    if r.get("durum") != "onayli":
        return
    k = r.get("koken", "")
    if k in ("ar", "fa") and guvenilir(r.get("model")):
        _ar_fa_uygula(r)
        return
    if k in ("tr", "ar", "fa", "") or not r.get("okunus"):
        return
    w, kok, ok = r["kelime"], r.get("kok") or "", r["okunus"]
    if w.lower() != kok.lower() or re.search(r"[çğıöşüÇĞİÖŞÜ]", w) or " " in ok:
        return
    if yabanci._turkce_mi(w) or ok.lower() == w.lower():
        return
    if not (w[:1].isupper() or re.search(r"[xwq]", w.lower())):
        return                                   # küçük harfli Türkçeleşmiş kelime (liberal, reform): Türkçe kurallar
    from difflib import SequenceMatcher
    if SequenceMatcher(None, w.lower(), ok.lower()).ratio() < 0.3:
        return                                   # okunuş kelimeye hiç benzemiyor: çeviri ya da yanlış
    yabanci._TABLO.setdefault(w.lower(), ok)


def _oku(yol):
    if not yol.exists():
        return
    for s in open(yol, encoding="utf-8"):
        if s.startswith("#") or "\t" not in s:
            continue
        p = s.rstrip("\n").split("\t")
        r = dict(zip(ALANLAR, p + [""] * (len(ALANLAR) - len(p))))
        if r["kelime"]:
            KAYIT[r["kelime"].lower()] = r


def _onbellek_sil():
    from . import onisle
    onisle._yeni_bicim.cache_clear()


def yukle():
    KAYIT.clear()
    for yol in (PAKET, KALICI):
        _oku(yol)
    for r in KAYIT.values():
        _uygula(r)
    _onbellek_sil()


def denetle(r):
    """Yapay zekâ cevabını düzene sokar ve denetler; durum alanını 'onayli' ya da 'kontrol' yapar."""
    r = {a: str(r.get(a) or "").strip().replace("\t", " ").replace("\n", " ") for a in ALANLAR}
    r["koken"] = r["koken"].lower()[:5]
    w = turkish_lower(r["kelime"])
    if r["koken"] in ("ar", "fa"):
        kok = turkish_lower(r["kok"] or r["kelime"])
        sade = lambda x: x.translate(str.maketrans("âîû", "aiu"))
        if not sade(w).startswith(sade(kok)[:max(3, len(kok) - 1)]):     # kök kelimenin başında olmalı (mahmuz+uyla)
            r["durum"] = "kontrol"
        elif not harf_uyumu(kok, r["yazilis"]):
            r["durum"] = "kontrol"
        else:
            r["durum"] = "onayli"
        r["kok"] = kok
    elif r["koken"] == "tr":
        r["durum"] = "onayli"
    else:
        r["durum"] = "onayli" if r["okunus"] and re.fullmatch(r"[A-Za-zÇĞİÖŞÜçğıöşüÂÎÛâîû' \-]+", r["okunus"]) else "kontrol"
    r["tarih"] = r["tarih"] or time.strftime("%Y-%m-%d")
    return r


def ekle(satirlar):
    """Yeni yapay zekâ cevaplarını kalıcı dosyaya ekler ve hemen uygular. Dönen: (onaylı, kontrol) sayıları."""
    on = ko = 0
    with _kilit:
        KALICI.parent.mkdir(parents=True, exist_ok=True)
        yeni_dosya = not KALICI.exists()
        with open(KALICI, "a", encoding="utf-8") as f:
            if yeni_dosya:
                f.write("# " + "\t".join(ALANLAR) + "\n")
            for r in satirlar:
                r = denetle(r)
                eski = KAYIT.get(r["kelime"].lower())
                if not r["kelime"] or eski and (guvenilir(eski.get("model")) or not guvenilir(r["model"])):
                    continue                     # Tur YZ3: Lite kaydının yerine güçlü modelin cevabı yazılır (son satır geçerli)
                f.write("\t".join(r[a] for a in ALANLAR) + "\n")
                KAYIT[r["kelime"].lower()] = r
                _uygula(r)
                on += r["durum"] == "onayli"
                ko += r["durum"] == "kontrol"
        _onbellek_sil()
    return on, ko


_KELIME = re.compile(r"[A-Za-zÇĞİÖŞÜçğıöşüÂÎÛâîû][A-Za-zÇĞİÖŞÜçğıöşüÂÎÛâîû\-]*")


def bilinmeyenler(metin: str, en_fazla: int = 100000):
    """Metindeki, hiçbir sözlükte / kayıtta bulunmayan ve henüz (güvenilir modele) sorulmamış kelimeler (tekil)."""
    from .onisle import _yeni_bicim
    gor, out = set(), []
    for m in _KELIME.finditer(metin or ""):
        w = m.group(0).strip("-")
        if len(w) < 3 or w in gor:
            continue
        gor.add(w)
        wl = turkish_lower(w)
        kayit = KAYIT.get(wl) or KAYIT.get(w.lower())
        if kayit and guvenilir(kayit.get("model")) or w.lower() in yabanci._TABLO or yabanci._roma(w):
            continue
        if wl in dictionary.HAYRAT_ANAHTAR or dictionary.lookup_exact(wl) or dictionary.lookup_with_suffix(wl)[0]:
            continue
        if _yeni_bicim(w):
            continue
        out.append(w)
        if len(out) >= en_fazla:
            break
    return out


yukle()
