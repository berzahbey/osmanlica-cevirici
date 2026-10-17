# -*- coding: utf-8 -*-
"""
Ana orkestrasyon: girdi metnini alır, gerekiyorsa Türkçeye çevirir,
sonra Osmanlıcaya (Arap harfli) çevirir: sözlük + kural motoru (yapay zekâ yok, çıktı her çalıştırmada aynı).
"""
import re
import unicodedata
import logging
from langdetect import detect, DetectorFactory

from . import dictionary
from . import rules
from . import kok
_KOK_MOD = kok
from .alphabet import turkish_lower

DetectorFactory.seed = 0
logger = logging.getLogger("osmanlica")

SENTENCE_SPLIT_RE = re.compile(r"((?<=[.!?;:\n])\s+)")
WORD_RE = re.compile(r"[A-Za-zÇçĞğİıÖöŞşÜüÂâÎîÛû]+(?:['’][A-Za-zÇçĞğİıÖöŞşÜüÂâÎîÛû]+)*")


def detect_language(text: str) -> str:
    sample = text[:2000].strip()
    if not sample:
        return "tr"
    try:
        return detect(sample)
    except Exception:
        return "tr"


def draft_transliterate_sentence(sentence: str) -> str:
    """Cümledeki her kelimeyi önce sözlükte arar, bulamazsa kural motoruna düşer."""
    def repl(m):
        word = m.group(0)
        if "'" in word or "\u2019" in word:
            parts = word.replace("\u2019", "'").split("'")
            base = parts[0]
            tails = parts[1:]
            # Kesme işareti kelimenin kendi parçası olabilir (Kur'an, Mes'ud, san'at):
            # önce birleşik hâlini sözlükte ara, kalan parçaları ek say. Kur'an'ın -> Kur'an + ın
            # Kesmeli kelimenin son parçasına ek bitişmiş olabilir: Kur'anı -> Kur'an + ı
            if len(parts) == 2:
                son = turkish_lower(parts[1])
                for i in range(len(son) - 1, 0, -1):
                    if _ek_mi(son[i:]) and dictionary.lookup_exact(parts[0] + "'" + parts[1][:i]):
                        parts = [parts[0] + "'" + parts[1][:i], parts[1][i:]]
                        base, tails = parts[0], parts[1:]
                        break
            for k in range(len(parts), 1, -1):
                joined = "'".join(parts[:k])
                if dictionary.lookup_exact(joined):
                    base, tails = joined, parts[k:]
                    break
                birlesik = dictionary.lookup_exact(joined.replace("'", ""))
                if birlesik and not (k == 2 and re.search(r"([^aeıioöuüâîû])\1$", turkish_lower(parts[0]))
                                     and _ek_mi(turkish_lower(parts[1])) and dictionary.lookup_exact(parts[0])):
                    # Şeddeli kök + ek: Hakk'a -> Hakk + a (حقّه); sözlükteki "hakka" (حقا, "gerçekten") başka kelime
                    base, tails = joined.replace("'", ""), parts[k:]
                    break
            if base == parts[0] and len(parts) == 2 and not _ek_mi(turkish_lower(parts[1])):
                # ayın/hemze işareti (ma’nâ, te’mîn): ek ayıracı değil, kelimenin parçası
                tam = turkish_lower(word.replace("\u2019", "'"))
                h2 = rules._harmony_class(tam.replace("'", ""))
                for aday in (tam.replace("'", "\u2018"), tam):
                    hit2, sufs2 = dictionary.lookup_with_suffix(aday)
                    if hit2:
                        kok2 = aday[: len(aday) - len("".join(sufs2))] if sufs2 else aday
                        return hit2[0] + rules.ekleri_yaz(kok2, sufs2, [], h2, rules.ek_guvenilir(kok2, sufs2))
                if re.search("[âîûāīū]", tam):   # şapkasız kelimede kesme işareti ek ayıracıdır (Çeşmesi'nde, Urfa'daki)
                    return rules.transliterate_word_with_suffix(tam.replace("'", "\u2018"))
            harmony = rules._harmony_class(turkish_lower(word).replace("'", ""))
            hit, sufs = dictionary.lookup_with_suffix(base)
            b = turkish_lower(base).replace("'", "")
            tails_l = [turkish_lower(t) for t in tails if t]
            if hit:
                root = b[: len(b) - len("".join(sufs))] if sufs else b
                kok_yazi = hit[0]
                if not sufs and tails_l and tails_l[0][:1] == "n" and kok_yazi.endswith("\u0633\u06cc") \
                        and b.endswith(("si", "sı", "su", "sü")):
                    kok_yazi = kok_yazi[:-1]   # Gazetesi'nin -> غزتهسنڭ (Hayrat)
                if not sufs and tails_l in (["ya"], ["ye"]) and b.endswith(("a", "â")) and turkish_lower(word).replace("\u2019", "'").endswith(("'ya", "'ye")) and kok_yazi.endswith("ی") \
                        and " " not in kok_yazi:
                    return kok_yazi + " یه"   # Tur H: elif maksura ile biten ad + -ya ayri (Hayrat: Mustafa'ya, Isa'ya)
                return kok_yazi + rules.ekleri_yaz(root, sufs, tails_l, harmony, rules.ek_guvenilir(root, sufs))
            return rules.transliterate_word_with_suffix(base) + rules.ekleri_yaz(b, [], tails_l, harmony)

        hit, sufs = dictionary.lookup_with_suffix(word)
        if not hit or sufs:
            bilesik = _bilesik_fiil(word)
            if bilesik:
                return bilesik
        if hit:
            if not sufs:
                return hit[0]
            w = turkish_lower(word)
            root = w[: len(w) - len("".join(sufs))]
            harmony = rules._harmony_class(w)
            return hit[0] + rules.ekleri_yaz(root, sufs, [], harmony, rules.ek_guvenilir(root, sufs))
        o = rules.transliterate_word_with_suffix(word)
        return kok.kokle(word, o) or o   # kök sözlüğü: kural motorunun kökü Hayrat yazımıyla (gizleyemezler كیزله‌یه‌مزلر)

    def tirnak_eki(m):
        kelime, isaret, ek = m.group(1), m.group(2), m.group(3)
        if not _ek_mi(turkish_lower(ek)):
            return m.group(0)
        ayrik = _ayrik_ek(m.string, m.start(1), turkish_lower(kelime))
        if ayrik:
            return ayrik + isaret + rules.ekleri_yaz(turkish_lower(kelime), [], [turkish_lower(ek)],
                                                     rules._harmony_class(turkish_lower(kelime + ek)))
        tam = _ek_duzelt(repl(_Eslesme(kelime + "'" + ek)), kelime + ek)
        kok = _ek_duzelt(repl(_Eslesme(kelime)), kelime)
        if not tam.startswith(kok):
            # şedde farkı (sözlükte "hak'tan" حقدن, "hak" حقّ): şeddesiz karşılaştırılır, ek kısmı tam yazımdan alınır
            t2, k2 = tam.replace("\u0651", ""), kok.replace("\u0651", "")
            if not t2.startswith(k2):
                # ek, tırnaktan sonra ek olarak yazılır (eskiden ayrı kelime sayılıp Hayrat'ın ek parçası kayıtlarına düşüyordu)
                kl, el = turkish_lower(kelime), turkish_lower(ek)
                return kok + isaret + rules.ekleri_yaz(kl, [], [el], rules._harmony_class(kl + el))
            return kok + isaret + t2[len(k2):]
        return kok + isaret + tam[len(kok):]

    sentence = _TIRNAK_EK_RE.sub(tirnak_eki, sentence)
    def kelime(m):
        w = m.group(0)
        wl = turkish_lower(w)
        ayrik = _ayrik_ek(m.string, m.start(), wl) if hasattr(m, "string") else None
        if ayrik:
            return ayrik
        if wl in dictionary.HAYRAT_ANAHTAR:
            return repl(m)            # Hayrat'taki tam kelime: ek kuralları dokunmaz (tek ölçü)
        my = re.fullmatch(r"(.{3,}[ıiuü])y([ıiuüae])", wl)
        if my and "'" not in w and "’" not in w and not dictionary.lookup_exact(wl) and wl not in _KOK_MOD.ZKOK \
                and (dictionary.lookup_exact(my.group(1)) or my.group(1) in _KOK_MOD.ZKOK) and not _fiil_koku_mu(my.group(1)) \
                and not (my.group(2) in "ae" and (my.group(1) not in _KOK_MOD.ZKOK or re.search(r"[^aeıioöuüâîû][iî]y[ae]$", wl) and "â" in wl)):
            # -ya/-ye yalniz Zemberek kokunde: Arapca -iye disil sifat olabilir (ahlakiye, umumiye, zatiye): ayrilmaz
            _sy = draft_transliterate_sentence(w[:len(my.group(1))]).strip()
            _ek = " یی" if my.group(2) in "ıiuü" else " یه"
            _tm = repl(m)
            if not (_sy[:-1] and _tm.startswith(_sy[:-1])):
                # Tur I2: kok tek basina baska yaziliyorsa (testi, pihti) kelimenin kendi yazimindan ayrilir
                _sy = _tm[:-2] if _tm.endswith(("ییی", "ییه")) else (_tm[:-1] if _tm.endswith("یه") else "")
            if _sy.endswith("ی") and " " not in _sy:
                return _sy + _ek
                # Tur I: ی ile biten kelime + -yi / -ya ayri (Hayrat: yaziyi, dogruya, simdiye; suyu bitisik kalir)
        kv = _KOK_MOD.KOK.get(wl, {})
        if "V" in kv and "N" not in kv and "'" not in w and not dictionary.lookup_exact(wl) and not dictionary.lookup_with_suffix(wl)[0]:
            return kv["V"][0]         # Tur D: yalın fiil kökü (emir): vur اور (Hayrat), eskiden harf harf وور
        ma = re.fullmatch(r"(.{4,}?)[aâ]ne", wl.replace("’", "").replace("'", ""))
        if ma and "'" not in w and not dictionary.lookup_exact(wl) and not dictionary.lookup_exact(wl[:-1]) \
                and not dictionary.lookup_exact(wl[:-2]):   # insan+e, divan+e değil
            _ak = dictionary.lookup_exact(ma.group(1))
            if _ak and " " not in _ak[0] and _ak[0][-1:] not in "\u0647\u0627":
                return _ak[0] + "\u0627\u0646\u0647"   # Tur G: Farsça -âne zarfı (Hayrat: mürîdâne مریدانه، mütekellimâne متكلّمانه)
        tz = _tenvin_zarf(wl)
        if tz:
            return tz                 # Arapça -en zarfı: hakîkaten حقیقتًا، zâhiren ظاهرًا (Hayrat)
        ca = _ca_eki(wl)
        if ca:
            return ca                 # -ca/-ce eki: Osmanlıca عثمانلیجه، devletçe دولتجه (Hayrat)
        if "'" not in w and "\u2019" not in w and not dictionary.lookup_exact(wl):
            ez = _ek_fiil(wl, repl)
            if ez:
                return ez             # ek-fiil -ken/-yse/-yiz (Tur B): halindeyken حالنده‌یكن، şüphedeyseniz شبهه‌ده‌یسه‌ڭز
        o = _lerin_eki(w, _matbaa_ekleri(w, _ek_duzelt(repl(m), w)))
        if "'" in w or "\u2019" in w or len(wl) < 4 or dictionary.lookup_exact(wl):
            return o
        mn = re.search(r"[aeıioöuü](n[ıiuü]z)(" + "|".join(_NIZ_SONRA) + r")?$", wl)
        kok = wl[:mn.start(1)] if mn else wl[:-3]
        _kh = dictionary.lookup_exact(kok) if mn else None
        if mn and mn.group(2) and (dictionary.lookup_exact(kok[:-1]) or dictionary._get_soft(kok[:-1]) or kok[:-1] in globals()["kok"].ZKOK or kok[:-1].endswith(("ât", "ūt"))
                                   or (kok[-1] in "uü" and _kh and _kh[0].endswith("\u06cc")) or _fiil_koku_mu(kok[:-2]) and kok[-2:] in ("ma", "me")):
            mn = None                          # ünsüzle biten kök + iyelik -ınız + hâl (adâlet+iniz+den): _imiz_yazimi
        if mn and kok[-1:] in "ıiuü" and len(kok) >= 5:
            _k1 = dictionary.lookup_exact(kok[:-1])
            if _k1 and (str(_k1[1]).startswith(("ar", "fa")) or kok[:-1].endswith(("an", "en"))) and dictionary.lookup_with_suffix(wl)[0] \
                    and _k1[0][-1:] not in "\u062f\u0630\u0631\u0632\u0648\u0698\u0627":   # bitişmeyen harften sonra Hayrat ی yazar (cihadınız جهادیڭز)
                mn = None                      # Tur F: ünsüzle biten Arapça isim / -an sıfat-fiil + -ınız (ilah+ınız الهڭز، yaratan+ınız)
        if mn and dictionary.lookup_exact(kok) and not re.search(r"[ğsy][ıiuü]$", kok) and \
                not (re.search(r"[dt][ıiuü]$", kok) and (dictionary.lookup_exact(kok[:-2] + "mak") or dictionary.lookup_exact(kok[:-2] + "mek"))):
            _kg = _ek_duzelt(repl(_Eslesme(kok)), kok)
            if kok[-2:] in ("ma", "me") and _fiil_koku_mu(kok[:-2]) and _kg[-1:] in "\u0627\u0647":
                _kg = _kg[:-1] + "\u0647\u200c"   # Tur F: mastar + -nız (Hayrat olmanız اولمه‌ڭز): almanız آلمه‌ڭز (alma آلما değil)
            return _kg + "ڭز" + _NIZ_SONRA.get(mn.group(2) or "", "")
            # ünlüyle biten isim + -nız: ordunuz اوردوڭز (oldunuz değil); Tur C: + hâl eki (elçinizi ایلچیڭزی، kapınıza)
        if _EK_KURALLARI:
            yeni = _hayrat_ek_kurali(wl, o)   # sözlükte olmayan kelime: Hayrat'tan öğrenilen ek sonu
            kh, ks = dictionary.lookup_with_suffix(wl)
            kok_yazi = (kh[0] if kh and ks and str(kh[1]).startswith(("ar", "fa")) else "").replace("\u0651", "")
            if kok_yazi and len(kok_yazi) > len(wl) - len("".join(ks)) - 2:
                kok_yazi = ""                  # ünlüleri yazılan (Türkçe) kök: bacak باجاق -> bacağa باجاغه
            if yeni.count("\u0627\u0631") < o.count("\u0627\u0631") and _genis_zaman(wl):
                yeni = o                       # Tur C: geniş zaman -ar'ın elifi (kılarsa قیلارسه، anlarsa آڭلارسه) silinmez
            if "\u0627\u06cc\u0627\u06cc" in yeni and "\u0627\u06cc\u0627\u06cc" not in o:
                yeni = o                       # Tur C: öğrenilmiş ek sonu bileşik fiilde ای'yi ikiler (ذكر ایایده‌جك)
            if kh and ks in (["in"], ["ın"], ["un"], ["ün"]) and o == kh[0] + "\u06ad" and dictionary.lookup_exact(wl[:-2]) \
                    and not kh[0].endswith("\u06ad"):
                yeni = o                       # Tur E: sözlük kökü + ilgi eki ڭ (evren+in اورنڭ): öğrenilmiş ek sonu (ینڭ) uygulanmaz
            _st = wl[:len(wl) - len("".join(ks))] if kh and ks else ""
            _mv = _KOK_MOD.KOK.get(_st[:-2], {}).get("V") if re.fullmatch(r".{3,}m[ae]", _st) and ks[0][:1] == "s" and kh[0][-1:] == "ا" \
                and o.startswith(kh[0]) and _fiil_koku_mu(_st[:-2]) else None
            if _mv and ks in (["sın"], ["sin"], ["sın", "lar"], ["sin", "ler"]):
                o = yeni = _mv[0] + ("ماسین" if _st[-1] == "a" else "مه\u200cسین") \
                    + ("لر" if len(ks) == 2 else "")   # Tur G2b: olumsuz emir -mAsIn (Hayrat olmasin, etmesin)
            elif _mv:
                o = yeni = _mv[0] + "مه\u200c" + o[len(kh[0]):]   # Tur G2: fiil + -mA + -sI (yag+ma+sini, Hayrat yagmasi)
            if kh and ks and str(kh[1]).startswith(("ar", "fa")) and kh[0][-1:] == "\u0627" and o.startswith(kh[0]) \
                    and not yeni.startswith(kh[0]):
                yeni = o                       # Tur G: elifle biten Arapça kök (sema+sını سماسنی) öğrenilmiş ek sonuyla ه olmaz
            if _cift_harf(yeni) > _cift_harf(o):
                yeni = o                       # öğrenilmiş ek sonu harfi ikinci kez yazıyor (yiyecek+in یییه‌ه‌جكڭ): sözlük kökü + ek kalır
            if not (kok_yazi and o.replace("\u0651", "").startswith(kok_yazi) and not yeni.replace("\u0651", "").startswith(kok_yazi)):
                o = yeni                       # Arapça/Farsça kökün harfleri değişmez: şafağın شفقڭ
        em = _emir_in(wl, w[:1].isupper())
        if em:
            return em                          # Tur C: emir -ın/-in (inin اینڭ، uyun اویڭ، faydalanın فائده‌لانڭ)
        if re.search(r"[ae]r[ıi][zm]$", wl) and _genis_zaman(wl):
            o = re.sub("ری([زم])$", r"ر\1", o)               # Tur C: geniş zaman -arız/-erim (Hayrat: başlarız باشلارز، bekleriz بكلرز)
        if re.search(r"[dt][ıiuü]kt[ae]n$", wl):
            o = re.sub("([دت])ی?([قك])دن$", r"\1\2دن", o)       # -dıktan/-dikten (Tur B, Hayrat): آچیقلادقدن، كوردكدن
        if re.search(r"[dt][ıiuü]ğ[ıiuü]n[ıiuü]z", wl):
            o = re.sub("([غك])ی?ن[یو]ز", r"\1ڭز", o)            # -dığınız/-duğunuz (Tur B, Hayrat): اولوندیغڭز، كوردیكڭز
            o = o.replace("شتیغ", "شدیغ").replace("شتیك", "شدیك")   # -ştuğ- (kavuştuğunuz قاووشدیغڭز)
        if re.search(r"[dt][ıu]ğ[ıu]nda$", wl):
            o = re.sub("[دت][قغ]نده$", "دیغنده", o)          # -dığında (Hayrat: vardığında واردیغنده، baktığında باقدیغنده)
        if re.search(r"m[iü]yor", wl):
            o = re.sub("مه\u200c?ه?یور", "مییور", o)          # -miyor/-müyor (Hayrat: görünmüyor كورونمییور)
        m = re.search(r"[^aeıioöuü]([ae])s[ıi]n$", wl)
        if m and (dictionary.lookup_exact(wl[:-4] + "mak") or dictionary.lookup_exact(wl[:-4] + "mek")):
            o = re.sub("(?:ا|ه\u200c?)?(?:سین|سڭ)$", "اسڭ" if m.group(1) == "a" else "ه\u200cسڭ", o)
            # istek 2. tekil (Hayrat): kalında اسڭ (olasın اولاسڭ، davranasın طاوراناسڭ)، incede ه‌سڭ (gizleyesin كیزله‌یه‌سڭ)
        o = _tur_d_ekler(wl, o)
        return _iyelik_hal_yazimi(wl, _imiz_yazimi(wl, o))

    return WORD_RE.sub(lambda m: _he_ki(kelime(m), m.group(0)), sentence)


