"""Tur ÇY (25 Kasım 2026, Zahir kararı): Hayrat'ın AYNI kelimeyi iki türlü yazdığı ve ikiliğin bir kurala dayanmadığı yerde kurala
uyan yazım. Ölçüm Hayrat'ın kelime kelime Latin/Osmanlıca eşlemesiyle (22 eser): Hayrat kelime düzeyinde çok tutarlı; iki türlü yazılan
kelimelerin çoğu kurala dayanır ve DOKUNULMAZ: senin/onun ڭ/ن (başına باشڭه/باشنه), anlam farkı (yedi یدی / ye-di ییدی, arz ارض/عرض,
başlar باشلار/باشلر), tekrar (ayrı ayrı), dua işareti.
Kurala dayanmayan ikilikler:
  - -iyye/-iyyet nisbe şeddesi (aynı kök hem şeddeli hem şeddesiz: mâhiyet ماهیّت 335 / ماهیت 209, İlâhiye): Arapça aslında nisbe yâsı
    şeddeli (Zahir'in şedde kuralı) -> şeddeli. Yalnız Hayrat'ın gerçekten iki türlü yazdığı kökler (azınlık %15+) (data/iyye_sedde.tsv); Hayrat'ın hep şeddesiz
    yazdığı (ehemmiyet) ve aslında şeddesi olmayan (terbiye, tavsiye, ma'siyet, âliye) dokunulmaz.
  - Arapça aslına göre: kezâlik كذلك (Hayrat كذالك 60 / كذلك 34), takvâ تقوی (تقوا 54 / تقوی 10).
  - Hemzeli Arapça kelimeler aslına göre (Zahir, 25 Kasım: "Arapça aslı yazılsın"): neş'et نشأت (Hayrat نشئت 185 / نشأت 24; aslı نشأة),
    menşe' منشأ، menşei منشأی (Hayrat منشئی 29 / منشأی 16; çevirici منشای yazıyordu), mebde' مبدأ gibi.
  - numara نومره (Hayrat نومره 6 / نومرو 4): Batı kelimesi okunuşa göre, son a ه.
OSM_BIRLIK=0 ile kapatılır."""
import os
import re
from pathlib import Path

ACIK = os.environ.get("OSM_BIRLIK", "1") != "0"
SEDDE = "ّ"
TAM = {"\u0643\u0630\u0627\u0644\u0643": "\u0643\u0630\u0644\u0643",          # kezâlik: كذالك -> كذلك
       "\u062a\u0642\u0648\u0627": "\u062a\u0642\u0648\u06cc",                    # takvâ: تقوا -> تقوی
       "\u0645\u0646\u0634\u0627\u06cc": "\u0645\u0646\u0634\u0623\u06cc",        # menşei: منشای -> منشأی
       "\u0645\u0646\u0634\u0627": "\u0645\u0646\u0634\u0623"}                    # menşe': منشا -> منشأ
_TAM_LATIN = {"\u0645\u0646\u0634\u0627\u06cc": re.compile(r"^men[şs]e['’]?[iî]$"), "\u0645\u0646\u0634\u0627": re.compile(r"^men[şs]e['’]?$")}
# hemzenin aslî kürsüsü (Arapça aslı): Latin başı -> (çevirici yazımı başı, aslı)
_HEMZE_ASLI = [(re.compile(r"^ne[şs]['’]?et"), "\u0646\u0634\u0626\u062a", "\u0646\u0634\u0623\u062a"),      # neş'et: نشئت -> نشأت
               (re.compile(r"^men[şs]e['’]?"), "\u0645\u0646\u0634\u0626", "\u0645\u0646\u0634\u0623")]        # menşe': منشئ -> منشأ
_NUMARO = "نومرو"                                      # نومرو
KOKLER = set()
_yol = Path(__file__).parent.parent / "data" / "iyye_sedde.tsv"
if _yol.exists():
    KOKLER = {s.strip() for s in open(_yol, encoding="utf-8") if s.strip() and not s.startswith("#")}
_IYYE = re.compile(r"^(.+?)(iyye|iye|iyyet|iyet)(.*)$")
_NISBE_YA = re.compile("ی(?=[هەت])")


def _sade(lat):
    l = lat.replace("I", "ı").replace("İ", "i").lower()
    l = re.sub(r"['’‘ʻ]", "", l)
    return l.translate(str.maketrans("âîûāīū", "aiuaiu"))


def duzelt(lat, osm):
    """Tek kelime (lat boş olabilir: eşlenemeyen kelime; o zaman yalnız Latin gerektirmeyen düzeltmeler)."""
    if not ACIK or not osm:
        return osm
    o = osm
    if o in TAM and (o not in _TAM_LATIN or (lat and _TAM_LATIN[o].match(lat.replace("I", "ı").replace("İ", "i").lower()))):
        o = TAM[o]
    if lat:
        lk = lat.replace("I", "ı").replace("İ", "i").lower()
        for r, eski, yeni in _HEMZE_ASLI:
            if r.match(lk) and o.startswith(eski):
                o = yeni + o[len(eski):]
        l = _sade(lat)
        m = _IYYE.match(l)
        if m and m.group(1) in KOKLER and SEDDE not in o:
            yerler = [x.start() for x in _NISBE_YA.finditer(o)]
            if yerler:
                o = o[:yerler[-1] + 1] + SEDDE + o[yerler[-1] + 1:]
        if l.startswith("numara") and o.startswith(_NUMARO):                   # numara نومرو -> نومره
            o = _NUMARO[:-1] + "ه" + ("‌" if len(o) > 5 else "") + o[5:]
    return o
