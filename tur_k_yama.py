# Tur K yama betigi (osmanlica-cevirici; Tur J + J2'nin ustune). Depo kokunde calistirilir. Tekrar calistirilabilir.
import sys

def oku(y):
    return open(y, encoding="utf-8").read()

def yaz(y, s):
    open(y, "w", encoding="utf-8").write(s)

def satir_ekle(yol, satirlar):
    s = oku(yol)
    mevcut = s.splitlines()
    eklenen = 0
    for l in satirlar:
        if l in mevcut:
            continue
        if not s.endswith("\n"):
            s += "\n"
        s += l + "\n"
        eklenen += 1
    yaz(yol, s)
    print("TAMAM:" if eklenen else "ATLANDI:", yol, eklenen, "satir")

T = "app/engine/transliterator.py"
Z = "\u200c"

# 1) -le fiilleri (Hayrat söylemiş سویلهمش، söyledik سویلهدك): belirle-, destekle- kok sozlugune
satir_ekle("app/data/kok_elle.tsv", ["belirle\tبلیرله\tV\t1", "belirlen\tبلیرله" + Z + "ن\tV\t1", "destekle\tدستكله\tV\t1"])
# 2) iplik (Hayrat ایپلك): ipliği ip+lik sanilmasin
satir_ekle("app/data/duzeltmeler.tsv", ["iplik\tایپلك\ttr", "ipliği\tایپلكی\ttr", "ipliğinden\tایپلكندن\ttr"])

# 3) Kelime sonu: Tur K kurallari (Hayrat yazimi), _tur_j'den sonra
s = oku(T)
if "def _tur_k(" in s:
    print("ATLANDI:", T, "_tur_k")
else:
    eski = "    return WORD_RE.sub(lambda m: _tur_j(_he_ki(kelime(m), m.group(0)), m.group(0)), sentence)\n"
    if s.count(eski) != 1:
        print("HATA:", T, "WORD_RE satiri bulunamadi (Tur J uygulanmis olmali)")
        sys.exit(1)
    s = s.replace(eski, "    return WORD_RE.sub(lambda m: _tur_k(_tur_j(_he_ki(kelime(m), m.group(0)), m.group(0)), m.group(0)), sentence)\n")
    anahtar = "def _tj_fiil(r: str) -> bool:\n"
    if s.count(anahtar) != 1:
        print("HATA:", T, "_tj_fiil bulunamadi")
        sys.exit(1)
    s = s.replace(anahtar, '''def _tur_k(o: str, latin: str) -> str:
    """Tur K (18 Ekim, Bakara denetimi 3): kural motorunun yazdigi kelimede Hayrat ek yazimi. Hayrat'taki ve sozlukte tam kaydi olan
    kelimeye dokunulmaz. OSM_TUR_J=0 ile birlikte kapanir."""
    if not _TUR_J_ACIK or not o or " " in o:
        return o
    wl = turkish_lower(latin).replace("\\u2019", "'")
    if "'" in wl or wl in dictionary.HAYRAT_ANAHTAR or dictionary.lookup_exact(wl):
        return o
    # a) -dIklAr- دقلر/دكلر (Hayrat olduklarını اولدقلرینی، bulunduklarını): harcadıklarının خرجادقلرینڭ
    if re.search(r"[dt][\\u0131u]klar", wl):
        o = o.replace("\\u062f\\u06cc\\u0642\\u0644\\u0631", "\\u062f\\u0642\\u0644\\u0631", 1)
    if re.search(r"[dt][i\\u00fc]kler", wl):
        o = o.replace("\\u062f\\u06cc\\u0643\\u0644\\u0631", "\\u062f\\u0643\\u0644\\u0631", 1)
    # b) -dIğIm- دیغم/دیكم (Hayrat olduğumuz اولدیغمز، geldiğime كلدیگمه): indirdiğime ایندیردیكمه
    if re.search(r"[dt][\\u0131iu\\u00fc]\\u011f[\\u0131iu\\u00fc]m", wl):
        o = re.sub("([\\u063a\\u0643\\u06af])\\u06cc\\u0645", r"\\1" + "\\u0645", o, count=1)
    # c) unsuzden sonra iyelik -umuz/-ümüz مز (Hayrat yolumuz یولمز، rûhumuza روحمزه، suçumuz صوچمز): kulumuza قولمزه
    if re.search(r"[^aeıioöuüâîû][u\\u00fc]m[u\\u00fc]z", wl):
        o = o.replace("\\u0648\\u0645\\u0648\\u0632", "\\u0645\\u0632", 1)
    # d) ğ/t ile biten kok + iyelik + ilgi -InIn: نڭ (Hayrat -ğının 96, -tının 91 yuzde: hastalığının خستهلغنڭ، hayatının حیاتنڭ)
    if re.search(r"[\\u011ft][\\u0131iu\\u00fc]n[\\u0131iu\\u00fc]n$", wl) and \\
            re.search("[^\\u0647\\u0648\\u0627\\u06cc\\u200c]\\u06cc\\u0646\\u06ad$", o):
        o = o[:-3] + "\\u0646\\u06ad"
    return o


''' + anahtar)
    yaz(T, s)
    print("TAMAM:", T, "_tur_k")
