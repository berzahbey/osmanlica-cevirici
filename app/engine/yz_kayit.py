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
ADLAR = {}          # Tur KE3: yapay zekânın verdiği özel ad yazılışları (büyük harfli kelime için sözlükten önce: Halime حلیمه)
TR_KOK = set()      # Tur KE: Türkçe (ve Batı dili) kayıtların kökleri: aynı kökün yeni ekli hâli yeniden sorulmaz
_kilit = threading.Lock()

# Latin ünsüz -> Osmanlıcada karşılığı olabilecek harfler (harf uyumu denetimi için)
_UNSUZ = {"b": "بپ", "c": "جچ", "ç": "چج", "d": "دذضط", "f": "ف", "g": "غگكق", "ğ": "غگك", "h": "حهخ", "j": "ژج", "k": "كقخ",
          "l": "ل", "m": "م", "n": "نڭ", "p": "پب", "r": "ر", "s": "سصث", "ş": "ش", "t": "تطثدض", "v": "و", "y": "ی", "z": "زذضظ"}
_HARF_DISI = set("اوىیهعءأإآؤئةًٌٍَُِّْٰ‌")     # ünlü harfleri, ayın, hemze, harekeler: karşılaştırmada atlanır


def _unsuzler_latin(w, tekle=True):
    s = turkish_lower(w)
    s = re.sub(r"[^a-zçğıöşü]", "", s.translate(str.maketrans("âîû", "aiu")))
    out = [c for c in s if c in _UNSUZ]
    if not tekle:
        return out
    return [c for i, c in enumerate(out) if i == 0 or c != out[i - 1] or c in "y"]       # çift ünsüz (şedde) tek sayılır


def harf_uyumu(latin: str, osm: str) -> bool:
    """Arap harfli yazılışın ünsüzleri Latin yazımın ünsüzleriyle sırayla uyuşuyor mu (mahmuz ~ مهمیز: m-h-m-z).
    ا و ی ه ع ء ünlü harfi ya da fazladan harf olarak atlanabilir; atlanmazsa ünsüz (v, y, h) karşılığı sayılır."""
    if not osm or not re.fullmatch(r"[\u0600-\u06ff\u200c ]+", osm):
        return False
    a = [c for c in osm.replace(" ", "").replace("\u200c", "") if c not in "ًٌٍَُِّْٰ"]
    a = [c for i, c in enumerate(a) if i == 0 or c != a[i - 1]]
    tek, cift = _unsuzler_latin(latin), _unsuzler_latin(latin, tekle=False)
    if tek != cift and harf_uyumu_lat(cift, a):          # Tur YZ4: tamam تمام (iki ayrı mim), şedde değil
        return True
    return harf_uyumu_lat(tek, a)


def harf_uyumu_lat(lat, a):
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


def yeniden_sorulur(r) -> bool:
    """Tur YZ4 (13 Kasım 2026): güçlü modellerin ücretsiz günlük sınırı küçük (ilk gün ~700 kelime). Lite'ın 22 bin kaydının hepsi
    yeniden sorulmaz: yalnız Arapça/Farsça dediği (ya da denetimden geçmeyen) kelimeler. Lite'ın 'tr' kaydı zararsızdır (Türkçe
    kurallar yazar), Batı dili kaydı da Tur YZ2 süzgeciyle uygulanır."""
    if guvenilir(r.get("model")):
        return _bati_adi_eksik(r)          # Tur KE4: yazılışı olmayan Batı özel adı bir kez daha sorulur
    return r.get("koken") in ("ar", "fa") or r.get("durum") == "kontrol"


def _bati_adi_eksik(r) -> bool:
    """Tur KE4: büyük harfli Batı dili özel adının kaydında Osmanlıca yazılış yok (eski istem yalnız okunuş istiyordu)."""
    w = r.get("kelime") or ""
    return w[:1].isupper() and r.get("koken") not in ("tr", "ar", "fa", "") and not (r.get("yazilis") or "").strip()


def _ar_fa_uygula(r):
    """Güvenilir modelin onaylı Arapça/Farsça kaydı: kök, aslî yazılışıyla sözlüğe eklenir (sözlükte varsa dokunulmaz;
    ekleri çevirici yazar: kahramanları -> قهرمانلری)."""
    kok = turkish_lower(r.get("kok") or "")
    osm = (r.get("yazilis") or "").translate(_OSM_HARF)
    if len(kok) < 3 or not osm or dictionary._get(kok):
        return
    dictionary.DICTIONARY[kok] = (osm, r["koken"])
    duz = dictionary._flat(kok)
    if duz != kok and duz not in dictionary.DICTIONARY:
        dictionary.DICTIONARY[duz] = (osm, r["koken"])