def _he_ki(o: str, latin: str) -> str:
    """Tur C: -deki/-daki ekinde he bitişmez (Hayrat دەكی; çevirici ه + ZWNJ): یانلرنده‌كی. Eskiden دهكی bitişik basılıyordu."""
    if "\u0647\u0643\u06cc" in o and re.search(r"[dt][ae]ki", turkish_lower(latin)):
        o = o.replace("\u062f\u0647\u0643\u06cc", "\u062f\u0647\u200c\u0643\u06cc")
    if "\u0647\u06ad" in o and not re.search(r"h['’]?[ıiuüâ]?n", turkish_lower(latin)):   # Allah'ın اللّهڭ، padişahın: ه ünsüz
        o = o.replace("\u0647\u06ad", "\u0647\u200c\u06ad")   # Tur C: he + ڭ bitişmez (سه‌ڭز، طلبه‌ڭز; Hayrat ە)
    return _unlu_he(o, latin)


_OSM_HARF = "[\u0621-\u064a\u067e\u0686\u0698\u06a9\u06ad\u06af\u06cc]"


def _tur_d_ekler(wl: str, o: str) -> str:
    """Tur D: sözlükte olmayan kelimede (kural motoru) ek ortasındaki fazla elif ve -nız (Hayrat yazımı). OSM_TUR_D_EK=0 kapatır.
    - çoğul -lar + ek: لار -> لر (sınırlarıdır صینیرلریدر، bozguncuların، sapanlardandınız); geniş zaman -ar (başla-r، kıl-ar) dokunulmaz;
    - -acak + ek: اجاق/اجاغ -> اجق/اجغ (harcayacaklarını، olacağın اولاجغڭ); -mış + ek: میش -> مش (sarsılmışlardı);
    - -nız + ek: نیز/نوز -> ڭز (hepinizi هپڭزی، erkeklerinizden)، mastar -ma/-me + nız -> مه‌ڭز (düzeltmenize دوزلتمه‌ڭزه)."""
    if not _TUR_D_EK_ACIK or " " in o:
        return o
    cogul = [m.start() for m in re.finditer("lar", wl)]
    if cogul and re.search("\u0644\u0627\u0631" + _OSM_HARF, o) and \
            not any(_fiil_koku_mu(wl[:i] + "la") or _fiil_koku_mu(wl[:i] + "l") or _fiil_koku_mu(wl[:i]) or wl.startswith("larak", i)
                for i in cogul):
        o = re.sub("\u0644\u0627\u0631(?=" + _OSM_HARF + ")", "\u0644\u0631", o)
    m = re.search("([ae])c[ae][kğ]", wl)
    if m and m.end() < len(wl) and wl[:m.end()] not in kok.ZKOK and wl[:m.end() - 1] + "k" not in kok.ZKOK and re.search("\u0627\u062c\u0627[\u0642\u063a]" + _OSM_HARF, o):
        o = re.sub("\u0627\u062c\u0627([\u0642\u063a])(?=" + _OSM_HARF + ")", "\u0627\u062c\\1", o)
    ms = re.search("s[ae]l[ae]r", wl)
    if ms and _fiil_koku_mu(wl[:ms.start()]):
        o = re.sub("\u0633(?:\u0627|\u0647\u200c?)?\u0644\u0627?\u0631", "\u0633\u0647\u200c\u0644\u0631", o, count=1)
        # şart -sa + çoğul (Hayrat: olsalardı اولسه‌لردی، etselerdi ایتسه‌لردی): dursalardı طورسه‌لردی
    if re.search("m[ıi]ş(l[ae]r|t|d|s)", wl):
        o = re.sub("\u0645\u06cc\u0634(?=" + _OSM_HARF + ")", "\u0645\u0634", o)
    my = re.search("y[ae]n(d[ae]n|d[ae]|[ıi]|[ae]|l[ae]r)$", wl)
    if my and (_fiil_koku_mu(wl[:my.start()]) or "V" in kok.KOK.get(wl[:my.start()], {})):   # gaye+ne değil
        o = re.sub("\u06cc\u0647\u200c?\u0646(?=(?:\u062f\u0646|\u062f\u0647|\u06cc|\u0647|\u0644\u0631)$)", "\u06cc\u0646", o)   # gizleyenden كیزله‌یندن
    me = re.search("[^aeıioöuü]([ae])s[ıi]n[ıi]z$", wl)
    if me and _fiil_koku_mu(wl[:me.start() + 1]):
        o = re.sub("(?<=[^\u0627\u0647\u200c])\u0633\u06cc?\u06ad\u0632$", ("\u0627" if me.group(1) == "a" else "\u0647\u200c") + "\u0633\u06ad\u0632", o)
        # istek -esiniz (Hayrat: bilesiniz بیله‌سڭز، olasınız اولاسڭز): düşünesiniz دوشونه‌سڭز
    mm = re.search("m[ae]n[ıi]z", wl)
    if mm and (_fiil_koku_mu(wl[:mm.start()]) or re.search("[^aeıioöuü]m[ae]$", wl[:mm.start()])):
        # mastar + -nız (Hayrat: olmanız اولمه‌ڭز، buyurmanızı بویورمه‌ڭزی، çalışmanıza): مه‌ڭز
        o = re.sub("\u0645[\u0647\u0627]?\u200c?(?:\u06ad|[\u06cc\u0648]?\u0646[\u06cc\u0648])\u0632", "\u0645\u0647\u200c\u06ad\u0632", o)
    mz = re.search("(?<=[aeıioöuüâîû])[ıiuü]?n[ıiuü]z(?=[a-ln-zçğıöşü])", wl)
    if mz and mz.start() >= 3 and not re.search("n[ıiuü]z[ıi]?m", wl) and \
            not any(wl[:L] in kok.ZKOK for L in range(mz.end(), len(wl) + 1)):   # -izm, boynuz, beniz, deniz, nizam değil
        if re.search("m[ae]n[ıi]z[a-zçğıöşü]", wl):
            o = re.sub("\u0645[\u0647\u0627]?\u200c?\u0646[\u06cc\u0648]\u0632(?=" + _OSM_HARF + ")", "\u0645\u0647\u200c\u06ad\u0632", o)
        o = re.sub("([\u06cc\u0648]?)\u0646[\u06cc\u0648]\u0632(?=" + _OSM_HARF + ")", "\\1\u06ad\u0632", o)
    if re.search("ğ[ıiuü]n[ıiuü]z", wl):
        o = re.sub("([\u0643\u063a\u06af])\u06cc(\u06ad\u0632)", "\\1\\2", o)   # -ğiniz كڭز (Hayrat: ettiğiniz ایتدیگڭز)
    return o


_TUR_D_EK_ACIK = __import__("os").environ.get("OSM_TUR_D_EK", "1") != "0"
_HARF_SONRA = re.compile("\u0647(?=[\u0621-\u064a\u067e\u0686\u0698\u06a9\u06ad\u06af\u06cc])")


def _kuyruk_he(o: str, latin: str) -> str:
    """Tur G2: bilesik fiil kuyrugu (etmemek, edilmeyi) unlu he kuralini alir; Hayrat'ta kuyrugun kendisi varsa ve yalniz ZWNJ ile
    ayriliyorsa Hayrat yazimi (hapsetmemek)."""
    l = turkish_lower(latin)
    if l in dictionary.HAYRAT_ANAHTAR:
        h = dictionary.lookup_exact(l)
        if h and h[0].replace("\u200c", "") == o.replace("\u200c", ""):
            return h[0]
    return _unlu_he(o, latin)


def _unlu_he(o: str, latin: str) -> str:
    """Tur D: ünlü (e/a) okunan he, arkasından harf gelince bitişmez (Hayrat ە; Türkçe ek sınırında 35.243 ە / 1.100 bitişik):
    توبه‌لری، قبله‌سنه، صدقه‌دن، كیزله‌مه‌لری. Ünsüz h (Allah'ın، günahları، fıkhı، şehir) bitişik kalır: Latin'deki h sayısı kadar ه/ح/خ
    ünsüz sayılır, baştan sırayla; fazlası ünlüdür. Hayrat'taki tam kelimeye dokunulmaz (tek ölçü). OSM_UNLU_HE=0 kapatır."""
    if not _UNLU_HE_ACIK or "\u0647" not in o or " " in o:
        return o
    l = turkish_lower(latin).replace("’", "'")
    if l in dictionary.HAYRAT_ANAHTAR:
        return o
    unsuz = l.count("h") - o.count("\u062d") - o.count("\u062e")
    out, i = [], 0
    for j, c in enumerate(o):
        out.append(c)
        if c == "\u0647":
            if unsuz > 0:
                unsuz -= 1
            elif _HARF_SONRA.match(o, j):
                out.append("\u200c")
    return "".join(out)


_UNLU_HE_ACIK = __import__("os").environ.get("OSM_UNLU_HE", "1") != "0"


# ---- Tur B (13 Ekim): ek-fiil (i-) ekleri isimden sonra ayrı yazılır (Hayrat): -(y)ken یكن/كن، -(y)se/-(y)sa یسه/سه، -(y)seniz یسه‌ڭز،
# -(y)iz/-(y)ız ییز/یز. Gövde sözlükte (kök + ek olarak) bulunmalı; fiil gövdesi (gelirken, olursa) kural motorunda kalır.
_EK_FIIL = [("yseniz", "یسه\u200cڭز"), ("ysanız", "یسه\u200cڭز"), ("yken", "یكن"), ("ysem", "یسه\u200cم"), ("ysam", "یسه\u200cم"),
            ("yse", "یسه"), ("ysa", "یسه"), ("yiz", "ییز"), ("yız", "ییز"), ("ken", "كن")]


def _fiil_koku_mu(r: str) -> bool:
    if len(r) < 2:
        return False
    return bool(dictionary.lookup_exact(r + "mak") or dictionary.lookup_exact(r + "mek") or "V" in kok.KOK.get(r, {}))


_NIZ_SONRA = {"": "", "ı": "\u06cc", "i": "\u06cc", "u": "\u06cc", "ü": "\u06cc", "a": "\u0647", "e": "\u0647",
              "da": "\u062f\u0647", "de": "\u062f\u0647", "dan": "\u062f\u0646", "den": "\u062f\u0646",
              "ın": "\u06ad", "in": "\u06ad", "un": "\u06ad", "ün": "\u06ad", "la": "\u0644\u0647", "le": "\u0644\u0647",
              "dır": "\u062f\u0631", "dir": "\u062f\u0631", "dur": "\u062f\u0631", "dür": "\u062f\u0631"}


def _emir_in(wl: str, buyuk: bool = False):
    """Tur C: sözlükte olmayan kelime = fiil kökü (ünsüzle biten) + -ın/-in/-un/-ün: 2. çoğul emir ڭ (Hayrat: girin كیرڭ، bakın باقڭ).
    Kök kök sözlüğünde (faydalan فائده‌لان) ya da sözlükte -mak/-mek ile (in-, uy-). İlgi eki de ünsüzden sonra ڭ: yazım aynı."""
    m = re.match(r"^(.+[^aeıioöuüâîû])[ıiuü]n$", wl)
    if not m or dictionary.lookup_with_suffix(wl)[0]:
        return None
    r = m.group(1)
    v = kok.KOK.get(r, {}).get("V") or (kok._turev(r) or {}).get("V")
    if v:
        return v[0] + "\u06ad"
    if len(r) == 2 and _fiil_koku_mu(r) and wl not in kok.ZKOK and not buyuk:   # irin (isim), Asın (özel ad) değil
        return rules.transliterate_word(r) + "\u06ad"
    return None


def _genis_zaman(wl: str) -> bool:
    """Tur C: fiil kökü + geniş zaman -r/-ar/-er + kişi/şart eki (kıl+ar+sa, cevapla+r+ız, anla+r+sa). Çoğul -lar/-ler değil."""
    m = re.match(r"^(.+?)([ae]?)r(sa|se|ız|iz|sak|sek|sanız|seniz|sam|sem|sın|sin|sınız|siniz|ım|im|ken)$", wl)
    if not m:
        return False
    return _fiil_koku_mu(m.group(1) + m.group(2)) or (bool(m.group(2)) and _fiil_koku_mu(m.group(1)))


def _ek_fiil(wl: str, repl):
    if __import__("os").environ.get("OSM_EK_FIIL", "1") == "0":
        return None
    m = re.match(r"(.{3,}(?:lar|ler))([ıi]z)$", wl)
    if m and not _genis_zaman(wl):     # Tur C: cevapla+r+ız fiil (جوابلارز)، çoğul + ız değil
        h, _ = dictionary.lookup_with_suffix(m.group(1))
        go = _ek_duzelt(repl(_Eslesme(m.group(1))), m.group(1)) if h else ""
        if go.endswith("\u0644\u0631") and " " not in go:
            return go + "\u0632"         # çoğul + -ız (Hayrat): olanlarız اولانلرز
    m = re.match(r"(.{2,}[^aeıioöuüâîûy])([ıiuü]z)$", wl)
    if m and not re.search(r"(s[ıiuü]z|[ıiuü]m[ıiuü]z|[ıiuü]n[ıiuü]z)$", wl) and not re.search(r"[aeıioöuüâîû][nm]$", m.group(1)):
        h = dictionary.lookup_exact(m.group(1))
        if h and h[1] in ("ar", "fa", "ar-fa", "fa-ar") and " " not in h[0] and "\u060c" not in h[0] \
                and not h[0].endswith(("\u06ad", "\u0645")):
            return h[0] + "\u0632"      # Tur C: Arapça/Farsça isim + -ız/-iz (Hayrat): muhtâcız محتاجز، hazırız حاضرز، aitiz عائدز
    for ek, yaz in _EK_FIIL:
        if not wl.endswith(ek) or len(wl) - len(ek) < 3:
            continue
        g = wl[:-len(ek)]
        if ek[0] == "y" and g[-1] not in "aeıioöuü":
            continue
        if re.search(r"(m[ae]|m[ae]l[ıi]|[ae]c[ae]k|[ıiuü]?yor)$", g):
            continue                      # fiil gövdesi (alama-yız, katmalı-yız): eski yol
        if ek == "ken" and (g[-1] in "aeıioöuü" or re.search(r"(r|z|m[ae]z|yor|m[ıiuü]ş|d[ıiuü]|t[ıiuü]|ac[ae]k|ec[ae]k)$", g)):
            continue                      # fiil + ken (gelirken, yapmazken, giderken) eski yol
        h, ekler = dictionary.lookup_with_suffix(g)
        if not h or (not ekler and h[1] == "tr" and len(g) < 4):
            continue
        if rules._fiil_ayir(g):
            continue
        go = _ek_duzelt(repl(_Eslesme(g)), g)
        if not go or " " in go:
            continue
        ara = "\u200c" if go.endswith(("\u0647", "\u0627", "\u062f", "\u0631", "\u0632", "\u0648")) and yaz[0] != "\u0643" else ""
        if go.endswith("\u0647") and yaz[0] != "\u0643":
            ara = "\u200c"
        return go + ara + yaz
    return None


# ---- -ca/-ce/-ça/-çe eki (Hayrat: ek her zaman جه; devletçe دولتجه، ahlâkça اخلاقجه، Osmanlıca عثمانلیجه) ----
_CA_SONRASI = sorted(["", "sı", "si", "ya", "ye", "dan", "den", "da", "de", "nın", "nin", "yı", "yi", "sına", "sine",
                      "sını", "sini", "sının", "sinin", "sında", "sinde", "sından", "sinden", "dır", "dir"],
                     key=len, reverse=True)
_CA_SERT = "çfhkpsşt"