# 4) test_tur_e: belirlediğinizin artik -le fiili kuralıyla (Hayrat söyledik سویلهدك): بلیرلهدیكڭزڭ
s = oku("tests/test_tur_e.py")
eski = '("belirlediğinizin", "\u0628\u0644\u06cc\u0631\u0644\u062f\u06cc\u0643\u06ad\u0632\u06ad")'
yeni = '("belirlediğinizin", "\u0628\u0644\u06cc\u0631\u0644\u0647' + Z + '\u062f\u06cc\u0643\u06ad\u0632\u06ad")'
if yeni in s:
    print("ATLANDI: tests/test_tur_e.py")
elif s.count(eski) == 1:
    yaz("tests/test_tur_e.py", s.replace(eski, yeni))
    print("TAMAM: tests/test_tur_e.py")
else:
    print("HATA: tests/test_tur_e.py belirlediğinizin satiri bulunamadi")
    sys.exit(1)
# 5) yeni test: tests/test_tur_k.py
_test = '"""Tur K (18 Ekim, Bakara denetimi 3): -le fiilleri (belirle-, destekle-), -dIklAr-, -dIğIm-, -umuz, ğ/t + -InIn, iplik.\n"korunan"lar (gözünün, elçinin, yerinin, kitaplarının: Hayrat ینڭ) bozulmamalı. Birebir (ZWNJ dahil) karşılaştırılır.\nÇalıştırma: docker run --rm -v "$PWD":/k -w /k berzahbey/osmanlica-cevirici:latest python tests/test_tur_k.py"""\nimport logging\nimport os\nimport sys\n\nlogging.disable(50)\nsys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app"))\nfrom engine.transliterator import transliterate_text as T  # noqa: E402\n\nDURUMLAR = [\n    (\'belirlemi\\u015f\', \'\\u0628\\u0644\\u06cc\\u0631\\u0644\\u0647\\u200c\\u0645\\u0634\'),\n    (\'belirlenmi\\u015f\', \'\\u0628\\u0644\\u06cc\\u0631\\u0644\\u0647\\u200c\\u0646\\u0645\\u0634\'),\n    (\'belirlemeden\', \'\\u0628\\u0644\\u06cc\\u0631\\u0644\\u0647\\u200c\\u0645\\u0647\\u200c\\u062f\\u0646\'),\n    (\'belirledi\\u011finizin\', \'\\u0628\\u0644\\u06cc\\u0631\\u0644\\u0647\\u200c\\u062f\\u06cc\\u0643\\u06ad\\u0632\\u06ad\'),\n    (\'destekledik\', \'\\u062f\\u0633\\u062a\\u0643\\u0644\\u0647\\u200c\\u062f\\u0643\'),\n    (\'harcad\\u0131klar\\u0131n\\u0131n\', \'\\u062e\\u0631\\u062c\\u0627\\u062f\\u0642\\u0644\\u0631\\u06cc\\u0646\\u06ad\'),\n    (\'indirdi\\u011fime\', \'\\u0627\\u06cc\\u0646\\u062f\\u06cc\\u0631\\u062f\\u06cc\\u0643\\u0645\\u0647\'),\n    (\'kulumuza\', \'\\u0642\\u0648\\u0644\\u0645\\u0632\\u0647\'),\n    (\'krall\\u0131\\u011f\\u0131n\\u0131n\', \'\\u0642\\u0631\\u0627\\u0644\\u0644\\u063a\\u0646\\u06ad\'),\n    (\'kal\\u0131nt\\u0131n\\u0131n\', \'\\u0642\\u0627\\u0644\\u06cc\\u0646\\u062a\\u0646\\u06ad\'),\n    (\'ipli\\u011fi\', \'\\u0627\\u06cc\\u067e\\u0644\\u0643\\u06cc\'),\n    (\'ipli\\u011finden\', \'\\u0627\\u06cc\\u067e\\u0644\\u0643\\u0646\\u062f\\u0646\'),\n    (\'\\xe7a\\u011f\\u0131rd\\u0131\\u011f\\u0131mda\', \'\\u0686\\u0627\\u063a\\u06cc\\u0631\\u062f\\u06cc\\u063a\\u0645\\u062f\\u0647\'),\n    (\'at\\u0131ld\\u0131klar\\u0131nda\', \'\\u0622\\u062a\\u06cc\\u0644\\u062f\\u0642\\u0644\\u0631\\u0646\\u062f\\u0647\'),\n    (\'oldu\\u011fumuz\', \'\\u0627\\u0648\\u0644\\u062f\\u06cc\\u063a\\u0645\\u0632\'),\n    (\'kitaplar\\u0131n\\u0131n\', \'\\u0643\\u062a\\u0627\\u0628\\u0644\\u0631\\u06cc\\u0646\\u06ad\'),\n    (\'g\\xf6z\\xfcn\\xfcn\', \'\\u0643\\u0648\\u0632\\u06cc\\u0646\\u06ad\'),\n    (\'el\\xe7inin\', \'\\u0627\\u06cc\\u0644\\u0686\\u06cc\\u0646\\u06ad\'),\n    (\'yerinin\', \'\\u06cc\\u0631\\u06cc\\u0646\\u06ad\'),\n    (\'ad\\u0131n\\u0131n\', \'\\u0622\\u062f\\u06cc\\u0646\\u06ad\'),\n    (\'peygamberinin\', \'\\u067e\\u06cc\\u063a\\u0645\\u0628\\u0631\\u06cc\\u0646\\u06ad\'),\n    (\'hayat\\u0131n\\u0131n\', \'\\u062d\\u06cc\\u0627\\u062a\\u0646\\u06ad\'),\n    (\'s\\xf6ylemi\\u015f\', \'\\u0633\\u0648\\u06cc\\u0644\\u0647\\u200c\\u0645\\u0634\'),\n    (\'temizleyin\', \'\\u062a\\u0645\\u06cc\\u0632\\u0644\\u0647\\u200c\\u06cc\\u06ad\'),\n]\n\n\ndef main():\n    kalan = 0\n    for w, beklenen in DURUMLAR:\n        c = T(w).strip()\n        if c != beklenen:\n            kalan += 1\n            print(f"KALDI {w} -> {c} (beklenen {beklenen})")\n    print("SONUC: HEPSI GECTI" if not kalan else f"SONUC: {kalan} TEST KALDI")\n\n\nif __name__ == "__main__":\n    main()\n'
try:
    _eski = oku("tests/test_tur_k.py")
except FileNotFoundError:
    _eski = None
if _eski == _test:
    print("ATLANDI: tests/test_tur_k.py")
else:
    yaz("tests/test_tur_k.py", _test)
    print("TAMAM: tests/test_tur_k.py")
print("BITTI")
