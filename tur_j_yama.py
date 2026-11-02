# Tur J yama betigi (osmanlica-cevirici). Depo kokunde calistirilir: python3 /tmp/tur_j_yama.py
# Tekrar calistirilabilir: yapilmis degisiklik "ATLANDI" der; beklenen metin yoksa "HATA:" ile durur.
import sys

def oku(y):
    return open(y, encoding="utf-8").read()

def yaz(y, s):
    open(y, "w", encoding="utf-8").write(s)

def degistir(yol, eski, yeni, isaret):
    s = oku(yol)
    if isaret in s:
        print("ATLANDI:", yol, isaret[:50])
        return
    if s.count(eski) != 1:
        print("HATA:", yol, "beklenen metin", s.count(eski), "kez bulundu:", eski[:70])
        sys.exit(1)
    yaz(yol, s.replace(eski, yeni))
    print("TAMAM:", yol, isaret[:50])

def satir_ekle(yol, satirlar):
    s = oku(yol)
    var = set(l.split("\t")[0] for l in s.splitlines() if l and not l.startswith("#"))
    eklenen = 0
    for l in satirlar:
        anahtar = l.split("\t")[0]
        if anahtar in var and l in s.splitlines():
            continue
        if anahtar in var and yol.endswith("duzeltmeler.tsv"):
            # ayni anahtar varsa (eski kayit) sonradan okunan yeni satir onu ezer
            pass
        if not s.endswith("\n"):
            s += "\n"
        s += l + "\n"
        eklenen += 1
    yaz(yol, s)
    print("TAMAM:" if eklenen else "ATLANDI:", yol, eklenen, "satir")

Z = "\u200c"
T = "app/engine/transliterator.py"

# 0) Yeni dosyalar: app/engine/kuran_okunus.py ve tests/test_tur_j.py (sikistirilmis; md5 denetlenir)
import base64, zlib, hashlib, os
def dosya_yaz(yol, veri, md5):
    b = zlib.decompress(base64.b64decode("".join(veri.split())))
    if hashlib.md5(b).hexdigest() != md5:
        print("HATA:", yol, "md5 tutmuyor (betik bozulmus olabilir)")
        sys.exit(1)
    if os.path.exists(yol) and open(yol, "rb").read() == b:
        print("ATLANDI:", yol)
        return
    open(yol, "wb").write(b)
    print("TAMAM:", yol, md5)
dosya_yaz("app/engine/kuran_okunus.py", """
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
rEgwv92ab+NpD2uhNJqQ43+XpQ/2
""", "f589ef1c9ce4c078b19163197d592f61")
dosya_yaz("tests/test_tur_j.py", """
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
""", "663ee5a14ff338fe0de8660723c21cd5")
degistir("tests/test_tur_d.py", '("düşmemeniz", "دوشممه' + Z + 'ڭز")', '("düşmemeniz", "دوشمه' + Z + 'مه' + Z + 'ڭز")',
         '("düşmemeniz", "دوشمه' + Z + 'مه')

# 1) Sozluk duzeltmeleri (Hayrat'ta olmayan kelimeler; dogrusu Hayrat yazim kurallarina ve asli imlaya gore)
satir_ekle("app/data/duzeltmeler.tsv", [
    "dilediğine\tدیله" + Z + "دیگنه\ttr",      # eski sozluk kaydi دیلدیگنه (dilediği دیلهدیگی ile tutarsiz)
    "öldürün\tئولدیرڭ\ttr",                      # Hayrat öldür ئولدیر; eski kayit اولدرڭ
    "ölün\tئولڭ\ttr",                            # emir: Muslumanlar olarak olun (Zemberek "ölün" ismi sandiriyordu)
    "asanı\tعصاڭی\tar",                          # asa+n+i (Asanı taşa vur); eskiden آسان+ی
    "büyüyü\tبویویی\ttr",                        # buyu (sihir) + yu; eskiden بویویو
    "bıldırcın\tبلدرجین\ttr",                    # eskiden بیلدیرجڭ (-in ilgi eki sanildi)
    "rahimlerinde\tرحملرنده\tar",               # rahim (dol yatagi) رحم; râhimler راحملر، Rahîm رحیم ayri
    "lehinizedir\tلهڭزه" + Z + "در\tar",         # leh'in he'si unsuz (Hayrat lehine لهنه، lehinde لهنده)
    "sapsarı\tصاپ صاری\ttr",                     # Hayrat sarı صاری
    "unzurnâ\tانظرنا\tar",                       # Bakara 104 (انظرنا)
    "unzurna\tانظرنا\tar",
    "alaca\tآلاجه\ttr",
    "alacasız\tآلاجه" + Z + "سز\ttr",
    "rehin\tرهن\tar",                            # eskiden رهین
    "rehinler\tرهنلر\tar",
    "ilah\tاله\tar",
    "eşin\tاشڭ\ttr",                            # eş+in (Zemberek "eşin-" fiil koku sandiriyordu)                             # kaynak "sozlukler" idi: Tur F kurali (ilah+iniz الهڭز) islemiyordu
])