def _ca_eki(wl: str):
    """Sözlükte olmayan kelime = sözlükteki kök + -ca/-ce (+ ek). Kökün kendi yazımı + جه (+ ara boşluk + ek).
    Kelimenin kendisi sözlükteyse (bahçe, derece, tarihçe) ya da fiil -dıkça/-ınca ise None (eski yol)."""
    if len(wl) < 5 or dictionary.lookup_exact(wl):
        return None
    for r in _CA_SONRASI:
        if r and not wl.endswith(r):
            continue
        govde = wl[:len(wl) - len(r)] if r else wl
        m = re.fullmatch(r"(.{3,})([cç])([ae])", govde)
        if not m:
            continue
        kok = m.group(1)
        if dictionary._get(govde) or re.search(r"[dt][ıiuü]k$", kok):
            continue
        if (m.group(2) == "ç") != (kok[-1] in _CA_SERT):
            continue                      # ses uyumu: hakça, devletçe; Osmanlıca, sabırca
        h = dictionary._get_soft(kok)
        if not h:
            continue
        kok_yazi = h[0]
        if re.search(r"[ıiuü]n$", kok):
            if not kok_yazi.endswith("\u06ad"):
                continue                  # fiil -ınca (yazınca) kural motorunda
            kok_yazi = kok_yazi[:-1] + "\u0646"   # iyelik + n + ce: ilmince علمنجه، hükmünce حكمنجه
        yazi = kok_yazi + ("\u200c" if kok_yazi.endswith("\u0647") else "") + "\u062c\u0647"   # ailece عائله‌جه
        if r:
            ek = rules.ekleri_yaz(govde, [r], [], rules._harmony_class(wl))
            yazi += "\u200c" + ek.lstrip("\u200c")   # bitişmeyen he + ara boşluk: عثمانلیجه‌دن
        return yazi
    return None


# ---- Arapça -en zarfları (tenvin; Hayrat: -ten 1.217 kez تًا، he ile biten kökte 230 kez ةً) ----
def _tenvin_zarf(wl: str):
    """Sözlükte olmayan kelime = sözlükteki Arapça kök + en: kök + ًا (zâhiren ظاهرًا، hakîkaten حقیقتًا);
    kök + ten ve kök he ile bitiyorsa ةً (maddeten مادّةً). Türkçe ek ya da fiilse None."""
    if len(wl) < 6 or dictionary.lookup_exact(wl) or rules._fiil_ayir(wl):
        return None
    m = re.fullmatch(r"(.{3,}?)en", wl)
    if not m:
        return None
    kok = m.group(1)
    if wl.endswith(("ken", "sen", "rden")) or dictionary._get(wl[:-1]):
        return None                       # derken, dersen, nerden; desise+n, talebe+n
    for ek in ("den", "dan", "ten", "tan", "nden", "ndan"):
        if wl.endswith(ek) and len(wl) - len(ek) >= 2 and (dictionary._get(wl[:-len(ek)])
                                                            or dictionary.lookup_with_suffix(wl[:-len(ek)])[0]):
            return None                   # ayrılma eki: birden, şeyden, seneden
    if re.search(r"(?:[ıiuü][lnr]|el|er|ar|ür|ir|ıl|il|ul|ül|t[ıiuü]r|d[ıiuü]r)$", kok) and not dictionary._get(kok + "e"):
        if dictionary.lookup_with_suffix(kok + "mek")[0] or dictionary.lookup_with_suffix(kok + "mak")[0] \
                or rules._fiil_ayir(kok + "mek") or rules._fiil_ayir(kok + "mak"):
            return None                   # Türkçe fiil sıfatı: yükselen, ekilen, içiren
    if dictionary._get(kok[:-1] + "mek") or dictionary._get(kok[:-1] + "mak") or dictionary._get(kok + "mek") \
            or dictionary._get(kok + "mak"):
        return None                       # Türkçe fiil: öğreten, işleten
    if kok.endswith("t") and len(kok) >= 4:
        h = dictionary._get(kok[:-1])     # madde + ten -> مادّةً
        if h and h[0].endswith("\u0647"):
            return h[0][:-1] + "\u0629\u064b"
    h = dictionary._get(kok)
    if not h or kok[-1] in "aeıioöuüâîû":
        return None
    y = h[0]
    if " " in y or not re.search("[\u0621-\u064a]$", y) or y.endswith(("\u06cc", "\u0648", "\u0627", "\u0647")):
        return None
    return y + "\u064b\u0627"


# ---- Hayrat'tan öğrenilen ek sonu kuralları (tools/hayrat_ek_ogren.py; sözlükte olmayan kelimeler) ----
def _ek_kurallarini_yukle():
    import os
    from pathlib import Path
    if os.environ.get("OSM_EK_KURAL", "1") == "0":
        return {}
    dosya = Path(os.environ.get("HAYRAT_EK_KURAL") or Path(__file__).parent.parent / "data" / "hayrat_ek_kurallari.tsv")
    kural = {}
    if dosya.exists():
        for satir in open(dosya, encoding="utf-8"):
            if satir.startswith("#"):
                continue
            p = satir.rstrip("\n").split("\t")
            if len(p) >= 3:
                if "\u0651" in p[2].replace("\u0644\u0651\u0647", "") and "\u0651" not in p[1]:
                    continue                  # Tur C: ek sonu kuralı şedde eklemez (şedde kökündür: akdine عقدّینه değil)
                kural.setdefault(p[0], []).append((p[1], p[2]))
    for v in kural.values():
        v.sort(key=lambda x: -len(x[0]))
    return kural


_EK_KURALLARI = _ek_kurallarini_yukle()


_BITISMEZ_HARF = set("\u0627\u0622\u062f\u0630\u0631\u0632\u0698\u0648")   # ا آ د ذ ر ز ژ و
_UNSUZ_HARF = {"b": "\u0628", "c": "\u062c", "ç": "\u0686", "d": "\u062f\u0637\u0636", "f": "\u0641", "g": "\u0643\u063a",
               "ğ": "\u063a\u0643", "h": "\u062d\u0647\u062e", "j": "\u0698", "k": "\u0643\u0642", "l": "\u0644", "m": "\u0645",
               "n": "\u0646\u06ad", "p": "\u067e\u0628", "r": "\u0631", "s": "\u0633\u0635\u062b", "ş": "\u0634",
               "t": "\u062a\u0637\u062f", "v": "\u0648", "z": "\u0632\u0630\u0636\u0638"}
_IMIZ_RE = re.compile(r"([^aeıioöuüâîû'])([ıiuü])([mn])[ıiuü]z")


def _imiz_yazimi(l: str, osm: str) -> str:
    """Ünsüzden sonra -ımız/-ınız (Hayrat'ta 36 bin geçiş, harfe göre %95-100 tutarlı): kökün son harfi bitişmeyen harfse (ا د ذ ر ز ژ و)
    ya da kök y ile bitiyorsa araya ی yazılır (قراریڭزی، سندیمز، لریڭز، سویله‌مه‌ییڭز); bitişen harften sonra yazılmaz (اكمكمز، قلبڭز).
    Fiil emri (-ınız, kelime sonunda) her zaman ی: geçiniz كچیڭز، bakınız باقیڭز. Yalnız sözlükte olmayan kelimelerde (sonda)."""
    m = None
    for m in _IMIZ_RE.finditer(l):
        pass
    if not m:
        return osm
    ek = "\u0645\u0632" if m.group(3) == "m" else "\u06ad\u0632"
    i = osm.rfind(ek)
    if i < 2:
        return osm
    var = osm[i - 1] == "\u06cc"
    k = i - 2 if var else i - 1
    while k > 0 and osm[k] in "\u200c\u0651":
        k -= 1
    harf = osm[k]
    if harf not in _UNSUZ_HARF.get(m.group(1), ""):
        return osm                    # kökün son harfi Latin ünsüze uymuyor: ünlüyle biten kök (kapımız قاپومز، arzunuz) ya da y (köyümüz)
    emir = m.group(3) == "n" and l.endswith(m.group(0)) and \
        bool(dictionary.lookup_exact(l[:m.start(2)] + "mak") or dictionary.lookup_exact(l[:m.start(2)] + "mek"))
    ister = emir or harf in _BITISMEZ_HARF
    if ister and not var:
        return osm[:i] + "\u06cc" + osm[i:]
    if var and not ister:
        return osm[:i - 1] + osm[i:]
    return osm


# Kelime sonunda ünsüz + iyelik ı + n'li hâl eki (Hayrat sayımı, bitişmeyen harften sonra ی / bitişen harften sonra ی):
# -ını 3329:630 / 88:19281, -ına 5064:108 / 1737:18855, -ının 1139:714 (karışık: dokunulmaz) / 206:5631.
_IYELIK_SON = ((re.compile(r"([^aeıioöuüâîû'])[ıiuü]n[ıiuü]$"), "\u0646\u06cc", True),
               (re.compile(r"([^aeıioöuüâîû'])[ıiuü]n[ae]$"), "\u0646\u0647", True),
               (re.compile(r"([^aeıioöuüâîû'])[ıiuü]n[ıiuü]n$"), "\u0646\u06ad", False))


def _iyelik_hal_yazimi(l: str, osm: str) -> str:
    for desen, ek, iki_yon in _IYELIK_SON if _IYELIK_SON_ACIK else ():
        m = desen.search(l)
        if not m or re.search(r"l[ae]r[ıi]n", l[m.start(1):]) or not osm.endswith(ek) or len(osm) < len(ek) + 2:
            continue
        kok = l[:m.start(1) + 1]
        nkok = dictionary.lookup_exact(l[:m.start(1) + 3])
        if not (dictionary._get_soft(kok) or dictionary._derin_kok_hit(kok)) or (nkok and nkok[0].endswith("\u0646")):
            return osm                    # kök sözlükte yoksa ya da -n ile biten kök varsa ünlü kökün kendisi: hırçın+ı, miskin+i, kadın+ın
        i = len(osm) - len(ek)
        var = osm[i - 1] == "\u06cc"
        k = i - 2 if var else i - 1
        while k > 0 and osm[k] in "\u200c\u0651":
            k -= 1
        if osm[k] not in _UNSUZ_HARF.get(m.group(1), ""):
            return osm
        ister = osm[k] in _BITISMEZ_HARF
        if ister and not var and iki_yon:
            return osm[:i] + "\u06cc" + osm[i:]
        if var and not ister:
            return osm[:i - 1] + osm[i:]
        return osm
    return osm


_IYELIK_SON_ACIK = __import__("os").environ.get("DENEME_IYELIK", "1") != "0"


def _cift_harf(o: str) -> int:
    """Ara boşlukla ya da bitişik iki ه (ه‌ه، هه) sayısı."""
    return len(re.findall("\u0647\u200c?\u0647", o))


def _hayrat_ek_kurali(w: str, o: str) -> str:
    """En uzun Latin son ek, sonra en uzun çevirici sonu; ara boşluk (ZWNJ) eşleşmede sayılmaz."""
    for L in range(min(8, len(w) - 2), 1, -1):
        for t1, t2 in _EK_KURALLARI.get(w[-L:], ()):
            for k in range(len(t1), len(t1) + 4):
                if k <= len(o) and o[-k:].replace("\u200c", "") == t1:
                    return o[:-k] + t2
    return o


# "-in/-ün" ile biten Arapça kökler: din+den دیندن (iyelik eki sanılıp yesi silinmesin)
_IN_ILE_BITEN_KOKLER = {"din", "yemin", "metin", "telkin", "zemin", "emin", "mümin", "mü'min", "yakîn", "tayin", "ta'yin",
                        "temin", "tahsin", "tezyin", "tebyin", "miskin", "hazin", "tekvin", "tazmin", "takdim"}

_SIK_FIIL_KOKLERI = {"ol", "et", "ed", "al", "ver", "gel", "git", "bil", "gör", "yap", "bul", "kal", "bak", "bırak", "de", "ye",
                     "iste", "söyle", "oku", "yaz", "çalış", "anla", "sor", "tut", "çık", "gir", "ver", "düşün", "kork"}


