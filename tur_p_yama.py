# Tur P (18 Ekim): kesmesiz sozluk anahtarlari, alt elif (U+0656) silme, Hayrat ifadesi + ek ZWNJ (hayrat_ifade.tsv 743 kayit),
# Mu'ciz-ul Beyan, ad (isim) -> alif-dal, Sahabeddin, Joseph Schacht. Kod klasorunde: python3 tur_p_yama.py   (tekrar calistirilabilir)
import hashlib, os, re, sys
md5 = lambda s: hashlib.md5(s.encode("utf-8")).hexdigest()
def oku(p): return open(p, encoding="utf-8").read()
def yaz(p, s): open(p, "w", encoding="utf-8").write(s)
for p in ("app/engine/dictionary.py", "app/engine/transliterator.py", "app/data/hayrat.tsv", "app/data/hayrat_ifade.tsv", "app/data/duzeltmeler.tsv"):
    if not os.path.isfile(p): sys.exit("HATA: dosya yok: " + p + " (kod klasorunde misiniz?)")
# --- app/engine/dictionary.py
s = oku("app/engine/dictionary.py")
if md5(s) == "6c4b27e8a7a0d5418fc049620b667ede": print("ATLANDI: app/engine/dictionary.py")
elif md5(s) != "725405b4b3a40206a0838dcf27c5201a": sys.exit("HATA: app/engine/dictionary.py beklenen surum degil (md5 " + md5(s) + ")")
else:
    o, n = "# Osmanl\u0131ca yaz\u0131mda tutarl\u0131l\u0131k: Arap\u00e7a ye (\u064a) yerine Osmanl\u0131ca/Fars\u00e7a ye (\u06cc), Fars\u00e7a kef (\u06a9) yerine kef (\u0643)\nDICTIONARY = {k: (v[0].replace(\"\\u064a\", \"\\u06cc\").replace(\"\\u06a9\", \"\\u0643\"), v[1]) for k, v in DICTIONARY.items()}", "# Osmanl\u0131ca yaz\u0131mda tutarl\u0131l\u0131k: Arap\u00e7a ye (\u064a) yerine Osmanl\u0131ca/Fars\u00e7a ye (\u06cc), Fars\u00e7a kef (\u06a9) yerine kef (\u0643)\nDICTIONARY = {k: (v[0].replace(\"\\u064a\", \"\\u06cc\").replace(\"\\u06a9\", \"\\u0643\").replace(\"\\u0656\", \"\"), v[1]) for k, v in DICTIONARY.items()}   # Tur P: alt elif (\u0656) art\u0131\u011f\u0131 silinir"
    if s.count(o) != 1: sys.exit("HATA: app/engine/dictionary.py icinde beklenen metin yok")
    s = s.replace(o, n)
    o, n = "        FLAT.setdefault(_fk, _v)", "        FLAT.setdefault(_fk, _v)\n\n# Tur P: kesmesiz/ay\u0131ns\u0131z yaz\u0131m (mukatta'\u00e2t -> mukattaat, ta'm\u00eer\u00e2t -> tamirat). Yaln\u0131z s\u00f6zl\u00fckte yoksa;\n# T\u00fcrk\u00e7e k\u00f6k (Zemberek) ya da T\u00fcrk\u00e7e k\u00f6k + ek olan yaz\u0131m al\u0131nmaz (tan, kas, tersi). OSM_KESMESIZ=0 kapat\u0131r.\n_KESME_SIL = {ord(_c): None for _c in \"'\\u2019\\u2018\\u02bf\\u02be`\"}\nif _os.environ.get(\"OSM_KESMESIZ\", \"1\") != \"0\":\n    _ZK = set()\n    _zf = Path(__file__).parent.parent / \"data\" / \"zemberek_kok.txt\"\n    if _zf.exists():\n        _ZK = {_l.split()[0].lower() for _l in open(_zf, encoding=\"utf-8\") if _l.strip()}\n\n    def _turkce_mi(w):\n        if w in _ZK:\n            return True\n        return any(w.endswith(_e) and len(w) - len(_e) >= 3 and w[: -len(_e)] in _ZK for _e in LOOKUP_SUFFIXES)\n    _EK_KESME = set(LOOKUP_SUFFIXES) | _EK_ANAHTAR | set(\"yi y\u0131 yu y\u00fc ye ya n\u0131n nin nun n\u00fcn \u0131n in un \u00fcn e a i \u0131 u \u00fc ndan nden\".split())\n\n    def _ek_ayiraci(k):\n        # kesme ek ay\u0131rac\u0131ysa (t\u00fcrk\u00e7e'yi, feyzi'nin) kesmesiz yaz\u0131m \u00fcretilmez: yaln\u0131z ay\u0131n/hemze kesmesi\n        return any(_c in k and k.rsplit(_c, 1)[1] in _EK_KESME for _c in \"'\\u2019\")\n    _say = {}\n    for _k, _v in DICTIONARY.items():\n        _fk = _flat(_k).translate(_KESME_SIL)\n        if _fk != _flat(_k) and len(_fk) >= 4:\n            _say.setdefault(_fk, set()).add(_v[0])\n    for _k, _v in DICTIONARY.items():\n        _fk = _flat(_k).translate(_KESME_SIL)\n        if (_fk != _flat(_k) and len(_fk) >= (7 if _v[1] == \"sozlukler\" else 5) and len(_say[_fk]) == 1 and _fk not in DICTIONARY and _fk not in FLAT\n                and _fk not in _FLAT_EXCLUDE and _fk not in _CIKAR and not _turkce_mi(_fk) and not _ek_ayiraci(_k)\n                and _fk.replace(\"yy\", \"y\") not in DICTIONARY):   # \u00e7ift y: Hayrat'\u0131n tek y'li yaz\u0131m\u0131 (cemiyet \u062c\u0645\u0639\u06cc\u062a, Tur N)\n            FLAT[_fk] = _v"
    if s.count(o) != 1: sys.exit("HATA: app/engine/dictionary.py icinde beklenen metin yok")
    s = s.replace(o, n)
    if md5(s) != "6c4b27e8a7a0d5418fc049620b667ede": sys.exit("HATA: app/engine/dictionary.py sonuc md5 tutmadi")
    yaz("app/engine/dictionary.py", s); print("TAMAM: app/engine/dictionary.py")