# 2) Elle kok: yağdır (Hayrat yağdırdı یاغدیردی، yağdırmak یاغدیرمق)
satir_ekle("app/data/kok_elle.tsv", ["yağdır\tیاغدیر\tV\t3", "kap\tقاپ\tV\t5"])   # kap- (Hayrat kapar قاپار): kapıverecek

# 3) Baglam kurali: kalın (emir) — solda bulunma hali (cennette kalın, orada kalın) قالڭ; sifat kalın قالین kalir
satir_ekle("app/data/baglam_kurallari.tsv", ["kalın\tقالڭ\tL1:([a-zçğıöşüâîû]+[dt][ae]|orada|burada|şurada)"])

# 4) Kesmeli ad + -ye/-ya: i/ı ile biten ad (Hayrat: Efendi'ye افندی یه): Elçi'ye ایلچی یه
degistir(T,
    '                    return kok_yazi + " یه"   # Tur H: elif maksura ile biten ad + -ya ayri (Hayrat: Mustafa\'ya, Isa\'ya)\n',
    '                    return kok_yazi + " یه"   # Tur H: elif maksura ile biten ad + -ya ayri (Hayrat: Mustafa\'ya, Isa\'ya)\n'
    '                if not sufs and tails_l in (["ya"], ["ye"]) and b.endswith(("i", "ı", "î")) and kok_yazi.endswith("ی") \\\n'
    '                        and " " not in kok_yazi and turkish_lower(word).replace("\\u2019", "\'").endswith(("\'ya", "\'ye")):\n'
    '                    return kok_yazi + " یه"   # Tur J: i ile biten ad + kesmeli -ye ayri (Hayrat: Efendi\'ye افندی یه): Elçi\'ye\n',
    "Tur J: i ile biten ad + kesmeli -ye")

# 5) Ek-fiil -yiz: ی ile biten govde + ییز ayri (Hayrat: etmeliyiz ایتملی ییز): vesilesiyiz وسیلهسی ییز
degistir(T,
    '        ara = "\\u200c" if go.endswith(("\\u0647", "\\u0627", "\\u062f", "\\u0631", "\\u0632", "\\u0648")) and yaz[0] != "\\u0643" else ""\n',
    '        if ek in ("yiz", "yız") and go.endswith("\\u06cc"):\n'
    '            return _unlu_he(go, g) + " \\u06cc\\u06cc\\u0632"   # Tur J: ی + -yiz ayri (Hayrat etmeliyiz ایتملی ییز)\n'
    '        ara = "\\u200c" if go.endswith(("\\u0647", "\\u0627", "\\u062f", "\\u0631", "\\u0632", "\\u0648")) and yaz[0] != "\\u0643" else ""\n',
    "Tur J: ی + -yiz ayri")

# 6) Kelime sonu duzeltmeleri (Tur J): her kelimenin son yaziminda
degistir(T,
    "    return WORD_RE.sub(lambda m: _he_ki(kelime(m), m.group(0)), sentence)\n",
    "    return WORD_RE.sub(lambda m: _tur_j(_he_ki(kelime(m), m.group(0)), m.group(0)), sentence)\n",
    "_tur_j(_he_ki(kelime(m)")

