# -*- coding: utf-8 -*-
"""
Ana orkestrasyon: girdi metnini alır, gerekiyorsa Türkçeye çevirir,
sonra cümleleri gruplar halinde Osmanlıcaya (Arap harfli) çevirip Ollama ile inceltir.
"""
import re
import unicodedata
import logging
from langdetect import detect, DetectorFactory

from . import dictionary
from . import rules
from .alphabet import turkish_lower
from . import ollama_client

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
            harmony = rules._harmony_class(turkish_lower(word).replace("'", ""))
            hit, sufs = dictionary.lookup_with_suffix(base)
            b = turkish_lower(base).replace("'", "")
            tails_l = [turkish_lower(t) for t in tails if t]
            if hit:
                root = b[: len(b) - len("".join(sufs))] if sufs else b
                return hit[0] + rules.ekleri_yaz(root, sufs, tails_l, harmony, rules.ek_guvenilir(root, sufs))
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
        return rules.transliterate_word_with_suffix(word)

    def tirnak_eki(m):
        kelime, isaret, ek = m.group(1), m.group(2), m.group(3)
        if not _ek_mi(turkish_lower(ek)):
            return m.group(0)
        tam = _ek_duzelt(repl(_Eslesme(kelime + "'" + ek)))
        kok = _ek_duzelt(repl(_Eslesme(kelime)))
        if not tam.startswith(kok):
            return m.group(0)
        return kok + isaret + tam[len(kok):]

    sentence = _TIRNAK_EK_RE.sub(tirnak_eki, sentence)
    return WORD_RE.sub(lambda m: _lerin_eki(m.group(0), _matbaa_ekleri(m.group(0), _ek_duzelt(repl(m)))), sentence)


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
    if re.search(r"[pçtksşhf]t[ae]n$", l) and re.search(r"(تان|تن)$", osm) and len(l) > 4:   # yaratan, tutan değil
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
    if re.search(r"[^aeıioöuüâîû][ea]bil", l) and "بیل" in osm:
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
    if re.search(r"[^aeıioöuüâîû][uü]yl[ae]$", l) and osm.endswith("ویله"):
        osm = osm[:-4] + "یله"
    # ayrılma eki -dan matbaada دن (sözlükte olmayan kelimede): قیزدن
    if l.endswith("dan") and osm.endswith("دان") and not dictionary.lookup_exact(l):
        osm = osm[:-3] + "دن"
    # kazan-: قزانمق؛ ön (eski ñ): اوڭنده
    if l.startswith("kazan") and osm.startswith("قازان"):
        osm = "قزان" + osm[5:]
    if re.match(r"^ön(ü|e|de|den|ce|üm|ün)", l) and osm.startswith("اون"):
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
    if l.startswith("öl") and osm.startswith("اول"):
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
    if "hane" in l and "هانه" in osm:
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
        osm = re.sub(r"(?:ین|ون)(ده|دن|دهكی|دكی|ی|ه|ڭ)(در)?$", r"ن\1\2", osm)
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
        # -et ile biten isim + hâl eki/ek-fiil (âhiret+te, rahmet+ten, rahmet+tir, mâhiyet+e+dir) fiil değildir
        if re.match(r"^(ette|ete|eti|etin|etle|eten|etten|ettir|ettirler|ettı|edir|edirler)$", kuyruk) or \
                re.match(r"^(ette|etten|etle)", kuyruk):
            continue
        kok = w[:k]
        if kuyruk.startswith("ede") and dictionary.lookup_exact(kok + "e"):
            continue                       # halke+den (حلقه) gibi: isim + ayrılma eki olabilir
        if kok[-1] in "aeıioöuüâîû" or (kok.endswith("y") and kok[-2:-1] in "iî"):
            continue                       # İlahiye+den gibi isim çekimi; ünlüyle biten kök birleşik fiil olmaz
        adaylar = [kok]
        if len(kok) >= 3 and kok[-1] == kok[-2]:
            adaylar.append(kok[:-1])       # hiss+etmek -> his, zann+etmek -> zan, redd -> red
        for a in adaylar:
            h = dictionary.lookup_exact(a)
            if h and h[1] in ("ar", "fa", "ar-fa", "fa-ar") and len(a) >= 2:
                return h[0] + " " + rules.transliterate_word_with_suffix(kuyruk)
    return None