# --- app/engine/transliterator.py
s = oku("app/engine/transliterator.py")
if md5(s) == "d087558696e456cc2116135a37b4c6c6": print("ATLANDI: app/engine/transliterator.py")
elif md5(s) != "25923443775c52ed1783427d0ef99879": sys.exit("HATA: app/engine/transliterator.py beklenen surum degil (md5 " + md5(s) + ")")
else:
    o, n = "                yazim = yazim[:-1]   # Tur L: Meyve Ris\u00e2lesi'nin -> \u0631\u0633\u0627\u0644\u0647\u200c\u0633\u0646\u06ad (Hayrat), iyelik \u06cc'si n'li ekten \u00f6nce d\u00fc\u015fer\n            yazim += _ifade_ek(turkish_text[m.start(1):m.end(1)], turkish_text[m.start(2):m.end(2)])", "                yazim = yazim[:-1]   # Tur L: Meyve Ris\u00e2lesi'nin -> \u0631\u0633\u0627\u0644\u0647\u200c\u0633\u0646\u06ad (Hayrat), iyelik \u06cc'si n'li ekten \u00f6nce d\u00fc\u015fer\n            _ek_yaz = _ifade_ek(turkish_text[m.start(1):m.end(1)], turkish_text[m.start(2):m.end(2)])\n            if yazim.endswith(\"\\u0647\") and _son2[-1:] in \"ae\" and _ek_yaz[:1] not in (\"\", \"\\u200c\"):\n                yazim += \"\\u200c\"   # Tur P: \u00fcnl\u00fc he ile biten ifade + ek ayr\u0131 (hakaik-i imaniyeyi \u062d\u0642\u0627\u0626\u0642 \u0627\u06cc\u0645\u0627\u0646\u06cc\u0647\u200c\u06cc\u06cc)\n            yazim += _ek_yaz"
    if s.count(o) != 1: sys.exit("HATA: app/engine/transliterator.py icinde beklenen metin yok")
    s = s.replace(o, n)
    if md5(s) != "d087558696e456cc2116135a37b4c6c6": sys.exit("HATA: app/engine/transliterator.py sonuc md5 tutmadi")
    yaz("app/engine/transliterator.py", s); print("TAMAM: app/engine/transliterator.py")