def _matbaa_ekleri(latin: str, osm: str) -> str:
    """Matbaa yazımında birkaç Türkçe ek: -ıyor/-iyor (ünsüzden sonra) ییور (ediyor ایدییور, geliyor كلییور);
    -ınız/-iniz ڭز (bakınız باقیڭز)."""
    l = turkish_lower(latin)
    # -yor: fiil kökü ünlüyle bitiyorsa o ünlü (iste-yor ایسته‌یور، sakla-yor صاقلایور، oku-yor اوقویور), ünsüzle bitiyorsa
    # -ıyor/-iyor ییور (ایدییور), -uyor/-üyor ویور (گورویور) — Risale matbaa nüshası
    m = re.match(r"^(.+?)([ıiuü])yor", l)
    if m and "یور" in osm and "ییور" not in osm and "ویور" not in osm and "هیور" not in osm and "ایور" not in osm:
        x, v = m.group(1), m.group(2)
        unsuz_kok = bool(dictionary.lookup_exact(x + "mak") or dictionary.lookup_exact(x + "mek"))   # gör-mek, ol-mak
        kok_unlu = None if unsuz_kok else \
            next((u for u in "aeıiuü" if dictionary.lookup_exact(x + u + ("mak" if u in "aıu" else "mek"))), None)
        if not kok_unlu and x.endswith("m") and v in "ıi" and x[-2:-1] not in "aeıioöuüâîû":
            kok_unlu = "a" if v == "ı" else "ı"              # olumsuz -mı-yor: قالمایوردی، طانیمایور; -mi-yor: بیلمییور
        if not kok_unlu and re.search(r"[^aeıioöuüâîû][lrnm]$", x):
            # ünsüz + l/r/n/m ile biten kök ünlüyle biter: sakl-a, bekl-e, söyl-e, titr-e
            son_unlu = next((c for c in reversed(x) if c in "aeıioöuüâîû"), "a")
            kok_unlu = "a" if son_unlu in "aıouâû" else "e"
        if kok_unlu:
            harf = {"a": "ا", "e": "ه", "ı": "ی", "i": "ی", "u": "و", "ü": "و"}[kok_unlu]
        elif x[-1:] not in "aeıioöuüâîû":
            harf = {"ı": "ی", "i": "ی", "u": "و", "ü": "و"}[v]
        else:
            harf = ""
        if x == "ol":
            harf = ""                                    # oluyor: matbaada اولیور
        if harf:
            i = osm.rfind("یور")                      # kökteki "یور" değil, ekteki (yürüyor)
            osm = osm[:i] + harf + osm[i:]
    if re.search(r"[ıi]n[ıi]z$", l) and osm.endswith("ینیز"):
        osm = osm[:-4] + "یڭز"
    # -sen/-san (şart, 2. tekil) سهڭ: istersen ایسترسهڭ, görsen گورسهڭ (sözlükte olmayan fiil çekimlerinde)
    if re.search(r"s[ae]n$", l) and len(l) >= 5 and osm.endswith("سن") and not dictionary.lookup_with_suffix(l)[0]:
        osm = osm[:-2] + "سهڭ"
    # aŋla-, diŋle-, beŋze- (eski ñ): آڭلامق، دیڭله، بڭزر
    for lat, eski, yeni in (("anla", "آنلا", "آڭلا"), ("anlı", "آنل", "آڭل"), ("dinle", "دینله", "دیڭله"),
                            ("dinle", "دینل", "دیڭله") if not l.startswith("dinler") else ("dinle", "\0", ""), ("benze", "بنز", "بڭز")):
        if l.startswith(lat) and osm.startswith(eski) and not re.match(r"anlam(?!a)", l):   # anlam, anlamı (isim) değişmez
            osm = yeni + osm[len(eski):]
    # geniş zaman -ir/-ır, kök r ile bitiyorsa (ver-ir, çevir-ir, bildir-ir): ویرر، چویرر، بیلدیرر (Risale)
    if (re.search(r"[iı]r[ıi]r(ler|lar)?$", l) or re.match(r"^ver[ıi]r(ler)?$", l)) and re.search(r"ریر(لر)?$", osm):
        osm = re.sub(r"ریر(لر)?$", r"رر\1", osm)
    # Arapça -iyye/-iye sıfatları tek ye: الهیه، ایمانیه، معنویه
    m_iy = re.search(r"([a-zçğıöşüâîû']{3,})iy?ye", l)
    if m_iy and "ییه" in osm:
        g = m_iy.group(1)
        taban = dictionary.lookup_exact(g + "i")
        _ak = ("ar", "fa", "ar-fa", "fa-ar", "sozlukler")
        _sapkali = dictionary.lookup_exact(g + "î")
        arapca = bool(_sapkali and _sapkali[1] in _ak) or bool(taban and taban[1] in _ak)
        if arapca or (not taban and len(g) >= 4):   # Arapça nisbe (ilâhî, ezelî); şimdi+ye, kişi+ye Türkçe: dokunma
            osm = osm.replace("ییه", "یه")
    # ayrılma/bulunma eki -tan/-ten, -ta/-te matbaada دن/ده: اوزاقدن، میكروپدن
    if re.search(r"[pçtksşhf]t[ae]n$", l) and re.search(r"(تان|تن)$", osm) and len(l) > 4 \
            and not (dictionary.lookup_exact(l) and dictionary.lookup_exact(l)[0] == osm):   # yaratan, tutan; Tur G: bostan, destan sözlükte
        osm = re.sub(r"(تان|تن)$", "دن", osm)
    # ettirgen -dir/-tir: یتیشدیرمك، چالیشدیرییور، ایتدیرن
    if re.search(r"(ş|t)t[ıiuü]r", l):
        osm = osm.replace("شتیر", "شدیر").replace("تتیر", "تدیر").replace("شتور", "شدیر").replace("تتور", "تدیر")
    # -daki/-deki/-taki/-teki: دهكی (Risale: اصلندهكی، عالمدهكی)
    if re.search(r"[dt][ae]ki$", l):
        osm = re.sub(r"(داكی|دكی|تاكی|تكی)$", "دهكی", osm)
    # demek, vermek kökleri tarihî yazımla (kural motorunun çözemediği çekimlerde): dedim دیدم، verdiler ویردیلر
    if l.startswith("ded") and osm.startswith("دد"):
        osm = "دید" + osm[2:]
    if re.match(r"^deme(d|z|s|y|l|m[ae]|k[ae]n|n)", l) and osm.startswith("دم") and not osm.startswith("دمی") and \
            not dictionary.lookup_with_suffix(l)[0]:
        osm = "دی" + osm[1:]                               # Tur C: demedikçe دیمه‌دكجه، demeden دیمه‌دن (Hayrat)
    if re.match(r"^ver(d|m|i|e|s|y|l)", l) and not l.startswith(("verem", "vergi")) and osm.startswith("ور") and not osm.startswith("ویر"):
        osm = "ویر" + osm[2:]
    # -maya/-meye (mastar + yönelme): قورتارمغه، گیتمگه (Risale)
    if re.search(r"(?<=[^aeıioöuüâîû])m(aya|eye)$", l) and re.search(r"م(ایه|یه|هیه)$", osm):
        osm = re.sub(r"م(ایه|یه|هیه)$", "مغه" if l.endswith("aya") else "مگه", osm)
    # şart -sam/-sem/-sak/-sek/-sanız/-seniz/-salar/-seler: ایتسهم، بیراقسهق، چالیشسهڭز
    m_s = re.search(r"s(am|em|ak|ek|anız|eniz|alar|eler)$", l)
    if m_s and len(l) >= 5 and not dictionary.lookup_with_suffix(l)[0] and (
            rules._fiil_ayir(l) or dictionary.lookup_exact(l[:m_s.start()] + "mak") or dictionary.lookup_exact(l[:m_s.start()] + "mek")
            or l[:m_s.start()] in _SIK_FIIL_KOKLERI):
        for eski, yeni in (("سام", "سهم"), ("ساق", "سهق"), ("سم", "سهم"), ("سق", "سهق"), ("سك", "سهك"), ("سانیز", "سهڭز"), ("سنیز", "سهڭز"),
                           ("سڭز", "سهڭز"), ("سالر", "سهلر"), ("سلر", "سهلر")):
            if osm.endswith(eski):
                osm = osm[: -len(eski)] + yeni
                break
    # -imiz/-ımız (iyelik, 1. çoğul) yesiz: ایشمزله، بیلدیكمزدن، برائتمزه
    if re.search(r"[ıiuü]m[ıiuü]z", l):
        osm = osm.replace("یمیز", "مز").replace("یموز", "مز")
    # -lerimi/-lerime: ye kalır (اثرلریمی، كتابلریمی)
    if re.search(r"l[ae]r[ıi]m(i|ı|e|a|in|ın|de|da|den|dan)$", l):
        osm = re.sub(r"لرم(ی|ه|ڭ|ده|دن)$", r"لریم\1", osm)
    # -cı/-ci ünsüzden sonra ج: حریتجی، خدمتجی
    if re.search(r"[ts]ç[ıi]", l):
        osm = osm.replace("تچی", "تجی").replace("سچی", "سجی")
    # ünlüyle biten fiil kökünün ünlüsü yazılır: iste-mez ایسته‌مز، bekle-yen بكله‌ین، söyle-diğim سویله‌دیگم
    for lat, kok in (("iste", "ایست"), ("bekle", "بكل"), ("söyle", "سویل")):
        if l.startswith(lat) and l[len(lat):len(lat) + 1] != "r" and osm.startswith(kok) and not osm.startswith(kok + "ه"):
            osm = kok + "ه" + osm[len(kok):]
    # yeterlik -ebil/-abil ve -eme/-ama (ünsüzden sonra): گله‌بیلیر، بیله‌مز، یتیشه‌مزسڭ (Risale)
    _abil_h = dictionary.lookup_with_suffix(l)[0] if re.search(r"[^aeıioöuüâîû][ea]bil", l) else None
    if re.search(r"[^aeıioöuüâîû][ea]bil", l) and "بیل" in osm and not (_abil_h and _abil_h[1] not in ("tr",)):
        # Arapça kelimede -abil- ek değil (kabile قبیله، Tur A)
        i = osm.find("بیل", 1)
        if i > 0 and osm[i - 1] not in "اه\u200c":
            osm = osm[:i] + ("ا" if re.search(r"[^aeıioöuüâîû]abil", l) else "ه") + osm[i:]
    if re.search(r"[^aeıioöuüâîû][ea]m[ea]z", l) and not dictionary.lookup_with_suffix(l)[0] \
            and not l.startswith(("yem", "dem")):
        i = osm.rfind("مز")
        if i > 0 and osm[i - 1] not in "اه\u200c":
            osm = osm[:i] + ("ا" if re.search(r"[^aeıioöuüâîû]amaz", l) else "ه") + osm[i:]
    # 2. kişi -sın/-sin (fiilde), -sınız: دوشرسڭ، گورونورسڭ، ییمزسڭز
    # geniş zaman 2. tekil (düşersin, görünürsün, yetişemezsin) سڭ; 3. tekil emir (geçirsin, çıkarsın, yazsın) سین kalır
    if re.search(r"([eüu]r|m[ea]z)s[ıiuü]n$", l):
        osm = re.sub(r"(سین|سون|سن)$", "سڭ", osm)
    elif re.search(r"([eüuıia]r|m[ea]z)s[ıiuü]n[ıiuü]z$", l):
        osm = re.sub(r"(سینیز|سونوز|سیڭز|سنیز)$", "سڭز", osm)
    # -uyla/-üyle (iyelik + ile): نوریله، یولیله
    _uy = dictionary.lookup_exact(l[:-3]) if re.search(r"[^aeıioöuüâîû][uü]yl[ae]$", l) else None
    if re.search(r"[^aeıioöuüâîû][uü]yl[ae]$", l) and osm.endswith("ویله") and not (_uy and _uy[0].endswith("\u0648")):
        osm = osm[:-4] + "یله"     # Tur C: u ile biten isim + -yla değil (ordu+yla اوردویله)
    # ayrılma eki -dan matbaada دن (sözlükte olmayan kelimede): قیزدن
    if l.endswith("dan") and osm.endswith("دان") and not dictionary.lookup_exact(l):
        osm = osm[:-3] + "دن"
    # kazan-: قزانمق؛ ön (eski ñ): اوڭنده
    if l.startswith("kazan") and osm.startswith("قازان"):
        osm = "قزان" + osm[5:]
    if re.match(r"^ön(ü|e|de|den|ce|üm|ün|ler)", l) and osm.startswith("اون"):   # Tur C: önlerinde
        osm = "اوڭ" + osm[3:]
    # yemek fiili: ییدم، ییمش، ییمز، ییمه‌یور (yedi "7" ve yer "mekân" belirsiz, dokunulmaz)
    if re.match(r"^ye(dim|dik|diler|miş|mek|mez|miyor|sin|meleri|meli)", l) and osm.startswith("ی") and not osm.startswith("یی"):
        osm = "ی" + osm
    # geniş zaman 1. kişi -ırım/-iriz: بیلیرم، اولابیلیرز
    if re.search(r"[ıiuü]r[ıiuü]m$", l) and not dictionary.lookup_exact(l):   # durum, korum gibi kelimeler değil
        osm = re.sub(r"(یریم|وروم)$", lambda m: "یرم" if m.group(1) == "یریم" else "ورم", osm)
    elif re.search(r"[ıiuü]r[ıiuü]z$", l) and not dictionary.lookup_exact(l):
        osm = re.sub(r"(یریز|وروز)$", lambda m: "یرز" if m.group(1) == "یریز" else "ورز", osm)
    # olumsuz emir -mesin/-masın: گلمه‌سین، گورمه‌سین
    if re.search(r"m(e|a)s[ıi]n(ler|lar)?$", l):
        osm = re.sub(r"مسین(لر)?$", lambda m: ("مه" if re.search(r"mes[ıi]n", l) else "ما") + "سین" + (m.group(1) or ""), osm)
    # ölüm, ölmek: ئولوم (Risale)
    if l.startswith("öl") and not l.startswith("ölç") and osm.startswith("اول"):   # Tur C: ölçü اولچو (Hayrat), ölüm ئولوم
        osm = "ئو" + osm[2:]
    # parça-: پارچه‌لانمق
    if l.startswith("parça") and osm.startswith("پارچا"):
        osm = "پارچه" + osm[5:]
    if l.startswith("ederek"):
        osm = osm.replace("ایده\u200cرك", "ایدرك", 1)        # Risale: ایدرك
    # -makla/-mekle matbaada مقله/مكله: اولمقله
    if l.endswith(("makla", "mekle")) and osm.endswith(("ماقله", "مكله")):
        osm = osm[:-5] + "مقله" if osm.endswith("ماقله") else osm
    # Farsça -hâne: ماتمخانه
    if "hane" in l and "هانه" in osm and not re.search(r"ş[aâ]h[aâ]ne", l):   # Tur G: şâhâne شاهانه (şah+âne, hane değil)
        osm = osm.replace("هانه", "خانه")
    # -sız/-siz eki matbaada yesiz: sayısız صاییسز, şüphesiz شبهه‌سز
    if re.search(r"s[ıiuü]z(l[ıiuü][kğ]\w*|ca|ce|dır|dir|lar|ler)?$", l) and "سیز" in osm:
        osm = osm[::-1].replace("زیس", "زس", 1)[::-1]
    # iyelik + n'li hâl eki (kural motorundan gelen kelimelerde de): kapısında قاپوسنده, yüzünde یوزنده
    _kh, _ks = dictionary.lookup_with_suffix(l)
    _kok = l[: len(l) - len("".join(_ks))] if (_kh and _ks) else ""
    # din+den, zemin+de: "-in" kökün kendi harfleri (iyelik değil); iç+in+den, üst+ün+de ise iyelik
    _kok_n = _kok in _IN_ILE_BITEN_KOKLER and bool(_ks) and _ks[0][:1] in "dt"
    if len(l) >= 6 and not _kok_n and not re.match(r"^(bu|şu|o)n(da|dan|daki|un|lar)", l) and \
            re.search(r"([ıiuü]n(da|de|dan|den|daki|deki)|s[ıiuü]n[ıiuüae]|s[ıiuü]n[ıiuü]n)(d[ıiuü]r|t[ıiuü]r)?$", l):
        osm = re.sub(r"(?<=..)(?:ین|ون)(ده|دن|دهكی|دكی|ی|ه|ڭ)(در)?$", r"ن\1\2", osm)   # Tur C: (?<=..) ev: اونده‌كی، انده‌كی değil
    elif len(l) >= 8 and re.search(r"[ıiuü]n(da|de)ki(ni|nı|ne|na|nde|nda|nden|ndan|nin|nın|ler|lar|leri|ları|lerin|ların|lere|lara)$", l):
        osm = re.sub(r"(?<=..)(?:ین|ون)(دهكی(?:نی|نه|نده|ندن|نڭ|لر|لری|لرڭ|لره))$", r"ن\1", osm)   # Tur C: önlerindekini اوڭلرنده‌كینی
    # 3. tekil emir: fiil kökü + -sın/-sin سین، -sun/-sün سون (Hayrat: etsin ایتسین، olsun اولسون، geçirsin كچیرسین);
    # geniş zaman 2. tekil (bilirsin بیلیرسڭ) dokunulmaz: kökü "bilir" diye bir fiil yok
    m3 = re.search(r"s([ıiuü])n$", l)
    if m3 and osm.endswith("سڭ") and len(l) >= 5:
        kok3 = l[:-3]
        if dictionary.lookup_exact(kok3 + "mek") or dictionary.lookup_exact(kok3 + "mak"):
            osm = osm[:-2] + ("سون" if m3.group(1) in "uü" else "سین")
    return osm


# Arapça harf-i tarif (Türkçe yazımda kesmeli/tireli): Kitâbü't-Tevhîd -> كتاب التوحید, Ebü'l-Hasan -> ابو الحسن,
# bi't-tab -> بالطبع; el-Bakara -> البقره, et-Tevbe -> التوبه, en-Nesefî -> النسفی (güneş harflerinde ses benzeşmesi)
_HARF = "A-Za-zÇçĞğİıÖöŞşÜüÂâÎîÛû"
_TARIF_IZAFET_RE = re.compile(r"(?<![" + _HARF + r"'’])((?:[" + _HARF + r"]+['’])*[" + _HARF + r"]+?)([üuıi])['’]([lstşdrnzc])[-–]([" + _HARF + r"]+(?:['’][" + _HARF + r"]+)*)")
_HARF_I_TARIF_RE = re.compile(r"(?<![" + _HARF + r"'’\-–])([Ee]l|[Aa]l|[Üü]l|[Uu]l|[İi]l|[EeAa][tsşdrnzc])[-–]([" + _HARF + r"]+(?:['’][" + _HARF + r"]+)*)")


def _arapca_kelime(w):
    o = draft_transliterate_sentence(w)
    return "ا" + o[1:] if o.startswith("آ") else o   # harf-i tarifli kelimede medd yok: el-A'râf -> الاعراف


def _izafet_tarif(m):
    kok, harf, sonraki = m.group(1), m.group(3).lower(), m.group(4)
    if not (harf == "l" or harf == turkish_lower(sonraki[:1])):
        return m.group(0)
    k = turkish_lower(kok)
    bas = {"eb": "ابو", "ebu": "ابو", "ebü": "ابو", "ibn": "ابن", "b": "ب", "f": "فی", "l": "ل"}.get(k)
    if bas is None:
        bas = draft_transliterate_sentence(kok)
    ayrac = "" if k in ("b", "l") else " "
    return bas + ayrac + "ال" + _arapca_kelime(sonraki)


def _harf_i_tarif(m):
    on, kelime = turkish_lower(m.group(1)), m.group(2)
    if len(kelime) < 3:            # Âl-i İmrân, Al-i Osman: izafet, harf-i tarif değil
        return m.group(0)
    if not (on in ("el", "al", "ül", "ul", "il") or on[1] == turkish_lower(kelime[:1])):
        return m.group(0)
    return "ال" + _arapca_kelime(kelime)


def _ul_tamlama(m):
    """Vâcib-ül Vücud -> واجب الوجود, Mesneviyy-ül Arabî -> المثنوی العربی (tireli -ül + boşluk + Arapça kelime)."""
    k1, on, k2 = m.group(1), turkish_lower(m.group(2)), m.group(3)
    if len(k2) < 3 or not (on[1] == "l" or on[1] == turkish_lower(k2[:1])):
        return m.group(0)
    return draft_transliterate_sentence(k1) + " ال" + _arapca_kelime(k2)


_UL_TAMLAMA_RE = re.compile(r"(?<![" + _HARF + r"'’])([" + _HARF + r"]+(?:['’][" + _HARF + r"]+)*)[-–]([üuıiÜUIİ][lstşdrnzc])\s+([" + _HARF + r"]+(?:['’][" + _HARF + r"]+)*)")
_EYYUHE_RE = re.compile(r"(?<![" + _HARF + r"])[Ee]yy[üu]h[ea]['’]?l[-–]([" + _HARF + r"]+)")
_MAKRON = str.maketrans({"ā": "â", "ī": "î", "ū": "û", "Ā": "Â", "Ī": "Î", "Ū": "Û"})


def _arapca_tarifler(metin: str) -> str:
    metin = _EYYUHE_RE.sub(lambda m: "ایّها ال" + _arapca_kelime(m.group(1)), metin)   # Eyyühe'l-aziz -> ایّها العزیز
    metin = _UL_TAMLAMA_RE.sub(_ul_tamlama, metin)
    metin = _TARIF_IZAFET_RE.sub(_izafet_tarif, metin)
    return _HARF_I_TARIF_RE.sub(_harf_i_tarif, metin)


# Tur C: et-/ed- çekiminin geçerli başları (ed + ünsüzle başlayan ek olmaz: edikçe, ediklerini değil; edin yalnız emir)
_ET_KUYRUK = re.compile(r"^(et($|m|t|s)|ed(er|ip|en|ec|eb|eg|em|eli|ey|esi|il|iy|iv|inc|ic|iş|in$|iniz$|e$))")
_ET_ISIM_EK = {"ti": "\u062f\u06cc", "tı": "\u062f\u06cc", "tir": "\u062f\u0631", "tır": "\u062f\u0631", "te": "\u062f\u0647",
               "ta": "\u062f\u0647", "ten": "\u062f\u0646", "tan": "\u062f\u0646", "tim": "\u062f\u0645", "tik": "\u062f\u0643"}


_BILESIK_KOK = None


def _bilesik_kok() -> dict:
    """Tur C: sözlükteki (çoğu Hayrat) birleşik fiil kayıtlarından isim kısmının yazımı: arzetti عرض ایتدی -> arz: عرض,
    zikrolunan ذكر اولونان -> zikr: ذكر. Aynı isim için en çok geçen yazım."""
    global _BILESIK_KOK
    if _BILESIK_KOK is None:
        from collections import Counter, defaultdict
        say = defaultdict(Counter)
        for k, v in dictionary.DICTIONARY.items():
            if " " not in v[0] or v[0].count(" ") != 1:
                continue
            isim, fiil = v[0].split(" ")
            m = re.match(r"^([a-zçğıöşüâîû]{2,}?)(et|ed|ol)", k)
            if not m or not fiil.startswith(("\u0627\u06cc", "\u0627\u0648\u0644", "\u0623\u06cc")):
                continue
            if (m.group(2) == "ol") != fiil.startswith("\u0627\u0648\u0644"):
                continue
            say[m.group(1)][isim] += 1
        _BILESIK_KOK = {k: c.most_common(1)[0][0] for k, c in say.items()}
    return _BILESIK_KOK


def _etmekli(kok: str) -> bool:
    """Kök sözlükte "etmek"le birleşik fiil olarak geçiyor mu (zulm: ظلم ایدر، hükm: حكم ایتدی)."""
    for ek in ("etmek", "eder", "etti", "eden", "edip", "edilir", "olunur", "olur"):
        h = dictionary.lookup_exact(kok + ek)
        if h and " " in h[0]:
            return True
    return False