TUR_J = r'''

# ---- Tur J (17 Ekim, Bakara denetimi 2): kelime sonu duzeltmeleri. Hayrat'taki tam kelimeye dokunulmaz. OSM_TUR_J=0 kapatir. ----
_TUR_J_ACIK = __import__("os").environ.get("OSM_TUR_J", "1") != "0"
_KOPULA = ("dır", "dir", "dur", "dür", "tır", "tir", "tur", "tür")
_TJ_UNLU = "aeıioöuüâîû"


def _tj_fiil(r: str) -> bool:
    """Fiil koku: sozlukte -mak/-mek ya da kok sozlugunde; isimden -la/-le ile turemis fiil (bağış+la, temiz+le)."""
    if _fiil_koku_mu(r):
        return True
    m = re.fullmatch(r"(.{3,}?)l[ae]n?", r)
    return bool(m and (dictionary.lookup_exact(m.group(1)) or dictionary.lookup_exact(r)))


def _tur_j(o: str, latin: str) -> str:
    if not _TUR_J_ACIK or not o or " " in o:
        return o
    w = latin
    wl = turkish_lower(w).replace("’", "'")
    if "'" in wl or wl in dictionary.HAYRAT_ANAHTAR or len(wl) < 4:
        return o
    tam = dictionary.lookup_exact(wl)
    # a) ettirgen emir -dIr (Hayrat yağdırdı یاغدیردی، alıştırmak آلیشدیرمق): kok sozlugunde fiil olan kelime ek-fiil -dır sanilmaz
    kv = kok.KOK.get(wl, {})
    if not tam and "V" in kv and "N" not in kv and wl.endswith(_KOPULA):
        h, s = dictionary.lookup_with_suffix(wl)
        if h and s and s[-1] in _KOPULA and len(s) == 1:
            return kv["V"][0].replace("\u06af", "\u0643")
    if tam:
        return o
    # b) iki harfli kok (ünlü + ünsüz) + ilgi/iyelik -ın/-in: ڭ (Hayrat işin ایشڭ، başın باشڭ): eşin اشڭ (ekin, akın gibi isimler haric)
    m = re.fullmatch(r"([aeıioöuü][^aeıioöuü])([ıiuü])n", wl)
    if m and wl not in kok.ZKOK:
        r = dictionary.lookup_exact(m.group(1))
        if r and " " not in r[0] and (o == r[0] + "\u06cc\u0646" or o == r[0] + "\u0648\u0646"):
            return r[0] + "\u06ad"
    # c) -ıver- tezlik fiili (Hayrat oluvermeleri اولیویرمهلری، bakıver باقیویر، salıverdim صالیویردم)
    m = re.fullmatch(r"(.+?)([ıiuü])(ver(?:[^aeıioöuü]|[aeıioöuü]).*|ver)", wl)
    if m and len(m.group(1)) >= 2 and _tj_fiil(m.group(1)) and not _fiil_koku_mu(m.group(1) + m.group(2)):
        kv1 = kok.KOK.get(m.group(1), {}).get("V")
        gov = kv1[0] if kv1 else draft_transliterate_sentence(m.group(1)).strip()
        kuy = _he_ki(draft_transliterate_sentence(m.group(3)).strip(), m.group(3))
        if gov and kuy.startswith("\u0648\u06cc\u0631") and " " not in gov + kuy:
            return (gov + "\u06cc" + kuy).replace("\u06af", "\u0643")
    # d) mastar + 2. tekil iyelik -nı/-na (Hayrat olmanı اولمهڭی، buyurmanı بویورمهڭی، okutmanı اوقوتمهڭی)
    m = re.fullmatch(r"(.+)m([ae])n([ıiae])", wl)
    if m and _tj_fiil(m.group(1)) and not dictionary.lookup_exact(wl[:-1]) and wl[:-1] not in kok.ZKOK \
            and not dictionary.lookup_with_suffix(wl[:-1])[0]:
        y = re.sub("\u0645[\u0627\u0647]?\u200c?\u0646[\u06cc\u0647]$", "\u0645\u0647\u200c\u06ad" + ("\u06cc" if m.group(3) in "ıi" else "\u0647"), o)
        if y != o:
            return y
    # e) olumsuz mastar -meme- (Hayrat görmemek كورمهمك، etmemeniz ایتمهمهڭز): ödememek اودهمهمك، düşmemeniz دوشمهمهڭز
    i = wl.find("meme")
    if i >= 2 and _tj_fiil(wl[:i]) and "\u0645\u0645" in o:
        o = o.replace("\u0645\u0645", "\u0645\u0647\u200c\u0645", 1)
        if re.search(r"meme(s|l[ıi])", wl):
            o = o.replace("\u0645\u0647\u200c\u0645\u0647\u200c", "\u0645\u0647\u200c\u0645", 1)   # Hayrat bilmemesini بیلمهمسنی، vermemeli ویرمهملی
    # f) -(y)emeyecek (Hayrat ödeyemeyeceğiz اودهیهمهیهجگز، söyleyemez سویلهیهمز)
    if "yemeyece" in wl:
        o = o.replace("\u06cc\u0645\u06cc\u0647\u200c\u062c", "\u06cc\u0647\u200c\u0645\u0647\u200c\u06cc\u0647\u200c\u062c")
    # g) kalın -madan (Hayrat okumadan اوقومادن، 36 kelime): yummadan یوممادن
    if wl.endswith("madan") and _tj_fiil(wl[:-5]) and not dictionary.lookup_exact(wl[:-3]) and wl[:-3] not in kok.ZKOK:
        # yalniz fiil + -madan (zarf-fiil); isim + -dan (lokmadan لقمهدن، sıtmadan) Hayrat'ta مهدن
        o = re.sub("\u0645\u0647\u200c?\u062f\u0646$", "\u0645\u0627\u062f\u0646", o)
    # h) -lardan + ek: لردن (Hayrat onlardandır اونلردندر): sapanlardandınız صاپانلردندیڭز
    if "lardan" in wl:
        o = o.replace("\u0644\u0631\u062f\u0627\u0646", "\u0644\u0631\u062f\u0646")
    # i) ettirgen -dIr/-tIr + -uyor: ییور (Hayrat dolduruyor طولدیرییور، bulunduruyor، durduruyorlar، boğduruyordu):
    #    öldürüyordunuz ئولدیرییوردیڭز. Öteki -uyor/-üyor Hayrat'ta ویور (konuşuyor قونوشویور، görüyor كورویور): dokunulmaz
    m = re.search(r"[dt][ıiuü]r([uü])yor", wl)
    if m and _fiil_koku_mu(wl[:m.start(1)]) and _fiil_koku_mu(wl[:m.start(1) - 3]):   # öl+dür، dol+dur (otur değil)
        o = o.replace("\u0631\u0648\u06cc\u0648\u0631", "\u0631\u06cc\u06cc\u0648\u0631", 1)
    return o
'''