# --- hayrat.tsv: ad
s = oku("app/data/hayrat.tsv")
o, n = "\nad\u0009\u0639\u0627\u062f\u0009ar\n", "\nad\u0009\u0622\u062f\u0009tr\n"
if s.count(n) == 1: print("ATLANDI: hayrat.tsv")
elif s.count(o) == 1: yaz("app/data/hayrat.tsv", s.replace(o, n)); print("TAMAM: hayrat.tsv (ad)")
else: sys.exit("HATA: hayrat.tsv ad kaydi yok")
# --- hayrat_ifade.tsv: -iye + ek ZWNJ, Mu'ciz-ul Beyan
p = "app/data/hayrat_ifade.tsv"; s = oku(p); ilk = md5(s)
if ilk == "25e39c06f67e27f03610b859f018d1b3": print("ATLANDI: hayrat_ifade.tsv")
elif ilk != "56b37511ae1a9bc8c8fc251c10f5a89b": sys.exit("HATA: hayrat_ifade.tsv beklenen surum degil (md5 " + ilk + ")")
else:
    TAIL = re.compile("(\u06cc\u06cc|\u06cc\u0647|\u0646\u06ad|\u062f\u0646|\u062f\u0647|\u0633\u06cc|\u0644\u0631|\u0644\u0631\u06cc|\u0644\u0631\u06cc\u0646\u06cc|\u0644\u0631\u06cc\u0646\u0647|\u0644\u0631\u0646\u062f\u0647|\u0644\u0631\u0646\u062f\u0646|\u0644\u0631\u06ad|\u0644\u0631\u06cc\u0646\u06ad|\u0633\u0646\u06cc|\u0633\u0646\u0647|\u0633\u0646\u062f\u0647|\u0633\u0646\u062f\u0646|\u0633\u0646\u06ad|\u0633\u06cc\u0644\u0647|\u062f\u0647\u200c\u0643\u06cc|\u062f\u0631\u0643\u0647|\u062f\u0631|\u06cc\u0644\u0647)$")
    LAT = re.compile("(iye|\u0131ye)(yi|y\u0131|ye|ya|nin|n\u0131n|den|dan|de|da|si|s\u0131|ler|lar|leri|lerini|lerine|lerinde|lerinden|lerin|sini|sine|sinde|sinden|sinin|siyle|deki|dir|d\u0131r|yle|yla)$")
    out = []; say = 0
    for l in s.split("\n"):
        a = l.split("\t")
        if len(a) >= 2:
            w = a[0].split()[-1]; ws = a[1].split(); ow = ws[-1]
            if LAT.search(w) and "\u200c" not in ow:
                m = TAIL.search(ow)
                if m and ow[:m.start()].endswith("\u0647"):
                    ws[-1] = ow[:m.start()] + "\u200c" + ow[m.start():]; a[1] = " ".join(ws); say += 1
            l = "\t".join(a)
        out.append(l)
    s = "\n".join(out)
    s += "kur'an-\u0131 mu'ciz-\u00fcl beyan\u0009\u0642\u0631\u0622\u0646 \u0645\u0639\u062c\u0632 \u0627\u0644\u0628\u06cc\u0627\u0646\nmu'ciz-\u00fcl beyan\u0009\u0645\u0639\u062c\u0632 \u0627\u0644\u0628\u06cc\u0627\u0646\n"
    if say != 743 or md5(s) != "25e39c06f67e27f03610b859f018d1b3": sys.exit("HATA: hayrat_ifade.tsv sonuc tutmadi (" + str(say) + ")")
    yaz(p, s); print("TAMAM: hayrat_ifade.tsv (743 kayit + 2 ifade)")
