"""Hayrat Risale-i Nur külliyatı: Osmanlıca + Latin, paragraf paragraf (risale.online/risale-api).
Konteynerde arka planda: python3 /tmp/hayrat_indir.py      (yarıda kalırsa tekrar çalıştırınca devam eder)
Çıktı (/data/hayrat): ham/<slug>/<yazi>_<ilk>-<son>.json, kelime_ciftleri.tsv, paragraflar.jsonl, eserler.json
Yalnız kişisel kalite kontrolü için; istekler arasında beklenir."""
import collections, json, os, re, sys, time
import requests
from bs4 import BeautifulSoup

API = "https://risale.online/risale-api"
KOK = "/data/hayrat"
PARCA = 25          # bir istekte sayfa sayısı
BEKLE = 1.0         # istekler arası saniye
S = requests.Session()
S.headers["User-Agent"] = "Mozilla/5.0 (dedplay kalite kontrol)"


def al(url, deneme=5):
    for i in range(deneme):
        try:
            r = S.get(url, timeout=180)
            if r.status_code == 200:
                return r.json()
            print(f"   {r.status_code} {url}", flush=True)
        except Exception as e:
            print(f"   hata {type(e).__name__} {url}", flush=True)
        time.sleep(BEKLE * (2 ** i) * 3)
    raise RuntimeError("indirilemedi: " + url)


def parca_indir(e, klasor, yazi, ilk, son):
    """Bir sayfa aralığını indirir; sunucu yetişemezse (zaman aşımı) aralığı 5'er sayfalık parçalara böler."""
    yol = f"{klasor}/{yazi}_{ilk:04d}-{son:04d}.json"
    if os.path.exists(yol):
        return
    kucukler = [(a, min(a + 4, son)) for a in range(ilk, son + 1, 5)]
    bolunmus = son - ilk >= 5 and any(os.path.exists(f"{klasor}/{yazi}_{a:04d}-{b:04d}.json") for a, b in kucukler)
    if not bolunmus:
        try:
            d = al(f"{API}/paragraf?eserid={e['id']}&ilksayfa={ilk}&sonsayfa={son}&yazi={yazi}", deneme=2 if son - ilk >= 5 else 6)
            json.dump(d, open(yol + ".tmp", "w", encoding="utf-8"), ensure_ascii=False)
            os.replace(yol + ".tmp", yol)
            time.sleep(BEKLE)
            return
        except RuntimeError:
            if son - ilk < 5:
                raise
            print(f"   {e['slug']} {yazi} {ilk}-{son}: 5'er sayfalık parçalara bölünüyor", flush=True)
    for a, b in kucukler:
        parca_indir(e, klasor, yazi, a, b)


def indir():
    eserler = veri(al(f"{API}/eserler"))
    os.makedirs(KOK, exist_ok=True)
    json.dump(eserler, open(f"{KOK}/eserler.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    toplam = sum(e["sayfa_sayisi"] for e in eserler if e.get("metin_var_mi"))
    print(f"{len(eserler)} eser, {toplam} sayfa", flush=True)
    for e in sorted(eserler, key=lambda x: x.get("sira") or 0):
        if not e.get("metin_var_mi"):
            continue
        klasor = f"{KOK}/ham/{e['slug']}"
        os.makedirs(klasor, exist_ok=True)
        for ilk in range(1, e["sayfa_sayisi"] + 1, PARCA):
            son = min(ilk + PARCA - 1, e["sayfa_sayisi"])
            for yazi in ("osmanlica", "latince"):
                parca_indir(e, klasor, yazi, ilk, son)
        print(f"  tamam: {e['latince']} ({e['sayfa_sayisi']} sayfa)", flush=True)


def veri(d):
    return (d.get("data") or []) if isinstance(d, dict) else (d or [])


def duz(t):
    return re.sub(r"\s+", " ", t or "").strip()


def isle():
    eserler = {e["id"]: e for e in json.load(open(f"{KOK}/eserler.json", encoding="utf-8"))}
    ciftler = collections.Counter()
    paragraf_say = 0
    with open(f"{KOK}/paragraflar.jsonl", "w", encoding="utf-8") as out:
        for slug in sorted(os.listdir(f"{KOK}/ham")):
            dosyalar = sorted(os.listdir(f"{KOK}/ham/{slug}"))
            lat = {}  # paragraf kimliğine göre (Latin ve Osmanlıca aralıkları farklı bölünmüş olabilir)
            for f in dosyalar:
                if f.startswith("latince_") and f.endswith(".json"):
                    for p in veri(json.load(open(f"{KOK}/ham/{slug}/{f}", encoding="utf-8"))):
                        lat[p["id"]] = p
            gorulen = set()
            for f in (x for x in dosyalar if x.startswith("osmanlica_") and x.endswith(".json")):
                osm = [p for p in veri(json.load(open(f"{KOK}/ham/{slug}/{f}", encoding="utf-8"))) if p["id"] not in gorulen]
                gorulen.update(p["id"] for p in osm)
                for p in osm:
                    soup = BeautifulSoup(p.get("osmanlica_html") or "", "html.parser")
                    for sp in soup.select("span.kelime-grup[data-latince]"):
                        ciftler[(duz(sp["data-latince"]), duz(sp.get_text()))] += 1
                    lat_html = (lat.get(p["id"]) or {}).get("latince_html") or ""
                    out.write(json.dumps({"eser": slug, "sayfa": p.get("sayfa"), "id": p["id"],
                                          "latince": duz(BeautifulSoup(lat_html, "html.parser").get_text(" ")),
                                          "osmanlica": duz(soup.get_text(" "))}, ensure_ascii=False) + "\n")
                    paragraf_say += 1
    with open(f"{KOK}/kelime_ciftleri.tsv", "w", encoding="utf-8") as f:
        for (l, o), n in sorted(ciftler.items(), key=lambda x: -x[1]):
            f.write(f"{l}\t{o}\t{n}\n")
    print(f"paragraf: {paragraf_say} | farklı kelime çifti: {len(ciftler)} | toplam kelime: {sum(ciftler.values())}", flush=True)


if __name__ == "__main__":
    if "isle" not in sys.argv:
        indir()
    isle()