def _kok_ekle(r):
    """Tur KE (13 Kasım 2026): Türkçe ya da Batı dili kaydının kökü bilinen sayılır (yorumla: yorumladığı, yorumlamaktan sorulmaz).
    Yalnız güvenilir modelin kaydı; kök kelimenin başında olmalı (Latince kök 'applicatio' alınmaz) ve en az 4 harf. Arapça/Farsça kökler zaten sözlüğe girer."""
    if r.get("koken") in ("ar", "fa", "") or not guvenilir(r.get("model")):
        return                           # Lite'ın köken etiketi güvenilmez (Arapça kelimeye de tr diyor): yalnız güçlü modelin kökü
    kok, w = turkish_lower(r.get("kok") or ""), turkish_lower(r.get("kelime") or "")
    if len(kok) >= 4 and w.startswith(kok) and re.fullmatch(r"[a-zçğıöşüâîû]+", kok):
        TR_KOK.add(kok)


_SERT = {"ğ": "k", "b": "p", "c": "ç", "d": "t"}


def bilinen_kok(wl: str) -> bool:
    """Kelime, kaydı olan bir Türkçe kökle + geçerli bir ekle mi başlıyor (yumuşama dahil: yorumla+dığı, çocuğ+u -> çocuk)."""
    if not TR_KOK:
        return False
    from . import kok as _kok
    for L in range(len(wl) - 1, 3, -1):
        r, kalan = wl[:L], wl[L:]
        if r not in TR_KOK and not (r[-1] in _SERT and r[:-1] + _SERT[r[-1]] in TR_KOK):
            continue
        if _kok._ek_gecerli(r, kalan, "N") or _kok._ek_gecerli(r, kalan, "V"):
            return True
    return False


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
    _kok_ekle(r)
    w = r.get("kelime") or ""
    if k in ("ar", "fa") and guvenilir(r.get("model")) and w[:1].isupper() and r.get("yazilis") \
            and turkish_lower(r.get("kok") or "") == turkish_lower(w):
        ADLAR[turkish_lower(w)] = r["yazilis"].translate(_OSM_HARF).strip()
    elif k not in ("tr", "ar", "fa", "") and guvenilir(r.get("model")) and w[:1].isupper() and r.get("yazilis") \
            and turkish_lower(r.get("kok") or w) == turkish_lower(w):
        y = r["yazilis"].translate(_OSM_HARF).strip()
        if harf_uyumu(r.get("okunus") or w, y):
            ADLAR[turkish_lower(w)] = y      # Tur KE4: Batı özel adı (Schopenhauer شوپنهاور), okunuşla harf uyumu denetlenir
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
    TR_KOK.clear()
    ADLAR.clear()
    for yol in (PAKET, KALICI):
        _oku(yol)
    for k, r in list(KAYIT.items()):
        if guvenilir(r.get("model")) and r.get("koken") in ("ar", "fa"):
            KAYIT[k] = denetle(r)        # Tur YZ4: eski kayıtlar da Osmanlıca harfle yeniden denetlenir (تاريخ -> تاریخ)
    for r in KAYIT.values():
        _uygula(r)
    _onbellek_sil()


_OSM_HARF = str.maketrans({"\u064a": "\u06cc", "\u0649": "\u06cc", "\u06a9": "\u0643", "\u0629": "\u0647", "\u0623": "\u0627",
                           "\u0625": "\u0627"})   # Tur YZ4: Arapça imla -> Osmanlıca (تاريخ -> تاریخ، صناعة -> صناعه، إعمال -> اعمال)


def denetle(r):
    """Yapay zekâ cevabını düzene sokar ve denetler; durum alanını 'onayli' ya da 'kontrol' yapar."""
    r = {a: str(r.get(a) or "").strip().replace("\t", " ").replace("\n", " ") for a in ALANLAR}
    r["yazilis"] = r["yazilis"].translate(_OSM_HARF)
    r["koken"] = r["koken"].lower()[:5]
    w = turkish_lower(r["kelime"])
    if r["koken"] in ("ar", "fa"):
        kok = turkish_lower(r["kok"] or r["kelime"])
        sade = lambda x: x.translate(str.maketrans("âîû", "aiu"))
        parcalar = [sade(x) for x in w.split("-") if x]                  # orta-sınıfların, tarih-yazımının: herhangi bir parça
        ks = sade(kok)
        dusen = re.sub(r"[aeıioöuü](?=[^aeıioöuü]$)", "", ks)           # ünlü düşmesi: seyir -> seyr(ederken), atıf -> atf(etmek)
        if not any(ws.startswith(k[:max(3, len(k) - 1)]) for k in (ks, dusen) for ws in parcalar):     # kök kelimenin başında olmalı (mahmuz+uyla)
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
                if not r["kelime"] or eski and (not yeniden_sorulur(eski) or not guvenilir(r["model"])):
                    continue                     # Tur YZ3: Lite kaydının yerine güçlü modelin cevabı yazılır (son satır geçerli)
                f.write("\t".join(r[a] for a in ALANLAR) + "\n")
                KAYIT[r["kelime"].lower()] = r
                _uygula(r)
                on += r["durum"] == "onayli"
                ko += r["durum"] == "kontrol"
        _onbellek_sil()
    return on, ko