# Tur C: Arapça/Farsça isim + olmak çekimi ayrı yazılır (Hayrat: emrolunan امر اولونان، mahvolur محو اولور، zikrolunan ذكر اولونان)
_OL_KUYRUK = re.compile(r"^ol(un|ur|du|dı|muş|mak|ma|mu|acak|acağ|an|up|sa|sun|ab|ama|ay|abil|unca|duk|duğ|maz|mad|mas|mış)")


def _bilesik_fiil(word: str):
    """Arapça/Farsça isim + etmek/edilmek bitişik yazılmışsa ayrı yazar (Osmanlıca imlâsı):
    halkeden -> خلق ایدن, zanneder -> ظن ایدر, hissedilir -> حس ایدیلیر, fehmetmek -> فهم ایتمك."""
    w = turkish_lower(word)
    for k in range(len(w) - 3, 2, -1):
        kuyruk = w[k:]
        if not kuyruk.startswith(("et", "ed")) or not re.match(r"^(et[mst]|ed[eiı])", kuyruk):
            continue
        if kuyruk.startswith(("edeb", "edep", "edib", "edip")):
            continue
        if not _ET_KUYRUK.match(kuyruk):
            continue                       # Tur C: geçerli et-/ed- çekimi değil (de+medikçe -> dem + edikçe, sad+edindeki değil)
        # -et ile biten isim + hâl eki/ek-fiil (âhiret+te, rahmet+ten, rahmet+tir, mâhiyet+e+dir) fiil değildir
        if re.match(r"^(ette|ete|eti|etin|etle|eten|etten|ettir|ettirler|ettı|edir|edirler)$", kuyruk) or \
                re.match(r"^(ette|etten|etle)", kuyruk):
            continue
        kok = w[:k]
        if kuyruk.startswith("ede") and dictionary.lookup_exact(kok + "e") and \
                (re.match(r"^(d[ae]n?|d[ae]ki|d[ıi]r)$", w[k + 1:]) or dictionary.lookup_with_suffix(w)[0]):
            continue                       # halke+den (حلقه) gibi: isim + ayrılma eki olabilir; Tur C: sözlükte hiç
            #                                bulunmayan kelimede isim + geçersiz ek (hacce+der) ise bileşik fiil (حجّ ایدر)
        _isim = dictionary.lookup_exact(kok + "et")
        _kh = dictionary.lookup_exact(kok)
        if _isim and kuyruk.startswith("et") and _isim[1] in ("ar", "fa", "ar-fa", "fa-ar", "sozlukler") and \
                not (_kh and _kh[1] in ("ar", "fa", "ar-fa", "fa-ar") and not re.search(r"([^aeıioöuüâîû])\1$", kok)) and \
                _isim[0][-1:] in ("\u062a", "\u0629", "\u0637") and " " not in _isim[0] and not _etmekli(kok) and \
                re.match(r"^(t[ıi](r|m|k|n|ler|niz)?|t[ae]n?|t[ae]ki|t[ıi]rler|i|e|in|ine|ini|inde|inden|le|ler\w*)$", w[k + 2:]):
            return _isim[0] + _ET_ISIM_EK.get(w[k + 2:], rules.transliterate_word_with_suffix(w[k + 2:]))
            # Tur C: -et ile biten Arapça isim + ek (ümmet+ti امّتدی، cennet+ti): ümm + etti değil. Yalnız kök sözlükte Arapça/Farsça
            # değilse ya da ikiz ünsüzle bitiyorsa (ümm, cenn); şevk+etti شوق ایتدی، hitab+etti fiil kalır
        if kok[-1] in "aeıioöuüâîû" or (kok.endswith("y") and kok[-2:-1] in "iî"):
            continue                       # İlahiye+den gibi isim çekimi; ünlüyle biten kök birleşik fiil olmaz
        adaylar = [kok]
        if len(kok) >= 3 and kok[-1] == kok[-2]:
            adaylar.append(kok[:-1])       # hiss+etmek -> his, zann+etmek -> zan, redd -> red
        if len(kok) >= 4 and kok[-1] == "t" and kok[-2] not in "aeıioöuüâîû":
            adaylar.append(kok[:-1] + "d")  # Tur C: kast+etmek -> kasd قصد
        for a in adaylar:
            h = dictionary.lookup_exact(a)
            if h and h[1] in ("ar", "fa", "ar-fa", "fa-ar") and len(a) >= 2 and " " not in h[0]:
                isim = _bilesik_kok().get(kok) or h[0]      # Tur C: Hayrat'taki birleşik fiilin isim yazımı (arz عرض، ارض değil)
                if isim == h[0].replace("\u0651", ""):
                    isim = h[0]                                # şedde korunur (ردّ، عدّ، ظنّ)
                if a != kok[:len(a)]:
                    return isim + " " + draft_transliterate_sentence(kuyruk)   # Tur C yeni yol (kast -> kasd): kuyruk tam kelime gibi
                return isim + " " + _kuyruk_he(rules.transliterate_word_with_suffix(kuyruk), kuyruk)   # Tur G2: ZWNJ
    return _ol_bilesik(w)


def _ol_bilesik(w: str):
    """Tur C: Arapça/Farsça isim + olmak bitişik yazılmışsa ayrı (emrolunduğunuz -> امر اولوندیغڭز). OSM_OL_BILESIK=0 kapatır."""
    if __import__("os").environ.get("OSM_OL_BILESIK", "1") == "0":
        return None
    for k in range(len(w) - 3, 2, -1):
        kuyruk = w[k:]
        if not _OL_KUYRUK.match(kuyruk):
            continue
        kok = w[:k]
        if kok[-1] in "aeıioöuüâîû" or dictionary.lookup_exact(w[:k + 2]):
            continue                       # ünlüyle biten isim (kafa+ol değil) ya da "…ol" bir kelime (kontrol, petrol)
        adaylar = [kok] + ([kok[:-1]] if len(kok) >= 3 and kok[-1] == kok[-2] else [])
        bk = _bilesik_kok().get(kok)
        if bk:
            ek = rules.transliterate_word_with_suffix(kuyruk)
            return bk + " " + _kuyruk_he(ek, kuyruk) if ek.startswith("\u0627\u0648\u0644") else None
        for a in adaylar:
            h = dictionary.lookup_exact(a)
            if h and h[1] in ("ar", "fa", "ar-fa", "fa-ar") and len(a) >= 3 and " " not in h[0]:
                ek = rules.transliterate_word_with_suffix(kuyruk)
                if not ek.startswith("\u0627\u0648\u0644"):
                    return None
                return h[0] + " " + _kuyruk_he(ek, kuyruk)   # Tur G2: unlu he bitismez
    return None


class _Eslesme:
    """repl() için WORD_RE eşleşmesi gibi davranan küçük sarmalayıcı."""
    def __init__(self, metin):
        self._m = metin

    def group(self, i=0):
        return self._m


# Kapanan tırnak/parantezden hemen sonra boşluksuz gelen Türkçe ek: “O”dur, “Hak”tan, (Rahman)'a değil
_TIRNAK_EK_RE = re.compile(r"([A-Za-zÇçĞğİıÖöŞşÜüÂâÎîÛû]+(?:['’][A-Za-zÇçĞğİıÖöŞşÜüÂâÎîÛû]+)*)([”\"»\)\]]+)([a-zçğıöşüâîû]{1,9})(?![A-Za-zÇçĞğİıÖöŞşÜüÂâÎîÛû'’])")


_AYRIK_PAREN_ACIK = {"in", "ın", "un", "ün", "nin", "nın", "nun", "nün"}
_AYRIK_PAREN_BOSLUK = _AYRIK_PAREN_ACIK | {"a", "e", "ı", "i", "u", "ü"}
_AYRIK_KESME_BOSLUK = _AYRIK_PAREN_BOSLUK | {"ya", "ye", "yı", "yi", "dan", "den", "tan", "ten", "da", "de", "ta", "te",
                                             "dır", "dir", "dur", "dür", "tır", "tir", "tur", "tür"}


def _ayrik_ek(metin: str, bas: int, wl: str):
    """Önceki kelimeden ayrı düşmüş ek: (sav)'ın, Allah'- tan, (filozoflar) ın, düşenler(in hâli). Ek olarak yazılır, yoksa None.
    Bitişik (kelime'ek, kelime'-ek, kelime'- ek, kelime)ek): her ek dizisi. Boşluklu ya da açılan parantezli durumda yalnız küçük
    harfle başlayan tek ek: kelime' ya / tan / dur, (filozoflar) ın, düşenler(in (kesmeden önce harf, rakam, nokta ya da parantez). Böylece (ya da, (Ya Muhammed, vara' ile, 'İleride,
    (Nun 71/5), Bir şehre (mısran) inin dokunulmaz. -tan/-ten/-ta/-te matbaa yazımıyla د (Rasulullah (sav)'tan -> دن)."""
    if wl == "ki" or not _ek_mi(wl):
        return None
    on = metin[max(0, bas - 4):bas]
    kucuk = metin[bas:bas + 1].islower()
    if re.search(r"[\w).]['\u2019]-?$|['\u2019]-\s$|\)$", on):
        pass
    elif kucuk and wl in _AYRIK_KESME_BOSLUK and re.search(r"[\w).]['\u2019]\s$", on):
        pass
    elif kucuk and wl in _AYRIK_PAREN_BOSLUK and re.search(r"\)\s$", on):
        pass
    elif kucuk and wl in _AYRIK_PAREN_ACIK and re.search(r"\($", on):
        pass
    else:
        return None
    if wl[:1] == "t":
        wl = "d" + wl[1:]
    onceki = re.findall(r"[A-Za-zÇçĞğİıÖöŞşÜüÂâÎîÛû]+", metin[:bas])
    kok = turkish_lower(onceki[-1]) if onceki else wl
    return rules.ekleri_yaz(kok, [], [wl], rules._harmony_class(kok + wl))


def _ek_mi(s: str) -> bool:
    """s bir ya da üst üste en çok üç Türkçe ekten mi oluşuyor (dur, tan, nın, ının, da...)."""
    if not s:
        return False
    eks = dictionary.LOOKUP_SUFFIXES

    def bol(x, n):
        if not x:
            return True
        if n == 0:
            return False
        return any(x.startswith(e) and bol(x[len(e):], n - 1) for e in eks)
    return bol(s, 3)


def _ek_duzelt(w: str, latin: str = None) -> str:
    """-yla/-yle (ile) ییله -> یله (kuvvetiyle قوّتیله). Tur C: Latin kelime -yla/-yle ile bitmiyorsa dokunulmaz (yıl+a ییله، یله değil)."""
    if latin is not None and not turkish_lower(latin).endswith(("yla", "yle")):
        return w
    return w[:-4] + "یله" if w.endswith("ییله") else w



def _merge_orphan_numbers(text: str) -> str:
    """Sadece 'N.' veya 'N)' iceren satirlari, hemen sonraki satirla
    birlestirir (PDF'ten cikan numarali liste bicimlendirmesi numarayi
    metinden ayri bir satira koyabiliyor)."""
    import re
    return re.sub(r'(?m)^([ \t]*\d+[.\)])[ \t]*\n[ \t]*', r'\1 ', text)




def _remove_hyphens(text: str) -> str:
    """Gercek Osmanlica yazida tire (-) diye bir isaret hic kullanilmaz -
    bu tamamen modern Latin alfabesine gecisten sonra turemis bir
    noktalama kuralidir (orn. 'Divan-i Kebir' gibi izafet tamlamalarinda).
    Osmanliya cevirmeden once tireyi bosluga cevirip kaldiriyoruz ki hem
    ciktida hic gorunmesin hem de kelimeler yapismasin."""
    import re
    return re.sub(r" {2,}", " ", re.sub(r"(?<!\d)-|-(?!\d)", " ", text))


def _letter(name: str) -> str:
    """Harf adı için şapkalı/şapkasız esnek desen: Lâm -> L[aâ]m"""
    return "".join("[aâ]" if c == "a" else "[iîİI]" if c == "i" else "[uû]" if c == "u" else c for c in name)


# Surelerin başındaki mukatta harfleri (en uzunlar önce)
_MUKATTAA = [
    (("elif", "lam", "mim", "sad"), "المص"), (("elif", "lam", "mim", "ra"), "المر"),
    (("kaf", "ha", "ya", "ayn", "sad"), "كهیعص"), (("elif", "lam", "mim"), "الم"),
    (("elif", "lam", "ra"), "الر"), (("ta", "sin", "mim"), "طسم"), (("ayn", "sin", "kaf"), "عسق"),
    (("ta", "sin"), "طس"), (("ta", "ha"), "طه"), (("ya", "sin"), "یس"), (("ha", "mim"), "حم"),
]
_MUKATTAA_RE = [(re.compile(r"(?<![\wâîû])" + r"[\s\-–,]+".join(_letter(p) for p in parts) + r"(?![\wâîû])", re.I), ar)
                for parts, ar in _MUKATTAA]
_TEK_HARF_RE = re.compile(r"(?m)^(\s*[\d٠-٩]+[.)]\s*)(S[âa]d|K[âa]f|N[ûu]n)(?=\s*[.,])", re.I)
_TEK_HARF = {"s": "ص", "k": "ق", "n": "ن"}


def _quran_phrases(text: str) -> str:
    """Mukatta harflerini Kur'an'daki yazımıyla yazar: Elif-Lâm-Mîm -> الم, Yâ-Sîn -> یس."""
    for rx, ar in _MUKATTAA_RE:
        text = rx.sub(ar, text)
    return _TEK_HARF_RE.sub(lambda m: m.group(1) + _TEK_HARF[m.group(2)[0].lower()], text)


# İzafet: ünsüzle biten kelimeden sonraki -ı/-i Osmanlıcada yazılmaz (Kur'ân-ı Kerîm -> قرآن كریم)
_IZAFET_RE = re.compile(r"(?:(?<=[^\W\d_])|(?<=[‘’]))-(?:[yY])?[ıiuüIİUÜ](?=[\s\-–]|$)", re.M)


_ROMA = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8, "IX": 9, "X": 10,
         "XI": 11, "XII": 12, "XIII": 13, "XIV": 14, "XV": 15, "XVI": 16, "XVII": 17, "XVIII": 18, "XIX": 19, "XX": 20}
_ROMA_RE = re.compile(r"(?<![\w'’])(" + "|".join(sorted(_ROMA, key=len, reverse=True)) + r")(?![\w'’])")


def _roma_rakam(text: str) -> str:
    """Tek başına duran büyük harfli Roma rakamlarını sayıya çevirir: BÖLÜM I -> BÖLÜM 1."""
    return _ROMA_RE.sub(lambda m: str(_ROMA[m.group(1)]), text)


def _drop_izafet(text: str) -> str:
    # İzafet silinir ama yerine görünmez işaret kalır: "-yı/-yi" -> \ue010 (sonra ی), öteki -> \ue011
    # (sonra ه ile biten kelimede hemze, ünsüzden sonra silinir). Bkz. transliterate_text sarmalayıcısı.
    # h ile biten kelimede ه ünsüzdür, hemze almaz: fıkh-ı ekber فقه اكبر، vech-i irtibât وجه ارتباطی (Hayrat) -> \ue0f1
    # Ünlüyle biten kelimede "-i" (Hayrat): î/i -> \ue013 (sonra ی -> ئ: müddeî-i مدّعئ، maânî-i معانئ),
    # â/a -> \ue014 (sonra ا -> ای: istikrâ-i استقرای، ulemâ-i علمای); ه ile bitiyorsa ikisi de hemze (nokta-i نقطهٔ).
    def _isaret(m):
        if m.group(0)[1:2] in "yY":
            return "\ue010"
        once = m.string[m.start() - 1:m.start()]
        if once in "hH":
            return "\ue0f1"
        if once in "îiÎİ":
            return "\ue013"
        if once in "âaÂA":
            if re.search(r"(?<![^\W\d_])(?:[mM]|[vV]er)\u00e2$", m.string[max(0, m.start() - 4):m.start()]):
                return "\ue015"          # mâ-i ماء، verâ-i وراء (Hayrat)
            return "\ue014"
        return "\ue011"
    return _IZAFET_RE.sub(_isaret, text)


# ---------------- Latin harfli yabancı dil dizileri (Zahir'in kararı: aslı olduğu gibi kalır) ----------------
# Yalnız Türkçede kelime olarak bulunmayan yabancı kelimeler (ne, her, an, on, et, der, al, has, son, la, fi... Türkçede de var)
_YABANCI_KELIME = {"the", "of", "and", "to", "was", "were", "with", "by", "for", "from", "which", "who", "what",
                   "this", "that", "these", "those", "said", "says", "his", "they", "she", "you", "your", "our",
                   "their", "my", "but", "have", "been", "des", "du", "les", "une", "sur", "dans", "par", "pour",
                   "aux", "avec", "comme", "est", "sont", "pas", "qui", "que", "nous", "vous", "elle", "cette",
                   "die", "das", "und", "von", "mit", "ein", "eine", "ist", "nicht", "auf", "zu"}