class _Eslesme:
    """repl() için WORD_RE eşleşmesi gibi davranan küçük sarmalayıcı."""
    def __init__(self, metin):
        self._m = metin

    def group(self, i=0):
        return self._m


# Kapanan tırnak/parantezden hemen sonra boşluksuz gelen Türkçe ek: “O”dur, “Hak”tan, (Rahman)'a değil
_TIRNAK_EK_RE = re.compile(r"([A-Za-zÇçĞğİıÖöŞşÜüÂâÎîÛû]+(?:['’][A-Za-zÇçĞğİıÖöŞşÜüÂâÎîÛû]+)*)([”\"»\)\]]+)([a-zçğıöşüâîû]{1,9})(?![A-Za-zÇçĞğİıÖöŞşÜüÂâÎîÛû'’])")


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


def _ek_duzelt(w: str) -> str:
    return w[:-4] + "یله" if w.endswith("ییله") else w


BATCH_SIZE = int(__import__("os").environ.get("OLLAMA_BATCH_SIZE", "12"))


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
    return _IZAFET_RE.sub(lambda m: "\ue010" if m.group(0)[1:2] in "yY" else "\ue011", text)


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
    (re.compile(r"(?<=\()\s*a\.\s?s\.?\s*(?=\))", re.I), "علیه السلام"),
    (re.compile(r"(?<![\w.])r\.\s?a\.?(?![\w])", re.I), "رضی الله عنه"),
]


_PARANTEZ_EKI = {"nin": "ڭ", "nın": "ڭ", "nun": "ڭ", "nün": "ڭ", "in": "ڭ", "ın": "ڭ", "un": "ڭ", "ün": "ڭ",
                 "ye": "ه", "ya": "ه", "e": "ه", "a": "ه", "de": "ده", "da": "ده", "te": "ده", "ta": "ده",
                 "den": "دن", "dan": "دن", "ten": "دن", "tan": "دن", "yi": "ی", "yı": "ی", "i": "ی", "ı": "ی",
                 "le": "له", "la": "له", "yle": "یله", "yla": "یله"}
_PARANTEZ_EK_RE = re.compile(r"(?<=[\u0600-\u06FF])([)\]”])['’]?(" + "|".join(sorted(_PARANTEZ_EKI, key=len, reverse=True))
                             + r")(?![A-Za-zÇçĞğİıÖöŞşÜüÂâÎîÛû])")


def _kisaltmalar(metin: str) -> str:
    metin = re.sub(r"\bHz\.\s*", "Hazret ", metin)          # Hz. Muhammed -> حضرت محمّد
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
    use_ollama_refine: bool = True,
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
    """Türkçe metni (zaten Türkçe olduğu varsayılır) Osmanlıcaya çevirir.
    Ollama'ya cümle cümle değil, BATCH_SIZE'lık gruplar halinde TEK istekte
    gönderir - bu, istek sayısını (ve dolayısıyla süreyi) ciddi oranda azaltır."""
    parts = SENTENCE_SPLIT_RE.split(turkish_text)
    sentences = parts[0::2]
    separators = parts[1::2]
    ollama_up = use_ollama_refine and ollama_client.is_available()
    if use_ollama_refine and not ollama_up:
        logger.warning("Ollama'ya ulaşılamadı, sadece kural motoru taslağı kullanılacak.")

    total = len(sentences)
    out_sentences = [""] * total
    done = 0

    non_empty_idx = [i for i, s in enumerate(sentences) if s.strip()]
    for i in non_empty_idx:
        out_sentences[i] = draft_transliterate_sentence(sentences[i])
    for i, s in enumerate(sentences):
        if not s.strip():
            out_sentences[i] = s

    if ollama_up and non_empty_idx:
        for batch_start in range(0, len(non_empty_idx), BATCH_SIZE):
            batch_idx = non_empty_idx[batch_start:batch_start + BATCH_SIZE]
            pairs = [(sentences[i], out_sentences[i]) for i in batch_idx]
            refined = ollama_client.refine_ottoman_batch(pairs)
            for i, r in zip(batch_idx, refined):
                out_sentences[i] = r
            done += len(batch_idx)
            if progress_callback:
                progress_callback(done, total)
    else:
        if progress_callback:
            progress_callback(total, total)

    result = []
    for i, s in enumerate(out_sentences):
        result.append(s)
        if i < len(separators):
            result.append("\n" if "\n" in separators[i] else " ")
    sonuc = _ottoman_punctuation("".join(result))
    sonuc = re.sub(r"(?<=[\u0621-\u06D3]) كه(?=[\s،.!؟:؛\"”]|$)", "كه", sonuc)   # ki öncesine bitişik: ناصلكه، واردركه
    return _yabancilari_geri_koy(sonuc, _saklanan)