_KELIME = re.compile(r"[A-Za-zÇĞİÖŞÜçğıöşüÂÎÛâîû][A-Za-zÇĞİÖŞÜçğıöşüÂÎÛâîû\-]*")


def _bilinmeyen_mi(w: str) -> bool:
    """Kelime hiçbir sözlükte / kayıtta yok ve henüz (güvenilir modele) sorulmamış mı."""
    from .onisle import _yeni_bicim
    wl = turkish_lower(w)
    kayit = KAYIT.get(wl) or KAYIT.get(w.lower())
    if kayit and not yeniden_sorulur(kayit) or w.lower() in yabanci._TABLO or yabanci._roma(w):
        return False
    if not kayit and bilinen_kok(wl):
        return False                     # Tur KE: Türkçe kökü daha önce sorulmuş (yorumladığı -> yorumla)
    if wl in dictionary.HAYRAT_ANAHTAR or dictionary.lookup_exact(wl) or dictionary.lookup_with_suffix(wl)[0]:
        return False
    return not _yeni_bicim(w)


_UNLU = set("aeıioöuüâîû")
_ISIM_TUREV = ("sızlık", "sizlik", "suzluk", "süzlük", "lık", "lik", "luk", "lük", "sız", "siz", "suz", "süz", "lı", "li", "lu", "lü",
               "cı", "ci", "cu", "cü", "çı", "çi", "çu", "çü", "ca", "ce", "ça", "çe", "cık", "cik", "çık", "çik")
_TUREV_EKI = ("landır", "lendir", "laştır", "leştir", "lan", "len", "laş", "leş", "lat", "let", "la", "le")


def _kok_biliniyor(r: str) -> bool:
    from . import kok as _kok
    k = KAYIT.get(r)
    return bool(dictionary._get_soft(r) or r in _kok.KOK or r in TR_KOK or (k and not yeniden_sorulur(k)))


def _soru_ogesi(w: str):
    """Tur KE3 (13 Kasım 2026): yapay zekâya kelime değil KÖK sorulur (Alamut: 9.840 bilinmeyen kelime 2.574 kökten).
    Dönen (grup, öğe) ya da None (sorulmaz):
      - Zemberek kökü bulunur; kök biliniyorsa (sözlük, Hayrat kökü, kayıt) sorulmaz: yazımı belli, ekleri kurallar yazar.
      - Türkçe fiil çekimi (kıvrıl-, kızar-, belir-) sorulmaz; isimden türemiş fiilde (sakinleş-, kırbaçla-) isim kökü sorulur.
      - Bilinmeyen kök sorulur (grup 2); Zemberek'in tanımadığı kelime (özel ad, yabancı kelime) olduğu gibi sorulur (grup 1)."""
    from . import kok as _kok
    from . import rules
    wl = turkish_lower(w)
    z = _kok.ZKOK

    def zk(x):
        """Zemberek kökü (yumuşama: eşiğ -> eşik; ünlü düşmesi: kayb -> kayıp, ağz -> ağız) ya da None."""
        if x in z:
            return x
        if len(x) >= 3 and x[-1] in _SERT and x[:-1] + _SERT[x[-1]] in z:
            return x[:-1] + _SERT[x[-1]]
        if len(x) >= 3 and x[-1] not in _UNLU and x[-2] not in _UNLU:
            for v in "ıiuü":
                if x[:-1] + v + x[-1] in z:
                    return x[:-1] + v + x[-1]
        return None
    f = rules._fiil_ayir(wl)
    if f and zk(f[0]) and not any(f[0].endswith(e) for e in _TUREV_EKI):
        return None                      # Türkçe fiil çekimi (eğ+iyorsunuz, ol+mayabilirim): kurallar yazar
    r = zk(wl) or next((zk(wl[:L]) for L in range(len(wl) - 1, 2, -1) if zk(wl[:L])
                        and (_kok._ek_gecerli(wl[:L], wl[L:], "N") or _kok._ek_gecerli(wl[:L], wl[L:], "V"))), None)
    if not r:
        return 1, w
    while True:                          # türemiş kök tabanına iner: yastıkla -> yastık, belirsiz -> belir, kolla -> kol
        e = next((e for e in _TUREV_EKI + _ISIM_TUREV if r.endswith(e) and len(r) - len(e) >= 3 and zk(r[:-len(e)])), None)
        if not e:
            break
        r = zk(r[:-len(e)])
    if f and len(f[0]) >= len(r) - 1:
        ek = next((e for e in _TUREV_EKI if r.endswith(e) and len(r) - len(e) >= 3), None)
        if not ek:
            return None                  # Türkçe fiil (kök + çekim): kurallar yazar, yapay zekâya gerek yok
        r = r[:-len(ek)]                 # isim + -la/-leş fiili: isim kökü sorulur (sakinleş -> sakin)
    if _kok_biliniyor(r):
        return None
    return 2, r