_YABANCI_IZ_RE = re.compile(r"[qwx]|th|ph|sh|gh|ck|ou|oe|ae|ea|ee|oo|eau|tion$|^ch|[^aeıioöuü\s]y[^aeıioöuü]")
_LATIN_KELIME_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿĞğİıŞş]+(?:['’][A-Za-zÀ-ÖØ-öø-ÿ]+)*")
_TURKCE_HARF_RE = re.compile(r"[çğıöşüÇĞİÖŞÜâîûÂÎÛ]")


def _yabanci_mi(kelime: str) -> bool:
    k = kelime.lower()
    if _TURKCE_HARF_RE.search(kelime):
        return False
    return k in _YABANCI_KELIME or bool(_YABANCI_IZ_RE.search(k)) or bool(re.search(r"[À-ÖØ-öø-ÿ]", kelime))


def _yabancilari_sakla(metin: str):
    """En az iki yabancı kelime içeren, kelimelerinin yarısından çoğu yabancı Latin dizilerini (ör. Fransızca/İngilizce
    kitap adı) çeviriye sokmadan ayırır; yerlerine işaret koyar. Tek tek özel adlar ve Türkçe yazılmış terimler çevrilir."""
    saklanan = []
    kelimeler = list(_LATIN_KELIME_RE.finditer(metin))
    i = 0
    parcalar = []
    son = 0
    while i < len(kelimeler):
        j = i
        while j + 1 < len(kelimeler) and re.fullmatch(r"[\s,;:\-–'’]*", metin[kelimeler[j].end():kelimeler[j + 1].start()]):
            j += 1
        dizi = kelimeler[i:j + 1]
        # dizinin içinden yabancı çekirdeği bul: baştan/sondan Türkçe kelimeleri at
        bas, bit = 0, len(dizi) - 1
        while bas <= bit and not _yabanci_mi(dizi[bas].group(0)):
            bas += 1
        while bit >= bas and not _yabanci_mi(dizi[bit].group(0)):
            bit -= 1
        if bas <= bit:
            asil = dizi[bas:bit + 1]
            yab = sum(1 for k in asil if _yabanci_mi(k.group(0)))
            yeterli = yab >= 2 and yab * 2 > len(asil)
            # çekirdeğin hemen yanındaki, Türkçe harfsiz büyük harfli kelimeler de dizinin parçası (Essai, Paris, Socrates)
            def yanina_katilir(k):
                t = k.group(0)
                return t[:1].isupper() and not _TURKCE_HARF_RE.search(t)
            def kisa(k):  # "de", "la" gibi araya giren kısa kelime
                t = k.group(0)
                return len(t) <= 3 and t.islower() and not _TURKCE_HARF_RE.search(t)
            while True:
                if bas > 0 and yanina_katilir(dizi[bas - 1]):
                    bas -= 1
                elif bas > 1 and kisa(dizi[bas - 1]) and yanina_katilir(dizi[bas - 2]):
                    bas -= 2
                else:
                    break
            while True:
                if bit + 1 < len(dizi) and yanina_katilir(dizi[bit + 1]):
                    bit += 1
                elif bit + 2 < len(dizi) and kisa(dizi[bit + 1]) and yanina_katilir(dizi[bit + 2]):
                    bit += 2
                else:
                    break
            cekirdek = dizi[bas:bit + 1]
            if yeterli:
                a, b = cekirdek[0].start(), cekirdek[-1].end()
                parcalar.append(metin[son:a])
                parcalar.append("\ue000%d\ue001" % len(saklanan))
                saklanan.append(metin[a:b])
                son = b
        i = j + 1
    parcalar.append(metin[son:])
    return "".join(parcalar), saklanan


def _yabancilari_geri_koy(metin: str, saklanan) -> str:
    return re.sub("\ue000(\\d+)\ue001", lambda m: saklanan[int(m.group(1))], metin)


# Dua kısaltmaları açık yazılır: (s.a.v) -> (صلّی الله علیه وسلّم), (a.s) -> (علیه السلام), (r.a) -> (رضی الله عنه)
_KISALTMA = [
    (re.compile(r"(?<![\w.])s\.\s?a\.\s?v\.?(?![\w])", re.I), "صلّی الله علیه وسلّم"),
    (re.compile(r"(?<=\()\s*a\.?\s?s\.?\s?m\.?\s*(?=\))", re.I), "علیه الصلاة والسلام"),   # (asm), (a.s.m.)
    (re.compile(r"(?<=\()\s*as\s*(?=\))", re.I), "علیه السلام"),                          # (as)
    (re.compile(r"(?<=\()\s*ra\s*(?=\))", re.I), "رضی الله عنه"),                          # (ra)
    (re.compile(r"(?<=\()\s*a\.\s?s\.?\s*(?=\))", re.I), "علیه السلام"),
    (re.compile(r"(?<![\w.])r\.\s?a\.?(?![\w])", re.I), "رضی الله عنه"),
]


_PARANTEZ_EKI = {"nin": "ڭ", "nın": "ڭ", "nun": "ڭ", "nün": "ڭ", "in": "ڭ", "ın": "ڭ", "un": "ڭ", "ün": "ڭ",
                 "ye": "ه", "ya": "ه", "e": "ه", "a": "ه", "de": "ده", "da": "ده", "te": "ده", "ta": "ده",
                 "den": "دن", "dan": "دن", "ten": "دن", "tan": "دن", "yi": "ی", "yı": "ی", "i": "ی", "ı": "ی",
                 "le": "له", "la": "له", "yle": "یله", "yla": "یله"}
_PARANTEZ_EK_RE = re.compile(r"(?<=[\u0600-\u06FF])([)\]”])['’]?(" + "|".join(sorted(_PARANTEZ_EKI, key=len, reverse=True))
                             + r")(?![A-Za-zÇçĞğİıÖöŞşÜüÂâÎîÛû])")


# Tur G: bitişik yazılmış sayılar ayrılır (Hayrat ayrı yazar: on bir اون بر، yirmi ikinci یكرمی ایكنجی، bin üç yüz)
_SAYI_KOK = ["milyon", "altmış", "yetmiş", "seksen", "doksan", "yirmi", "otuz", "sekiz", "dokuz", "kırk", "elli", "dört", "dörd",
             "altı", "yedi", "beş", "yüz", "bin", "bir", "iki", "üç", "on"]
_SAYI_SIRA = re.compile(r"(?:inci|ıncı|uncu|üncü|nci|ncı|ncu|ncü)$")


def _sayi_parcala(w: str):
    """Kelime bütünüyle sayı köklerinden oluşuyorsa parçaları; değilse None. Son parçaya sıra eki (-inci) ve ek gelebilir."""
    k = turkish_lower(w)
    parca, i = [], 0
    while i < len(k):
        for s in _SAYI_KOK:
            if k.startswith(s, i):
                parca.append(s); i += len(s); break
        else:
            break
    if len(parca) < 2:
        return None
    kalan = k[i:]
    if kalan and not re.fullmatch(r"(?:[ıiuü]?nc[ıiuü](?:[a-zçğıöşü]{0,6})?|[ıiuü]?n|[ae]|d[ae]|d[ae]n|l[ae]r|l[ae]rc[ae]|[ae]r)", kalan):
        return None
    if "dörd" in parca[:-1] or parca[:2] == ["bir", "bir"]:
        return None                    # Tur G2: birbiri, birbirine sayi degil (Hayrat)
    sinir, j = [], 0
    for p in parca:
        sinir.append(w[j:j + len(p)]); j += len(p)
    sinir[-1] = sinir[-1] + w[j:]
    return sinir


def _sayilari_ayir(metin: str) -> str:
    def f(m):
        p = _sayi_parcala(m.group(0))
        return " ".join(p) if p else m.group(0)
    return re.sub(r"(?<![^\W\d_])[A-Za-zÇçĞğİıÖöŞşÜü]{5,}(?![^\W\d_'’])", f, metin)


def _kisaltmalar(metin: str) -> str:
    metin = _sayilari_ayir(metin)
    metin = re.sub(r"\bHz\.\s*", "Hazret ", metin)          # Hz. Muhammed -> حضرت محمّد
    # Tur E: iki özel ad arasındaki "b." ibn (oğlu) kısaltmasıdır: Ahmed b. Hanbel -> احمد بن حنبل
    metin = re.sub(r"(?<![^\W\d_])([A-ZÇĞİÖŞÜÂÎÛ][a-zçğıöşüâîû'’]{1,20}) b\. (?=[A-ZÇĞİÖŞÜÂÎÛ][a-zçğıöşüâîû])", "\\1 \u0628\u0646 ", metin)
    metin = re.sub(r"\bAdem(?=[a-zçğıöşü'’]|\b)", "Âdem", metin)  # büyük harfli Adem peygamberdir (عدم değil)
    metin = re.sub(r"\bAlim(?!ler|lerin|lik)(?=[a-zçğıöşü'’”)]|\b)", "Aliym", metin)  # büyük harfli Alim: Allah'ın ismi علیم
    for rx, ar in _KISALTMA:
        metin = rx.sub(ar, metin)
    # Arapça açılımdan sonra gelen ek: (s.a.v)'in -> (صلّی الله علیه وسلّم)ڭ
    return _PARANTEZ_EK_RE.sub(lambda m: m.group(1) + _PARANTEZ_EKI[m.group(2)], metin)


# İmlâ turu 12: dua ibareleri açık yazılır (sellellahu aleyhi ve sellem, vellahu âlem, Yarabbi)
_DUA_IBARE = [
    (re.compile(r"(?<![^\W\d_])s[ae]ll[ae]ll[aâ]hu\s+aleyhi\s+(?:ve\s*)?sellem(?:['’]([a-zçğıöşü]{1,4}))?(?![^\W\d_])", re.I),
     "صلّی الله علیه وسلّم"),
    (re.compile(r"(?<![^\W\d_])vell[aâ]hu\s+(?:[aâ]lem|a['’]lem)(?![^\W\d_])", re.I), "والله اعلم"),
    (re.compile(r"(?<![^\W\d_])y[aâ]\s?rabb[iî](?![^\W\d_])", re.I), "یا ربّی"),
    (re.compile(r"(?<![^\W\d_])Irak(?:['’]([a-zçğıöşü]{1,4}))?(?![^\W\d_])"), "عراق"),   # büyük harfli Irak ülkedir (ırak = uzak)
]
_HARF = "A-Za-zÇçĞğİıÖöŞşÜüÂâÎîÛû"
_SAYI_KELIME = {"bir", "iki", "üç", "dört", "beş", "altı", "yedi", "sekiz", "dokuz", "on", "yirmi", "otuz", "kırk", "elli",
                "altmış", "yetmiş", "seksen", "doksan", "yüz", "birkaç", "kaç", "nice", "binlerce"}


def _dua_ibareleri(metin: str) -> str:
    for rx, ar in _DUA_IBARE:
        metin = rx.sub(lambda m: ar + (_PARANTEZ_EKI.get(m.group(1).lower(), "") if m.lastindex and m.group(1) else ""), metin)
    return metin


# ı ile başlayan Türkçe kelimeler (Islak, Işık, Irmak): büyük I'ları gerçek I'dır
_I_TURKCE = ("ılı", "ırak", "ırk", "ırmak", "ısı", "ısır", "ıslak", "ıslâk", "ıslan", "ıslat", "ısmarla", "ıssız", "ışı", "ızgara", "ıhlamur", "ıvır")


def _buyuk_i(metin: str) -> str:
    """OCR'ın noktasını düşürdüğü büyük İ: "Ibrahim", "Islâm" sözlükte "ı" ile bulunamaz, "İ" ile bulunursa İ okunur."""
    def f(m):
        w = m.group(0)
        if dictionary.lookup_with_suffix(w)[0] or turkish_lower(w).startswith(_I_TURKCE):
            return w
        alt = "İ" + w[1:]
        return alt if dictionary.lookup_with_suffix(alt)[0] else w
    return re.sub(r"(?<![" + _HARF + r"'’])I[a-zçğıöşüâîû]+", f, metin)


def _et_bin(metin: str) -> str:
    """Bağlama göre: Arapça/Farsça isimden sonra "et" emir (dikkat et ایت; et = ات yalnız tek başına), sayıdan sonra
    "bin" bin sayısı (kırk bin بیڭ; Ali bin Ebu Talib بن)."""
    def f(m):
        onceki, ara, kelime = m.group(1), m.group(2), turkish_lower(m.group(3))
        o = turkish_lower(onceki)
        if kelime == "bin" and (o in _SAYI_KELIME or o.isdigit()):
            return onceki + ara + "بیڭ"
        if kelime == "et":
            hit = dictionary.lookup_exact(o)
            if hit and str(hit[1]).startswith(("ar", "fa", "soz")):
                return onceki + ara + "ایت"
        return m.group(0)
    metin = re.sub(r"([" + _HARF + r"]+|\d+)(\s+)(et|bin)(?![" + _HARF + r"'’])", f, metin)
    # cümle/söz sonundaki "başlar" fiildir (باشلار); "başlar" (başın çoğulu) ekle gelir: باشلری، باشلره
    return re.sub(r"(?<![" + _HARF + r"'’])[Bb]aşlar(?=\s*[.,!?;:…»]|\s*$)", "باشلار", metin)


def _lerin_eki(latin: str, osm: str) -> str:
    """Kural motorunun çoğul + ilgi eki yazımı: valilerin والیلرین -> والیلرڭ, tatlıların طاتلیلارین -> طاتلیلرڭ."""
    if re.search(r"l[ae]r[ıi]n$", turkish_lower(latin)):
        for son in ("لارین", "لرین"):
            if osm.endswith(son):
                return osm[:-len(son)] + "لرڭ"
    return osm


def transliterate_text(
    turkish_text: str,
    progress_callback=None,
) -> str:
    turkish_text = unicodedata.normalize("NFC", turkish_text)   # ayrık şapka (u + ̂) -> û
    turkish_text = _merge_orphan_numbers(turkish_text)
    turkish_text = re.sub(r"(?<=[^\W\d_])[‘`´](?=[^\W\d_])", "’", turkish_text)  # kelime içindeki ‘ ayın/hemze işareti: En‘âm
    turkish_text = turkish_text.translate(_MAKRON)                                  # kādir -> kâdir (uzun ünlü işareti)
    turkish_text, _saklanan = _yabancilari_sakla(turkish_text)
    turkish_text = _kisaltmalar(turkish_text)
    turkish_text = _dua_ibareleri(turkish_text)   # imlâ turu 12
    turkish_text = _buyuk_i(turkish_text)
    turkish_text = _et_bin(turkish_text)
    turkish_text = _quran_phrases(turkish_text)
    turkish_text = _roma_rakam(turkish_text)
    turkish_text = _arapca_tarifler(turkish_text)      # Kitâbü't-Tevhîd, el-Bakara (tire silinmeden önce)
    turkish_text = _drop_izafet(turkish_text)
    turkish_text = _remove_hyphens(turkish_text)
    """Türkçe metni (zaten Türkçe olduğu varsayılır) Osmanlıcaya çevirir (sözlük + kural motoru)."""
    parts = SENTENCE_SPLIT_RE.split(turkish_text)
    sentences = parts[0::2]
    separators = parts[1::2]
    total = len(sentences)
    out_sentences = [""] * total
    done = 0

    non_empty_idx = [i for i, s in enumerate(sentences) if s.strip()]
    for i in non_empty_idx:
        out_sentences[i] = draft_transliterate_sentence(sentences[i])
    for i, s in enumerate(sentences):
        if not s.strip():
            out_sentences[i] = s

    if progress_callback:
        progress_callback(total, total)

    result = []
    for i, s in enumerate(out_sentences):
        result.append(s)
        if i < len(separators):
            result.append("\n" if "\n" in separators[i] else " ")
    sonuc = _ottoman_punctuation("".join(result))
    sonuc = re.sub(r"(?<=[\u0621-\u06D3]) كه(?=[\s،.!؟:؛\"”]|$)", "كه", sonuc)   # ki öncesine bitişik: ناصلكه، واردركه
    sonuc = _rakamlar(sonuc)                      # 1911 -> ١٩١١ (Latin harfli yabancı metindeki rakam kalır)
    return _yabancilari_geri_koy(sonuc, _saklanan)


def _ottoman_punctuation(text: str) -> str:
    """Latin noktalamayı Osmanlıca karşılıklarına çevirir: , -> ،  ; -> ؛  ? -> ؟
    (Sayıların içindeki virgüle dokunmaz: 3,5 aynen kalır.)"""
    text = re.sub(r",(?!\d)|(?<!\d),", "\u060c", text)
    return text.replace(";", "\u061b").replace("?", "\u061f")


def full_pipeline(
    raw_text: str,
    progress_callback=None,
    assume_turkish: bool = False,
) -> dict:
    """Tam hat: dil denetimi -> Osmanlıca çeviri. Yalnız Türkçe metin alınır (çeviri yok)."""
    # assume_turkish: metin zaten Türkçe (ör. Dedplay Stüdyo); dil tespiti atlanır,
    # kısa/yabancı isimli metinler yanlışlıkla "başka dil" sanılıp çevrilmez.
    lang = "tr" if assume_turkish else detect_language(raw_text)
    if lang != "tr":
        # Dil tahmini kısa/isimli Türkçe metinde yanılabilir: kısa metin ya da Türkçeye özgü harfli metin Türkçe sayılır.
        if len(raw_text.strip()) < 200 or re.search("[çğıöşüÇĞİÖŞÜ]", raw_text):
            lang = "tr"
        else:
            raise RuntimeError(
                f"Girdi Türkçe değil (tespit edilen dil: {lang}). Osmanlıca çevirici yalnız Türkçe metin alır."
            )
    turkish_text = raw_text

    ottoman_text = transliterate_text(turkish_text, progress_callback=progress_callback)

    return {
        "detected_lang": lang,
        "turkish_text": turkish_text,
        "ottoman_text": ottoman_text,
    }



# ---- İmlâ: izafet işaretleri ve isimlerdeki "bin" (transliterate_text sarmalayıcısı) ----
_transliterate_text_ilk = transliterate_text
_BIN_ISIM_RE = re.compile(r"([A-ZÇĞİÖŞÜÂÎÛ][^\s]*\s)bin(?=\s[A-ZÇĞİÖŞÜÂÎÛ])")


def _lillah(m):
    """Sözlükte bütün hâliyle olan kelime bölünmez (Elhamdülillâh الحمد لله); öteki: elhamdü lillâh, âdâtullâh -> عادات الله."""
    w = m.group(0)
    if dictionary.lookup_exact(turkish_lower(w)):
        return w
    w = re.sub(r"(?<=[^\W\d_]{3})[üu]?lill[âa]h", " lillâh", w)
    return re.sub(r"(?<=[^\W\d_]{3})[üu]ll[âa]h", " Allâh", w)


def transliterate_text(turkish_text, *args, **kwargs):
    """İzafet: ه ile biten kelimede hemze (رسالهٔ نور, قوّهٔ معنویه), "-yı/-yi"de ی (دنیای فانی), ünsüzden sonra yazılmaz.
    İki özel ismin arasındaki "bin" بن (Ali bin Ebî Tâlib); öteki "bin" sözlükten (sayı: بیڭ)."""
    turkish_text = turkish_text.replace("\u02bb", "\u2018")   # ʻ ayın işareti = ‘
    turkish_text = re.sub(r"[^\W\d_]*ll[âa]h[^\W\d_]*", _lillah, turkish_text)   # elhamdülillâh, âdâtullâh
    turkish_text = _BIN_ISIM_RE.sub("\\1\ue012", turkish_text)
    out = _transliterate_text_ilk(turkish_text, *args, **kwargs)
    out = out.replace("\ue012", "بن").replace("\ue010", "ی")
    out = re.sub("\u06cc(\u0651?)\ue013", "\u0626\\1", out)          # müddeî-i مدّعئ، maânî-i معانئ (Hayrat)
    out = re.sub("\u0627\ue014", "\u0627\u06cc", out)                # istikrâ-i استقرای، ulemâ-i علمای (Hayrat)
    out = re.sub("\u0627\ue015", "\u0627\u0621", out)
    out = re.sub("\u0647[\ue011\ue013\ue014]", "\u0647\u0654", out)
    out = re.sub("[\ue011\ue013\ue014\ue015\ue0f1]", "", out)
    out = re.sub("[\u2018\u2019'`\u02bf\u02be]", "", out)   # ayın/hemze işareti Osmanlıcaya harf olarak geçmez
    out = re.sub("[\u0610-\u061a]", "", out)   # Hayrat'ın isim üstü dua işaretleri (اونڭؐ، ابراهیمؑ) bağlama göre; dualar açık yazılır
    return out.replace("\u06af", "\u0643")                  # g sesi Hayrat gibi kef (ك) ile; ڭ kalır



# ---- Hayrat çok kelimeli ifadeleri ve birleşik yazımlar ----
import os as _os
from pathlib import Path

_IFADE_DOSYA = _os.environ.get("HAYRAT_IFADE") or str(Path(__file__).parent.parent / "data" / "hayrat_ifade.tsv")
_KESME = "'\u2019\u2018\u02bc\u02bb"
_SAPKA_TR = str.maketrans({"â": "a", "î": "i", "û": "u", "ā": "a", "ī": "i", "ū": "u", "ō": "o"})


def _ifade_anahtar(s):
    s = s.replace("I", "ı").replace("İ", "i").lower()
    for c in _KESME:
        s = s.replace(c, "'")
    return re.sub(r"\s+", " ", s.replace("\u2010", "-")).strip()


def _trie_regex(anahtarlar):
    kok = {}
    for a in anahtarlar:
        d = kok
        for c in a:
            d = d.setdefault(c, {})
        d[""] = True

    def kar(c):
        if c == "'":
            return "[" + _KESME + "]"
        if c == " ":
            return r"\s+"
        if c == "-":
            return "[-\u2010]"
        return re.escape(c)

    def yaz(d):
        son = "" in d
        dallar = [kar(c) + yaz(d[c]) for c in sorted(k for k in d if k)]
        if not dallar:
            return ""
        govde = dallar[0] if len(dallar) == 1 else "(?:" + "|".join(dallar) + ")"
        return "(?:" + govde + ")?" if son else govde
    return yaz(kok)


def _ifade_yukle():
    ifade = {}
    try:
        for satir in open(_IFADE_DOSYA, encoding="utf-8"):
            p = satir.rstrip("\n").split("\t")
            if len(p) >= 2 and p[0] and p[1]:
                ifade[_ifade_anahtar(p[0])] = p[1]
    except OSError:
        return {}, None
    if not ifade:
        return {}, None
    desen = r"(?<![^\W\d_])(" + _trie_regex(ifade) + r")(?:[" + _KESME + r"]([^\W\d_]+))?(?![^\W\d_])"
    return ifade, re.compile(desen)


_IFADE, _IFADE_RE = _ifade_yukle()
_BERI_RE = re.compile(r"(?<=دن|تن) (?:برو|بری)(?=$|[\s،.؛:!؟»)\]])")
_SORU_RE = re.compile(r" (می(?:دیر|در|سڭ|سڭز|سین|یز|ییز|یم|یدی|یدیر|كه)?)(?=$|[\s،.؛:!؟?»)\]])")
_transliterate_text_ifadesiz = transliterate_text


def _bitisik(out):
    out = out.replace("\u201c", '"').replace("\u201d", '"').replace("\u201e", '"')   # Hayrat düz tırnak
    out = _BERI_RE.sub("بری", out)          # seneden beri -> سنهدنبری (Hayrat)
    return _SORU_RE.sub(r"\1", out)           # var mıdır -> وارمیدر، olmaz mı -> اولمازمی


_IFADE_IZAFET_RE = re.compile(r"-([yY])?[ıiuüIİUÜ](?=[\s\-\u2013]|$)")


def _ifade_ek(latin, ek):
    son = re.split(r"[\s\-\u2010" + _KESME + r"]+", latin.strip())[-1]
    s = turkish_lower(son.translate(_SAPKA_TR))
    return rules.ekleri_yaz(s, [], [turkish_lower(ek)], rules._harmony_class(s))


def transliterate_text(turkish_text, *args, **kwargs):
    if not _IFADE_RE or not turkish_text:
        return _bitisik(_transliterate_text_ifadesiz(turkish_text, *args, **kwargs))
    kucuk = turkish_text.replace("I", "ı").replace("İ", "i").lower()
    if len(kucuk) != len(turkish_text):
        return _bitisik(_transliterate_text_ifadesiz(turkish_text, *args, **kwargs))
    parcalar, son = [], 0
    for m in _IFADE_RE.finditer(kucuk):
        yazim = _IFADE.get(_ifade_anahtar(m.group(1))) or _IFADE.get(_ifade_anahtar(m.group(1)).translate(_SAPKA_TR))
        if not yazim:
            continue
        if m.group(2) and not _ek_mi(turkish_lower(m.group(2))):
            continue          # kesmeden sonrası ek değil (Bu da‘vâ: "bu da" + "vâ" değil, ayınlı kelime)
        parcalar.append(("metin", turkish_text[son:m.start()]))
        if m.group(2):
            yazim += _ifade_ek(turkish_text[m.start(1):m.end(1)], turkish_text[m.start(2):m.end(2)])
        son = m.end()
        iz = _IFADE_IZAFET_RE.match(turkish_text, son)
        if iz:                           # ifadeden sonraki izafet (yed-i beyzâ-yı ید بیضای)
            if yazim.endswith("\u0627"):
                yazim += "\u06cc"
            elif yazim.endswith("\u06cc") and not iz.group(1):
                yazim = yazim[:-1] + "\u0626"
            elif yazim.endswith("\u0647") and turkish_text[son - 1:son] not in "hH":
                yazim += "\u0654"
            son = iz.end()
        parcalar.append(("ifade", yazim))
    if not parcalar:
        return _bitisik(_transliterate_text_ifadesiz(turkish_text, *args, **kwargs))
    parcalar.append(("metin", turkish_text[son:]))
    out = []
    for tur, p in parcalar:
        if tur == "ifade" or not p.strip():
            out.append(p)
        else:
            bas, sonb = p[: len(p) - len(p.lstrip())], p[len(p.rstrip()):]
            out.append(bas + _transliterate_text_ifadesiz(p.strip(), *args, **kwargs) + sonb)
    return _bitisik("".join(out))


# ---- Ayınlı (‘) ve uzatma çizgili (ā ī ū) kelimeler: sözlükteki anahtar doğrudan (Hayrat: da‘vâ دعوا، tab‘ طبع، iskāt اسقاط) ----
_AYIN_HARF = "A-Za-zÇçĞğİıÖöŞşÜüÂâÎîÛûĀāĪīŪū\u2018\u02bb"
_AYIN_OZEL = set("\u2018\u02bbĀāĪīŪū")
_AYIN_KELIME_RE = re.compile("(?<![-\u2010'\u2019" + _AYIN_HARF + "])[" + _AYIN_HARF + "]+(?![-\u2010'\u2019" + _AYIN_HARF + "])")
_transliterate_text_ayinsiz = transliterate_text


def transliterate_text(turkish_text, *args, **kwargs):
    if not turkish_text or not (_AYIN_OZEL & set(turkish_text)):
        return _transliterate_text_ayinsiz(turkish_text, *args, **kwargs)
    saklanan = []

    def sakla(m):
        w = m.group(0)
        if not (_AYIN_OZEL & set(w)) or len(saklanan) > 6000:
            return w
        h = dictionary.lookup_exact(turkish_lower(w.replace("\u02bb", "\u2018")))
        if not h:
            return w
        saklanan.append(h[0].replace("\u06af", "\u0643"))
        return "\ue030" + chr(0xe100 + len(saklanan) - 1)
    metin = _AYIN_KELIME_RE.sub(sakla, turkish_text)
    out = _transliterate_text_ayinsiz(metin, *args, **kwargs)
    for i, yazim in enumerate(saklanan):
        out = out.replace("\ue030" + chr(0xe100 + i), yazim)
    return out


# ---- Senin/onun (2./3. tekil iyelik): "senin" + en çok 6 kelime -> 2. kişi (kalbini قلبڭی، başına باشڭه) ----
# Araya virgül/nokta, başka bir sahip (onun, kendi, ilgi ekli kelime) ya da aynı kalıpta başka kelime girerse uygulanmaz.
_HITAP_KALIP = re.compile(r"^(.*[bcçdfgğhjklmnprsştvyz])([ıiuü])n(ı|i|u|ü|a|e|da|de|ta|te|dan|den|tan|ten|ın|in|un|ün|daki|deki|dır|dir)$")
_HITAP_EDAT = {"için", "gibi", "kadar", "ile", "göre", "karşı", "dolayı", "rağmen", "üzere", "nazaran", "ancak", "değil"}
_HITAP_SAHIP = {"onun", "bunun", "şunun", "kendi", "onların", "bunların", "benim", "bizim"}
_HITAP_TOK = re.compile(r"[^\W\d_]+(?:[’'‘][^\W\d_]+)*")
_HITAP_SON = re.compile("\u0646(\u200c?(?:\u06cc|\u0647|\u06d5|\u062f\u0647\u200c?\u0643\u06cc|\u062f\u0647|\u062f\u0646|\u06ad|\u062f\u0631))$")
_transliterate_text_hitapsiz = transliterate_text


def _hitap_ilgi(w: str) -> bool:
    return bool(re.search(r"(?:[’'][ıiuü]?n|[ıiuü]n|n[ıiuü]n)$", w)) and w not in ("senin", "benin", "için", "bin", "din", "ben")


def _hitap_yaz(kelime, *args, **kwargs):
    o = _transliterate_text_hitapsiz(kelime, *args, **kwargs)
    if " " in o.strip() or not _HITAP_SON.search(o):
        return None
    return _HITAP_SON.sub(lambda m: "\u06ad" + m.group(1), o)


# Hayrat Latin'indeki düz dua kısaltmaları (ham metinde, öteki katmanlardan önce): Muhammed’in asm, İmâm-ı Gazâlî’nin ra, Mûsâ as
_DUZ_DUA_RE = re.compile(r"(?<![^\W\d_(])(?:(asm)|(\S+)(\s+)(ra|as))(?![^\W\d_)])")
_DUZ_DUA = {"asm": "علیه الصلاة والسلام", "ra": "رضی الله عنه", "as": "علیه السلام"}


def _duz_dua(metin: str):
    saklanan = []

    def sakla(m):
        if m.group(1):
            k, on = "asm", ""
        else:
            onceki, k = m.group(2), m.group(4)
            ad = onceki.lstrip("(\u201c\u2018" + chr(34) + chr(39))
            if not ad or not ad[0].isupper():
                return m.group(0)                 # yalnız büyük harfli isimden sonra: Ali ra, Mûsâ as
            if k == "as" and m.start() > 0 and not re.search(r"[^\W\d_’'] $", metin[max(0, m.start() - 2):m.start()]):
                return m.group(0)                 # as: cümle başındaki büyük harften sonra değil ("Şunu as")
            on = onceki + m.group(3)
        saklanan.append(_DUZ_DUA[k])
        return on + "\ue033" + chr(0xe400 + len(saklanan) - 1)
    return _DUZ_DUA_RE.sub(sakla, metin), saklanan


def transliterate_text(turkish_text, *args, **kwargs):
    if not turkish_text:
        return _transliterate_text_hitapsiz(turkish_text, *args, **kwargs)
    metin, dualar = _duz_dua(turkish_text)
    out = _hitap_cevir(metin, *args, **kwargs)
    for i, yazim in enumerate(dualar):
        out = out.replace("\ue033" + chr(0xe400 + i), yazim)
    return re.sub("[\u0610-\u061a]", "", out)   # Hayrat'ın isim üstü dua işaretleri (ؐ ؑ ؓ) hiçbir katmanda kalmasın


def _hitap_cevir(turkish_text, *args, **kwargs):
    if not re.search(r"(?<![^\W\d_])[Ss]enin(?![^\W\d_])", turkish_text):
        return _transliterate_text_hitapsiz(turkish_text, *args, **kwargs)
    yerler = []
    for c in re.finditer(r"[^.!?;:,\n]+", turkish_text):
        toks = list(_HITAP_TOK.finditer(c.group(0)))
        for i, m in enumerate(toks):
            if not _HITAP_KALIP.match(turkish_lower(m.group(0))):
                continue
            for j in range(i - 1, max(-1, i - 7), -1):
                p = turkish_lower(toks[j].group(0))
                if p == "senin":
                    if j + 1 < i and turkish_lower(toks[j + 1].group(0)) in _HITAP_EDAT:
                        break             # "senin için ilkinden": senin edata bağlı, sahibi değil
                    yerler.append((c.start() + m.start(), c.start() + m.end()))
                    break
                if p in _HITAP_SAHIP or _hitap_ilgi(p) or _HITAP_KALIP.match(p):
                    break
    if not yerler:
        return _transliterate_text_hitapsiz(turkish_text, *args, **kwargs)
    saklanan, parca, son = [], [], 0
    for a, b in yerler:
        yazim = _hitap_yaz(turkish_text[a:b], *args, **kwargs)
        if not yazim:
            continue
        parca.append(turkish_text[son:a] + "\ue032" + chr(0xe300 + len(saklanan)))
        saklanan.append(yazim)
        son = b
    metin = "".join(parca) + turkish_text[son:]
    out = _transliterate_text_hitapsiz(metin, *args, **kwargs)
    for i, yazim in enumerate(saklanan):
        out = out.replace("\ue032" + chr(0xe300 + i), yazim)
    return out


# ---- Arapça dişil sıfat izafetten sonra (Hayrat: nübüvvet-i mutlaka مطلقه، ulûm-u âdiye عادیه) ----
_DISIL_SON = re.compile(r"(.+?)(iyye|iye|e|a)((?:n[ıi]n|y[ıi]|y[ae]|d[ae]|d[ae]n|t[ae]n|l[ae]r[ıi]?(?:n[ıi])?|l[ae]r[ıi]n[ae]|"
                        r"l[ae]r[ıi]n[ıi]n|l[ae]rd[ae]n?|s[ıi](?:n[ıi])?(?:n[ae])?|s[ıi]n[ıi]n|ki|d[ıi]r)?)")
_DISIL_RE = re.compile(r"(?<=-[ıiuüIİUÜ] )([^\W\d_]+)(-[ıiIİ])?(?![^\W\d_’'‘\-])")
_transliterate_text_disilsiz = transliterate_text


def _disil_sifat(y: str):
    yl = turkish_lower(y)
    m = _DISIL_SON.fullmatch(yl)
    if not m:
        return None
    kok, son, ek = m.groups()
    nisbe = son in ("iye", "iyye")
    if len(kok) < (2 if nisbe else 3) or re.search(r"[âîû]", son + ek[:1]) or yl.endswith(("â", "î", "û")):
        return None
    govde = kok + son
    def _sozluk(k):                      # iki kelimeye bölünmüş eski kayıt (arabiye عربی یه) yok sayılır, Hayrat'taki sayılır
        h = dictionary._get(k)
        return h if h and (" " not in h[0].strip() or k in dictionary.HAYRAT_ANAHTAR) else None
    tam = _sozluk(yl)
    if tam and not (tam[0].endswith("\u0627") and len(kok) >= 6 and not ek):
        return None                      # kelimenin kendisi sözlükte (camide, fenası); istisna: mutlaka مطلقا
    hit, ekler = dictionary.lookup_with_suffix(yl)
    if hit and " " in hit[0].strip() and yl not in dictionary.HAYRAT_ANAHTAR:
        hit = None
    if hit:
        kok_uz = len(yl) - sum(len(x) for x in ekler)
        if kok_uz > len(govde) or (kok_uz == len(govde) and not (hit[0].endswith("\u0627") and len(kok) >= 6)):
            return None                  # doğru bölme başka: insan+ın, beyân+ın, Akdes+ini, vâhime+nin
    hg = _sozluk(govde)
    if hg and not hg[0].endswith("\u0627"):
        return None                      # kendisi kelime (müsâade, akîde)
    hb = dictionary.DICTIONARY.get(kok + "î" if nisbe else kok) or (dictionary.DICTIONARY.get(kok + "i") if nisbe else None)
    if hit and (len(yl) - sum(len(x) for x in ekler) == len(kok) or (nisbe and len(yl) - sum(len(x) for x in ekler) == len(kok) + 1)) \
            and " " not in hit[0].strip():
        hb = hit                         # sözlüğün bulduğu kök aynıysa onun yazımı (mahsûs+e: محسوس)
    if not hb or " " in hb[0]:
        return None                      # şapkasız eşleme yok (vâhim ≠ vahîm)
    b = hb[0]
    if nisbe and not b.endswith("\u06cc"):
        return None
    if not nisbe and b.endswith(("\u0627", "\u06cc", "\u0648", "\u0647", "\u06ad")):
        return None
    yazi = b + "\u0647"
    if ek:
        e = rules.ekleri_yaz(govde, [ek], [], rules._harmony_class(yl))
        yazi += "\u200c" + e.lstrip("\u200c")
    return yazi


def transliterate_text(turkish_text, *args, **kwargs):
    if not turkish_text or "-" not in turkish_text:
        return _transliterate_text_disilsiz(turkish_text, *args, **kwargs)
    saklanan = []

    def sakla(m):
        izafet = m.group(2)
        onceki = re.search(r"(\S+-[ıiuüIİUÜ]) $", turkish_text[:m.start()])
        if onceki and _IFADE.get(_ifade_anahtar(onceki.group(1).lstrip("(\u201c\u2018" + chr(34) + chr(39)) + " " + m.group(0))):
            return m.group(0)            # Hayrat ifadesi (adem-i sırfa عدم صرفه): ifade katmanına bırak
        yazi = _disil_sifat(m.group(1))
        if not yazi or (izafet and not yazi.endswith("\u0647")) or len(saklanan) > 6000:
            return m.group(0)
        if izafet:
            yazi += "\u0654"            # izafet: ه ile biten kelimede hemze (عمیقهٔ)
        saklanan.append(yazi)
        return "\ue034" + chr(0xe500 + len(saklanan) - 1)
    metin = _DISIL_RE.sub(sakla, turkish_text)
    out = _transliterate_text_disilsiz(metin, *args, **kwargs)
    for i, yazi in enumerate(saklanan):
        out = out.replace("\ue034" + chr(0xe500 + i), yazi)
    return out


# ---- Bağlam sözlüğü (Hayrat'tan öğrenilen; tools/hayrat_baglam_ogren.py): et ایت/ات، basar بصر/باصار ----
import math as _math
_BAGLAM = {}            # kelime -> {norm: [ham, toplam, {özellik: sayı}]}
_BAGLAM_ESIK = 2.0
_BAGLAM_NOKTA = ".,;:!?\"'()[]«»“”‘’-—…"


def _baglam_norm(o):
    o = unicodedata.normalize("NFC", o).replace("\u06d5", "\u0647").replace("\u06c0", "\u0647").replace("\u06af", "\u0643") \
        .replace("\u06a9", "\u0643").replace("\u064a", "\u06cc").replace("\u0649", "\u06cc").replace("\u0623", "\u0627")
    o = re.sub("[\u0610-\u061a\u064b-\u065f\u0670\u0640\u0654\u200c\u200d]", "", o)
    return re.sub("[\u060c\u061b\u061f\u06d4]", "", o)


def _baglam_yazim(oh):
    """Hayrat'ın ham yazımı -> çevirici biçimi: hareke yok (şedde, tenvin kalır), bitişmeyen he = ه (+ ara boşluk)."""
    oh = re.sub("[\u064e\u064f\u0650\u0652\u0670\u0610-\u061a]", "", oh)
    oh = re.sub("\u06d5(?=.)", "\u0647\u200c", oh)
    return oh.replace("\u06d5", "\u0647").replace("\u06af", "\u0643")


def _baglam_yukle():
    global _BAGLAM_ESIK
    yol = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "data", "hayrat_baglam.tsv")
    if _os.environ.get("OSM_BAGLAM", "1") == "0" or not _os.path.exists(yol):
        return
    for satir in open(yol, encoding="utf-8"):
        p = satir.rstrip("\n").split("\t")
        if p[0] == "#esik" and len(p) > 1:
            _BAGLAM_ESIK = float(p[1])
            continue
        if satir.startswith("#") or len(p) < 4:
            continue
        w, oh, oz, n = p[0], p[1], p[2], int(p[3])
        k = _BAGLAM.setdefault(w, {}).setdefault(_baglam_norm(oh), [oh, 0, {}])
        if oz == "*":
            k[0], k[1] = oh, n
        else:
            k[2][oz] = n


_baglam_yukle()
_transliterate_text_baglamsiz = transliterate_text


def _baglam_sec(w, ozs):
    """Naive Bayes (öğrenme aracıyla aynı); kanıt eşiği geçmezse None (sözlükteki yazım kalır)."""
    yazimlar = _BAGLAM[w]
    toplam = sum(v[1] for v in yazimlar.values())
    h = dictionary.lookup_exact(w)
    v = _baglam_norm(h[0]) if h and _baglam_norm(h[0]) in yazimlar else max(yazimlar, key=lambda o: yazimlar[o][1])
    skor = {}
    for o, (oh, n, fs) in yazimlar.items():
        if n <= 0:
            continue
        s = _math.log(n / toplam)
        enc = 0
        for f in ozs:
            c = fs.get(f, 0)
            if not f.endswith(":#"):
                enc = max(enc, c)        # kanıt yalnız gerçek komşu kelimeden (paragraf başı/sonu sayılmaz)
            s += _math.log((c + 0.1) / (n + 5.0))
        skor[o] = (s, enc)
    if v not in skor:
        return None
    en = max(skor, key=lambda o: skor[o][0])
    if en != v and skor[en][0] - skor[v][0] >= _BAGLAM_ESIK and skor[en][1] >= 2:
        return _baglam_yazim(yazimlar[en][0])
    return None


def transliterate_text(turkish_text, *args, **kwargs):
    if not _BAGLAM or not turkish_text:
        return _transliterate_text_baglamsiz(turkish_text, *args, **kwargs)
    saklanan, parca, son = [], [], 0
    for par in re.finditer(r"[^\n]+", turkish_text):
        toks = []
        for m in re.finditer(r"\S+", par.group(0)):
            ham = m.group(0)
            k = turkish_lower(ham).strip(_BAGLAM_NOKTA)
            if not k:
                continue
            bas = par.start() + m.start() + (len(ham) - len(ham.lstrip(_BAGLAM_NOKTA)))
            toks.append((k, bas, bas + len(ham.strip(_BAGLAM_NOKTA))))
        for i, (k, a, b) in enumerate(toks):
            if k not in _BAGLAM:
                continue
            ozs = []
            for d, ad in ((-1, "L1"), (1, "R1"), (-2, "L2"), (2, "R2")):
                j = i + d
                ozs.append(f"{ad}:{toks[j][0]}" if 0 <= j < len(toks) else f"{ad}:#")
            yazim = _baglam_sec(k, ozs)
            if not yazim or a < son:
                continue
            parca.append(turkish_text[son:a] + "\ue035" + chr(0xe600 + len(saklanan)))
            saklanan.append(yazim)
            son = b
    if not saklanan:
        return _transliterate_text_baglamsiz(turkish_text, *args, **kwargs)
    metin = "".join(parca) + turkish_text[son:]
    out = _transliterate_text_baglamsiz(metin, *args, **kwargs)
    for i, yazim in enumerate(saklanan):
        out = out.replace("\ue035" + chr(0xe600 + i), yazim)
    return out


# ---- Hemzeyle biten kelime (mebde’ مبدأ، menşe’ منشأ، sû’ سوء): sözlükteki kesmeli kayıt doğrudan ----
# Metindeki ’ sözlükte ' ile yazılı; eskiden kelime sonundaki ’ atılıp kelime hemzesiz aranıyordu (mebde’ -> مبده).
# Kapanış tırnağıyla karışmasın diye yalnız sözlükte hemzeli kaydı olan kelime; arkasındaki izafet (-i) yazılmaz (Hayrat).
_HEMZE_RE = re.compile(r"(?<![^\W\d_])(?<![\-\u2010\u2018\u2019'])([^\W\d_]{2,}[\u2019'])(-[ıiuüIİUÜ])?(?![^\W\d_])")


def _ifade_kapsar(metin, bas, son):
    """[bas, son) aralığı bir Hayrat ifadesinin içinde mi (ifade katmanı daha doğru yazar: sû’-i isti‘mâle, kānûn-u medenîye)."""
    if not _IFADE_RE:
        return False
    kucuk = metin.replace("I", "ı").replace("İ", "i").lower()
    if len(kucuk) != len(metin):
        return False
    for m in _IFADE_RE.finditer(kucuk, max(0, bas - 120)):
        if m.start(1) >= son:
            break
        if m.end(1) > bas and " " in m.group(1).strip():
            return True
    return False
_HEMZE_HARF = set("\u0621\u0623\u0624\u0626")
_transliterate_text_hemzesiz = transliterate_text


def transliterate_text(turkish_text, *args, **kwargs):
    if not turkish_text or not re.search(r"[^\W\d_][\u2019'](?![^\W\d_])", turkish_text):
        return _transliterate_text_hemzesiz(turkish_text, *args, **kwargs)
    saklanan = []

    def sakla(m):
        w = turkish_lower(m.group(1)).replace("\u2019", "'")
        if _ifade_kapsar(turkish_text, m.start(), m.end()):
            return m.group(0)
        h = dictionary.lookup_exact(w)
        if not h or not (_HEMZE_HARF & set(h[0])) or " " in h[0].strip() or len(saklanan) > 6000:
            return m.group(0)
        saklanan.append(h[0].replace("\u06af", "\u0643"))
        return "\ue036" + chr(0xe700 + len(saklanan) - 1)
    metin = _HEMZE_RE.sub(sakla, turkish_text)
    if not saklanan:
        return _transliterate_text_hemzesiz(turkish_text, *args, **kwargs)
    out = _transliterate_text_hemzesiz(metin, *args, **kwargs)
    for i, yazim in enumerate(saklanan):
        out = out.replace("\ue036" + chr(0xe700 + i), yazim)
    return out


# ---- î ile biten kelimeye gelen -ye/-yi/-yim/-yiz ayrı yazılır (Hayrat: hakîkîye حقیقی یه، İlâhîyi الهی یی; 486/506 ve 523/525) ----
# Arapça dişil sıfat -iye (Arabiye عربیه) şapkasızdır, buna girmez. -yle bitişik kalır (Rabbânîyle ربّانیله).
_I_YE_RE = re.compile(r"(?<![^\W\d_])(?<![\u2018\u2019'\-\u2010])([^\W\d_]+[^\W\d_][\u00ee\u00ce])(y(?:e|i|im|iz))(?![^\W\d_])")
_I_YE_EK = {"ye": "\u06cc\u0647", "yi": "\u06cc\u06cc", "yim": "\u06cc\u0645", "yiz": "\u06cc\u0632"}
_transliterate_text_iyesiz = transliterate_text


def transliterate_text(turkish_text, *args, **kwargs):
    if not turkish_text or not re.search("[\u00ee\u00ce]y", turkish_text):
        return _transliterate_text_iyesiz(turkish_text, *args, **kwargs)
    ekler = []

    def ayir(m):
        if len(ekler) > 6000 or _ifade_kapsar(turkish_text, m.start(), m.end()):
            return m.group(0)
        ekler.append(_I_YE_EK[m.group(2).lower()])
        return m.group(1) + " \ue037" + chr(0xe800 + len(ekler) - 1)
    metin = _I_YE_RE.sub(ayir, turkish_text)
    out = _transliterate_text_iyesiz(metin, *args, **kwargs)
    for i, ek in enumerate(ekler):
        out = out.replace("\ue037" + chr(0xe800 + i), ek)
    return out


# ---- Rakamlar Osmanlıca (Hayrat ve Zahir'in kararı, 9 Ekim): 1911 -> ١٩١١. Latin harfe bitişik rakam (COVID-19) kalır ----
_RAKAM_RE = re.compile(r"(?<![A-Za-z\ue000])[0-9]+(?![A-Za-z])")


def _rakamlar(out: str) -> str:
    if not out:
        return out

    def cevir(m):
        if re.search("\ue001[\\s,.;:()\\-\u2013]*$", out[max(0, m.start() - 12):m.start()]):
            return m.group(0)            # yabancı dizinin hemen arkasındaki rakam (Paris 1959) kalır
        return "".join(chr(0x0660 + int(c)) for c in m.group(0))
    return _RAKAM_RE.sub(cevir, out)


# ---- Bağlam kuralları (elle, app/data/baglam_kurallari.tsv): komşu kelimeye göre yazım (arz etti عرض، kat eden قطع) ----
# En dış katman: kural tutan kelime yer tutucuyla saklanır, iç katmanlar onu görmez. Kural tutmazsa çıktı aynen eskisi.
# OSM_BAGLAM_KURAL=0 kapatır.
_BK = {}                 # kelime -> [(yazım, [(yer, derlenmiş ifade), ...], etmek), ...]
_BK_ETMEK = (r"(et|ett\w*|etm\w*|ets\w*|eder\w*|eden\w*|edip|ediyor\w*|edil\w*|edece\w*|ederek|edeli\w*"
             r"|edemez\w*|eyle\w*|olun\w*)")
_BK_NOKTA = ".,;:!?\"()[]«»“”…"


def _bk_yukle():
    yol = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "data", "baglam_kurallari.tsv")
    if _os.environ.get("OSM_BAGLAM_KURAL", "1") == "0" or not _os.path.exists(yol):
        return
    for satir in open(yol, encoding="utf-8"):
        if satir.startswith("#") or not satir.strip():
            continue
        p = satir.rstrip("\n").split("\t")
        if len(p) < 3:
            continue
        kosullar = []
        etmek = "@ETMEK" in p[2]
        for k in p[2].split(" & "):
            yer, ifade = k.split(":", 1)
            kosullar.append((yer.strip(), re.compile(ifade.strip().replace("@ETMEK", _BK_ETMEK))))
        _BK.setdefault(turkish_lower(p[0]), []).append((p[1], kosullar, etmek))