s = oku(T)
if "def _tur_j(" in s:
    print("ATLANDI:", T, "_tur_j tanimi")
else:
    anahtar = '_UNLU_HE_ACIK = __import__("os").environ.get("OSM_UNLU_HE", "1") != "0"\n'
    if s.count(anahtar) != 1:
        print("HATA:", T, "_UNLU_HE_ACIK satiri bulunamadi")
        sys.exit(1)
    yaz(T, s.replace(anahtar, anahtar + TUR_J))
    print("TAMAM:", T, "_tur_j tanimi")
# 6b) En dis katman: Kur'an mealinde parantez icindeki Arapca okunuslar Kur'an'daki kelimeyle (engine/kuran_okunus.py)
KATMAN = r"""


# ---- Tur J (17 Ekim): en dış katman — mealde parantez içindeki Arapça okunuş (el-muttaqîn) Kur'an'daki Arapça yazımıyla ----
from . import kuran_okunus as _kuran_okunus
_transliterate_text_okunussuz = transliterate_text
_OKUNUS_PARANTEZ = re.compile(r"\(([^()\n]{2,80})\)")
_OKUNUS_GUCLU = re.compile(r"(q|['’‘]|(?<![^\W\d_])(?:e[lsşrtdzn]|at|ed)-|(?<![^\W\d_])el(?=[bcçdfğhkmnprsştvyz]))")


def _okunus_mu(ic: str, ayetli: bool) -> bool:
    if re.search(r"[A-ZÇĞİÖŞÜÂÎÛ0-9öüç/]", ic) or not re.fullmatch(r"[a-zğıışâîûq'’‘\- ]+", ic):
        return False                     # büyük harf, rakam, ö/ü/ç (Türkçe), eğik çizgi: okunuş değil
    if _OKUNUS_GUCLU.search(ic):
        return True
    return ayetli and bool(re.search(r"[âîû]|ğ", ic))     # ayet numaralı paragrafta uzun ünlü ya da ğ (eşribû, ğulfun)


def transliterate_text(turkish_text, *args, **kwargs):
    if not isinstance(turkish_text, str) or "(" not in turkish_text:
        return _transliterate_text_okunussuz(turkish_text, *args, **kwargs)
    saklanan = []
    parcalar = []
    for par in turkish_text.split("\n"):
        m = re.match(r"\s*(\d{1,3})\s*[.)]", par)
        ayet = int(m.group(1)) if m else None

        def degis(mm):
            ic = mm.group(1).strip()
            if not _okunus_mu(ic, ayet is not None):
                return mm.group(0)
            ar = _kuran_okunus.bul(ic, ayet)
            if not ar:
                return mm.group(0)
            saklanan.append(ar)
            return "(" + chr(0xeb00 + len(saklanan) - 1) + ")"
        parcalar.append(_OKUNUS_PARANTEZ.sub(degis, par) if len(saklanan) < 200 else par)
    if not saklanan:
        return _transliterate_text_okunussuz(turkish_text, *args, **kwargs)
    out = _transliterate_text_okunussuz("\n".join(parcalar), *args, **kwargs)
    for i, ar in enumerate(saklanan):
        out = out.replace("" + chr(0xeb00 + i), ar)
    return out
"""
s = oku(T)
if "_transliterate_text_okunussuz" in s:
    print("ATLANDI:", T, "okunus katmani")