def _ekli_bicim(wl: str) -> bool:
    """Sözlükteki kelime aynı zamanda sözlükteki bir kökün ekli hâli mi (halime = hâl+im+e حالمه، adi = ad+i): büyük harfle geçtiğinde
    özel ad olabilir (Halime حلیمه، Adî عدی), sözlük kaydına güvenilmez."""
    return any(wl.endswith(e) and len(wl) - len(e) >= 3 and dictionary._get(wl[:-len(e)])
               for e in ("e", "a", "i", "ı", "u", "ü", "ye", "ya", "im", "ım", "in", "ın", "de", "da", "le", "la"))


def bilinmeyenler(metin: str, en_fazla: int = 100000):
    """Yapay zekâya sorulacak öğeler, önem sırasıyla (Tur KE3): önce Zemberek'in tanımadığı kelimeler (özel adlar başta), sonra
    bilinmeyen kökler; her grupta kitapta en sık geçen önce. Kota dolarsa en önemlileri sorulmuş olur."""
    sayi, ilk, kucuk, ortada = {}, {}, set(), set()
    for m in _KELIME.finditer(metin or ""):
        w = m.group(0).strip("-")
        if len(w) < 3:
            continue
        wl = turkish_lower(w)
        sayi[wl] = sayi.get(wl, 0) + 1
        ilk.setdefault(wl, w)
        if w[:1].islower():
            kucuk.add(wl)
        elif not re.search(r"(^|[.!?…:;\n])[\s\"'“”‘’«»(\[\-–—]*$", metin[max(0, m.start() - 12):m.start()]):
            ortada.add(wl)               # cümle ortasında büyük harfle: özel ad adayı
    puan = {}
    for wl, w in ilk.items():
        if w[:1].isupper() and wl not in kucuk and wl in ortada:
            # özel ad (hep büyük harfle geçiyor): yalnız tam eşleşme bilinir sayılır; ek ayırmayla bulunan kök tesadüftür
            # (Halime -> halim + e حلیم، Naim -> nâim)
            k = KAYIT.get(wl) or KAYIT.get(w.lower())
            if not (k and not yeniden_sorulur(k) or (dictionary.lookup_exact(wl) and not _ekli_bicim(wl))
                    or wl in ADLAR or yabanci._roma(w)):
                g, p = puan.get(w, (0, 0))
                puan[w] = (0, p + sayi[wl])
            continue
        if not _bilinmeyen_mi(w):
            continue
        o = _soru_ogesi(w)
        if not o:
            continue
        grup, oge = o
        if grup == 1 and w[:1].isupper() and wl not in kucuk:
            grup = 0                     # hep büyük harfle geçen: özel ad (Halime, Übeyde, Huzistan)
        anahtar = turkish_lower(oge) if grup == 2 else oge
        g, p = puan.get(anahtar, (grup, 0))
        puan[anahtar] = (min(g, grup), p + sayi[wl])
    # Zemberek'in tanımadığı küçük harfli kelimelerin ekli hâlleri birleşir (qorbazları -> qorbazlar): kök bir kez sorulur
    tek = {k for k, (g, _) in puan.items() if g == 1 and k[:1].islower()}
    for k in sorted(tek, key=len, reverse=True):
        kok = next((k[:-len(e)] for e in sorted(dictionary.LOOKUP_SUFFIXES, key=len, reverse=True)
                    if k.endswith(e) and k[:-len(e)] in tek and len(k) - len(e) >= 4), None)
        if kok and k in puan:
            g, p = puan.pop(k)
            g2, p2 = puan[kok]
            puan[kok] = (min(g, g2), p + p2)
    sirali = sorted(puan.items(), key=lambda x: (x[1][0], -x[1][1]))
    return [k for k, _ in sirali[:en_fazla]]


yukle()
