# -*- coding: utf-8 -*-
"""tools/cift_yazim.py: sahte Hayrat verisiyle sınıflandırma. Çalıştırma: python tests/test_cift_yazim.py"""
import os, sys, json, tempfile, collections
from pathlib import Path
KOK = Path(__file__).resolve().parent.parent
tmp = tempfile.mkdtemp()
os.environ["HAYRAT_DIR"] = tmp
os.environ["CIFT_CIKTI"] = os.path.join(tmp, "cikti")
sys.path.insert(0, str(KOK / "tools"))
sys.path.insert(0, str(KOK / "app"))
import importlib
import hayrat_baglam_ogren as HB
HB.H = tmp
import cift_yazim as C


def span(lat, osm):
    return f'<span class="kelime-grup" data-latince="{lat}">{osm}</span>'


def eser(ad, paragraflar):
    d = os.path.join(tmp, "ham", ad)
    os.makedirs(d, exist_ok=True)
    data = [{"id": f"{ad}{i}", "osmanlica_html": " ".join(span(l, o) for l, o in p)} for i, p in enumerate(paragraflar)]
    json.dump({"data": data}, open(os.path.join(d, "osmanlica_1.json"), "w", encoding="utf-8"), ensure_ascii=False)


# A ve B eserleri: et ایت (fiil) çoğunluk, ات (yemek) azınlık; arz ارض ve عرض aynı eserde
pA = [[("tefekkür", "تفكر"), ("et", "ایت")]] * 10 + [[("et", "ات"), ("yedi", "یدی")]] * 4 \
     + [[("arz", "ارض"), ("ve", "و"), ("semâ", "سما")]] * 5 + [[("arz", "عرض"), ("etti", "ایتدی")]] * 4 \
     + [[("kendine", "كندینه")]] * 8 + [[("kendine", "كندیڭه")]] * 4 \
     + [[("türlü", "تورلی")]] * 6 + [[("Saîd", "س * ع")]] * 5
pB = [[("et", "ایط")]] + [[("türlü", "دورلی")]] * 5 + [[("esîr", "اسیر")]] * 6 + [[("esîr", "اثیر")]] * 3 + [[("Saîd", "سعید")]] * 6
eser("a-eseri", pA)
eser("b-eseri", pB)

sonuc = C.cozumle(*C.topla(dict(HB.eserler())))
tur = {w: t for t, w, *_ in sonuc}
beklenen = {"et": "yazim_cesidi", "arz": "anlam_farki", "kendine": "senin_onun", "türlü": "yazim_cesidi", "esîr": "anlam_farki"}
hata = 0
for w, t in beklenen.items():
    if tur.get(w) != t:
        print("HATA:", w, "beklenen", t, "çıkan", tur.get(w)); hata += 1
if "saîd" in tur:
    print("HATA: dua işaretli yazım (س * ع) çift yazım sayıldı"); hata += 1
# eser ayrışması: türlü eserden esere ayrılıyor (1.00, birlikte 0); arz aynı eserde birlikte (birlikte 1)
ay = {w: (a, b) for t, w, n, l, a, b, o in sonuc}
if ay["türlü"] != (1.0, 0):
    print("HATA: türlü eser ayrışması", ay["türlü"]); hata += 1
if ay["arz"][1] != 1:
    print("HATA: arz birlikte geçen eser", ay["arz"]); hata += 1
# dosyalar
say = C.yaz_dosyalar(sonuc, 2)
for f in ("cift_yazim_ozet.txt", "yazim_cesitleri.tsv", "anlam_farki.tsv", "senin_onun.tsv"):
    if not os.path.exists(os.path.join(tmp, "cikti", f)):
        print("HATA: dosya yok", f); hata += 1
af = open(os.path.join(tmp, "cikti", "anlam_farki.tsv"), encoding="utf-8").read()
if "[arz]" not in af:
    print("HATA: anlam_farki.tsv bağlam örneği yok"); hata += 1
# birim: sınıf fonksiyonu
for w, a, b, t in [("neş'et", "نشئت", "نشأت", "yazim_cesidi"), ("takvâ", "تقوا", "تقوی", "yazim_cesidi"),
                   ("salât", "صلات", "صلاة", "yazim_cesidi"), ("hâlî", "خالی", "حالی", "anlam_farki"),
                   ("havâs", "خواص", "حواس", "anlam_farki"), ("kendini", "كندینی", "كندیڭی", "senin_onun")]:
    if C.sinif(w, HB.norm(a), HB.norm(b)) != t:
        print("HATA: sınıf", w, a, b, "beklenen", t, "çıkan", C.sinif(w, HB.norm(a), HB.norm(b))); hata += 1
print("SONUC: HEPSI GECTI" if not hata else f"SONUC: {hata} HATA")