else:
    yaz(T, s.rstrip("\n") + "\n" + KATMAN)
    print("TAMAM:", T, "okunus katmani")

# 7) hayrat.tsv: sapkasiz anahtarlarda kaybolmus ZWNJ (bitismez he) Hayrat kelime ciftlerindeki yazimdan geri konur
#    (vesilesi وسیلهسی، mucizeyi معجزهیی، defadır دفعهدر، ailesi عائلهسی). Ayni kelimenin bitisik yazimi Hayrat'ta daha sik ise dokunulmaz.
import collections, re
def _sade(x):
    return x.translate(str.maketrans("âîûÂÎÛāīū", "aiuaiuaiu"))
_ciftler = collections.defaultdict(list)
for l in open("tools/hayrat_kelime_ciftleri.tsv", encoding="utf-8"):
    a = l.rstrip("\n").split("\t")
    if len(a) >= 3:
        _ciftler[_sade(a[0].lower())].append((a[1], int(a[2])))
_satirlar, _deg = [], 0
for l in open("app/data/hayrat.tsv", encoding="utf-8"):
    a = l.rstrip("\n").split("\t")
    if len(a) >= 2 and Z not in a[1] and "\u0647" in a[1]:
        c = [(re.sub(Z + "(?![\u0621-\u064a\u067e\u0686\u0698\u06a9\u06ad\u06af\u06cc])", "", o.replace("\u06d5", "\u0647" + Z)), n)
             for o, n in _ciftler.get(_sade(a[0]), [])]   # ZWNJ yalniz harften once (sondaki ە ve ؐ isareti oncesi atilir)
        c = [x for x in c if Z in x[0] and x[0].replace(Z, "") == a[1]]
        bit = sum(n for o, n in _ciftler.get(_sade(a[0]), []) if o.replace("\u06d5", "\u0647") == a[1] and "\u06d5" not in o.rstrip("\u06d5"))
        if c and max(n for _, n in c) > bit:
            a[1] = max(c, key=lambda x: x[1])[0]
            _deg += 1
        elif not _ciftler.get(_sade(a[0])) and not _ciftler.get(_sade(a[0]).replace("'", "").replace("\u2019", "")) and " " not in a[1]:
            # Hayrat ciftlerinde birebir olmayan (kesmeli/ayinli kaynaktan gelen) kayit: unlu he kurali (Tur D) — Latin'deki h kadar he unsuz
            unsuz = a[0].lower().count("h") - a[1].count("\u062d") - a[1].count("\u062e")
            o2 = []
            for j, ch in enumerate(a[1]):
                o2.append(ch)
                if ch == "\u0647":
                    if unsuz > 0:
                        unsuz -= 1
                    elif re.match("\u0647(?=[\u0621-\u064a\u067e\u0686\u0698\u06a9\u06ad\u06af\u06cc])", a[1][j:]):
                        o2.append(Z)
            if "".join(o2) != a[1]:
                a[1] = "".join(o2)
                _deg += 1
    _satirlar.append("\t".join(a))
if _deg:
    yaz("app/data/hayrat.tsv", "\n".join(_satirlar) + "\n")
    print("TAMAM: app/data/hayrat.tsv ZWNJ geri kondu:", _deg, "kayit")
else:
    print("ATLANDI: app/data/hayrat.tsv (ZWNJ zaten tamam)")
print("BITTI")