# --- duzeltmeler.tsv
p = "app/data/duzeltmeler.tsv"; s = oku(p)
EK = "\u015fahab\u0009\u0634\u0647\u0627\u0628\u0009ar\n\u015fehab\u0009\u0634\u0647\u0627\u0628\u0009ar\njoseph\u0009\u0698\u0648\u0632\u0641\u0009sozlukler\nschacht\u0009\u0634\u0627\u062e\u062a\u0009sozlukler\n\u015fehabettin\u0009\u0634\u0647\u0627\u0628 \u0627\u0644\u062f\u0651\u06cc\u0646\u0009ar\n\u015fahabettin\u0009\u0634\u0647\u0627\u0628 \u0627\u0644\u062f\u0651\u06cc\u0646\u0009ar\n"
if s.endswith(EK): print("ATLANDI: duzeltmeler.tsv")
elif md5(s) == "e6e3a62e163b375e7e1ff9fd09421f18": yaz(p, s + EK); print("TAMAM: duzeltmeler.tsv (6 kayit)")
else: sys.exit("HATA: duzeltmeler.tsv beklenen surum degil")
# --- test
T = "\"\"\"Tur P (18 Ekim): sozlukte kesmesiz yazim (mukatta'at -> mukattaat), alt elif (U+0656) artigi, Hayrat ifadesi + ek ZWNJ\n(hakaik-i imaniyeyi), Kur'an-i Mu'ciz-ul Beyan, ad (isim), Sahabeddin, Joseph Schacht. Yazim birebir (ZWNJ dahil).\nCalistirma: docker run --rm -v \"$PWD\":/k -w /k berzahbey/osmanlica-cevirici:latest python tests/test_tur_p.py\"\"\"\nimport logging\nimport os\nimport sys\n\nlogging.disable(50)\nsys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), \"..\", \"app\"))\nfrom engine.transliterator import transliterate_text as T  # noqa: E402\n\nDURUMLAR = [\n    (\"mukattaat\", \"\\u0645\\u0642\\u0637\\u0651\\u0639\\u0627\\u062a\"),\n    (\"hakaik-i imaniyeyi\", \"\\u062d\\u0642\\u0627\\u0626\\u0642 \\u0627\\u06cc\\u0645\\u0627\\u0646\\u06cc\\u0647\\u200c\\u06cc\\u06cc\"),\n    (\"Kudret-i \\u0130lahiyenin\", \"\\u0642\\u062f\\u0631\\u062a \\u0627\\u0644\\u0647\\u06cc\\u0651\\u0647\\u200c\\u0646\\u06ad\"),\n    (\"Kur\\u2019an-\\u0131 Mu\\u2019ciz-\\u00fcl Beyan\\u2019\\u0131n\", \"\\u0642\\u0631\\u0622\\u0646 \\u0645\\u0639\\u062c\\u0632 \\u0627\\u0644\\u0628\\u06cc\\u0627\\u0646\\u06ad\"),\n    (\"ad koydu\", \"\\u0622\\u062f \\u0642\\u0648\\u06cc\\u062f\\u06cc\"),\n    (\"adlar\\u0131\", \"\\u0622\\u062f\\u0644\\u0631\\u06cc\"),\n    (\"\\u015eahabeddin\", \"\\u0634\\u0647\\u0627\\u0628 \\u0627\\u0644\\u062f\\u0651\\u06cc\\u0646\"),\n    (\"Joseph Schacht\", \"\\u0698\\u0648\\u0632\\u0641 \\u0634\\u0627\\u062e\\u062a\"),\n    (\"cemiyyet\", \"\\u062c\\u0645\\u0639\\u06cc\\u062a\"),\n]\nYOK = [\"Anadolu\", \"al\\u0131n\", \"avc\\u0131\", \"alacakl\\u0131\"]   # ciktida U+0656 olmamali\nKORUNAN = [(\"aras\\u0131\", \"\\u0622\\u0631\\u0627\\u0633\\u06cc\"), (\"tan\", \"\\u0637\\u0627\\u0646\"), (\"ada\", \"\\u0622\\u0637\\u0647\")]\n\n\ndef main():\n    kalan = 0\n    for w, b in DURUMLAR + KORUNAN:\n        c = T(w).strip()\n        if c != b:\n            kalan += 1\n            print(f\"KALDI {w} -> {c} (beklenen {b})\")\n    for w in YOK:\n        if \"\\u0656\" in T(w):\n            kalan += 1\n            print(f\"KALDI {w}: alt elif var\")\n    print(\"SONUC: HEPSI GECTI\" if not kalan else f\"SONUC: {kalan} TEST KALDI\")\n\n\nif __name__ == \"__main__\":\n    main()\n"
if os.path.exists("tests/test_tur_p.py") and oku("tests/test_tur_p.py") == T: print("ATLANDI: tests/test_tur_p.py")
else: yaz("tests/test_tur_p.py", T); print("TAMAM: tests/test_tur_p.py")
print("BITTI")
