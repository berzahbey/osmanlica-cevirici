# -*- coding: utf-8 -*-
"""
Ana orkestrasyon: girdi metnini alır, gerekiyorsa Türkçeye çevirir,
sonra cümleleri gruplar halinde Osmanlıcaya (Arap harfli) çevirip Ollama ile inceltir.
"""
import re
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
    return WORD_RE.sub(lambda m: _ek_duzelt(repl(m)), sentence)


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
_IZAFET_RE = re.compile(r"(?<=[^\W\d_])-(?:y)?[ıiuü](?=[\s\-–]|$)", re.M)


_ROMA = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8, "IX": 9, "X": 10,
         "XI": 11, "XII": 12, "XIII": 13, "XIV": 14, "XV": 15, "XVI": 16, "XVII": 17, "XVIII": 18, "XIX": 19, "XX": 20}
_ROMA_RE = re.compile(r"(?<![\w'’])(" + "|".join(sorted(_ROMA, key=len, reverse=True)) + r")(?![\w'’])")


def _roma_rakam(text: str) -> str:
    """Tek başına duran büyük harfli Roma rakamlarını sayıya çevirir: BÖLÜM I -> BÖLÜM 1."""
    return _ROMA_RE.sub(lambda m: str(_ROMA[m.group(1)]), text)


def _drop_izafet(text: str) -> str:
    return _IZAFET_RE.sub("", text)


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


def transliterate_text(
    turkish_text: str,
    use_ollama_refine: bool = True,
    progress_callback=None,
) -> str:
    turkish_text = _merge_orphan_numbers(turkish_text)
    turkish_text, _saklanan = _yabancilari_sakla(turkish_text)
    turkish_text = _kisaltmalar(turkish_text)
    turkish_text = _quran_phrases(turkish_text)
    turkish_text = _roma_rakam(turkish_text)
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
    return _yabancilari_geri_koy(_ottoman_punctuation("".join(result)), _saklanan)


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