def _ottoman_punctuation(text: str) -> str:
    """Latin noktalamayı Osmanlıca karşılıklarına çevirir: , -> ،  ; -> ؛  ? -> ؟
    (Sayıların içindeki virgüle dokunmaz: 3,5 aynen kalır.)"""
    text = re.sub(r",(?!\d)|(?<!\d),", "\u060c", text)
    return text.replace(";", "\u061b").replace("?", "\u061f")


def full_pipeline(
    raw_text: str,
    use_ollama_refine: bool = True,
    progress_callback=None,
    assume_turkish: bool = False,
) -> dict:
    """Tam hat: dil tespiti -> (gerekirse) Türkçeye çeviri -> Osmanlıca çeviri."""
    # assume_turkish: metin zaten Türkçe (ör. Dedplay Stüdyo); dil tespiti atlanır,
    # kısa/yabancı isimli metinler yanlışlıkla "başka dil" sanılıp çevrilmez.
    lang = "tr" if assume_turkish else detect_language(raw_text)
    ollama_up = ollama_client.is_available() if lang != "tr" else False

    if lang != "tr":
        if ollama_up:
            turkish_text = ollama_client.translate_to_turkish(raw_text, source_lang_hint=lang)
        else:
            raise RuntimeError(
                f"Girdi Türkçe değil (tespit edilen dil: {lang}) ve Ollama'ya "
                f"ulaşılamadığı için önce Türkçeye çevrilemedi."
            )
    else:
        turkish_text = raw_text

    ottoman_text = transliterate_text(
        turkish_text, use_ollama_refine=use_ollama_refine, progress_callback=progress_callback
    )

    return {
        "detected_lang": lang,
        "turkish_text": turkish_text,
        "ottoman_text": ottoman_text,
    }



# ---- İmlâ: izafet işaretleri ve isimlerdeki "bin" (transliterate_text sarmalayıcısı) ----
_transliterate_text_ilk = transliterate_text
_BIN_ISIM_RE = re.compile(r"([A-ZÇĞİÖŞÜÂÎÛ][^\s]*\s)bin(?=\s[A-ZÇĞİÖŞÜÂÎÛ])")


def transliterate_text(turkish_text, *args, **kwargs):
    """İzafet: ه ile biten kelimede hemze (رسالهٔ نور, قوّهٔ معنویه), "-yı/-yi"de ی (دنیای فانی), ünsüzden sonra yazılmaz.
    İki özel ismin arasındaki "bin" بن (Ali bin Ebî Tâlib); öteki "bin" sözlükten (sayı: بیڭ)."""
    turkish_text = _BIN_ISIM_RE.sub("\\1\ue012", turkish_text)
    out = _transliterate_text_ilk(turkish_text, *args, **kwargs)
    out = out.replace("\ue012", "بن").replace("\ue010", "ی")
    out = re.sub("\u0647\ue011", "\u0647\u0654", out)
    out = out.replace("\ue011", "")
    out = re.sub("[\u2018\u2019'`\u02bf\u02be]", "", out)   # ayın/hemze işareti Osmanlıcaya harf olarak geçmez
    return out.replace("\u06af", "\u0643")                  # g sesi Hayrat gibi kef (ك) ile; ڭ kalır