_bk_yukle()
_transliterate_text_kuralsiz = transliterate_text


def _bk_tutar(kosullar, komsu):
    for yer, ifade in kosullar:
        adaylar = [komsu[y] for y in ("L2", "L1", "R1", "R2")] if yer == "C" else [komsu.get(yer, "#")]
        if not any(a != "#" and ifade.fullmatch(a) for a in adaylar):
            return False
    return True


def transliterate_text(turkish_text, *args, **kwargs):
    if not _BK or not turkish_text:
        return _transliterate_text_kuralsiz(turkish_text, *args, **kwargs)
    saklanan, parca, son = [], [], 0
    for par in re.finditer(r"[^\n]+", turkish_text):
        toks = []
        for m in re.finditer(r"\S+", par.group(0)):
            ham = m.group(0)
            ic = ham.strip(_BK_NOKTA)
            if not ic:
                continue
            bas = par.start() + m.start() + (len(ham) - len(ham.lstrip(_BK_NOKTA)))
            toks.append((turkish_lower(ic), bas, bas + len(ic)))
        for i, (k, a, b) in enumerate(toks):
            if k not in _BK or a < son or len(saklanan) > 1000:
                continue
            komsu = {}
            for d, ad in ((-1, "L1"), (1, "R1"), (-2, "L2"), (2, "R2")):
                j = i + d
                komsu[ad] = toks[j][0] if 0 <= j < len(toks) else "#"
            for yazim, kosullar, etmek in _BK[k]:
                if _bk_tutar(kosullar, komsu):
                    parca.append(turkish_text[son:a] + "\ue038" + chr(0xea00 + len(saklanan)))
                    saklanan.append(yazim)
                    son = b
                    if etmek and komsu["R1"] == "et":
                        # yer tutucu iç bağlam katmanının ipucunu (Arapça isim + et) sakladığı için yalın "et" de burada yazılır
                        _, a2, b2 = toks[i + 1]
                        parca.append(turkish_text[son:a2] + "\ue038" + chr(0xea00 + len(saklanan)))
                        saklanan.append("\u0627\u06cc\u062a")      # ایت
                        son = b2
                    break
    if not saklanan:
        return _transliterate_text_kuralsiz(turkish_text, *args, **kwargs)
    out = _transliterate_text_kuralsiz("".join(parca) + turkish_text[son:], *args, **kwargs)
    for i, yazim in enumerate(saklanan):
        out = out.replace("\ue038" + chr(0xea00 + i), yazim)
    return out


# ---- Tur G (13 Ekim): en dış katman — Latin metinde ön düzeltme (bütün katmanlardan önce) ----
_transliterate_text_ongorusuz = transliterate_text
_IYE_IZAFET = re.compile(r"((?<=[tTeEaA])-[yY]?[ıiuüIİ]\s+[^\W\d_]{3,}?)[îÎ](y[ae])(?![^\W\d_])")   # dişil isim (hikmet, kudret, kuvve): maksad-ı hakîkîye yönelme


def transliterate_text(turkish_text, *args, **kwargs):
    """İzafetteki Arapça dişil sıfat -îye bitişik yazılır (hikmet-i umumîye حكمت عمومیه; isim + yönelme terakkîye ترقّی یه ayrı kalır);
    bitişik yazılmış sayılar ayrılır (onbir اون بر، Yirmiikinci یكرمی ایكنجی)."""
    if isinstance(turkish_text, str) and turkish_text:
        turkish_text = _sayilari_ayir(_IYE_IZAFET.sub(r"\1i\2", turkish_text))
    return _transliterate_text_ongorusuz(turkish_text, *args, **kwargs)
