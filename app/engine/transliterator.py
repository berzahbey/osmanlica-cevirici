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
            harmony = rules._harmony_class(turkish_lower(word).replace("'", ""))
            hit, sufs = dictionary.lookup_with_suffix(base)
            if hit:
                base_osmanli = hit[0]
                if sufs:
                    for suf in sufs:
                        base_osmanli = base_osmanli + rules._transliterate_suffix(suf, harmony)
            else:
                base_osmanli = rules.transliterate_word_with_suffix(base)
            for tail in tails:
                if tail:
                    base_osmanli = base_osmanli + rules._transliterate_suffix(tail.lower(), harmony)
            return base_osmanli

        hit, sufs = dictionary.lookup_with_suffix(word)
        if hit:
            osmanli = hit[0]
            if sufs:
                harmony = rules._harmony_class(turkish_lower(word))
                for suf in sufs:
                    osmanli = osmanli + rules._transliterate_suffix(suf, harmony)
            return osmanli
        return rules.transliterate_word_with_suffix(word)

    return WORD_RE.sub(repl, sentence)


BATCH_SIZE = int(__import__("os").environ.get("OLLAMA_BATCH_SIZE", "12"))


def _merge_orphan_numbers(text: str) -> str:
    """Sadece 'N.' veya 'N)' iceren satirlari, hemen sonraki satirla
    birlestirir (PDF'ten cikan numarali liste bicimlendirmesi numarayi
    metinden ayri bir satira koyabiliyor)."""
    import re
    return re.sub(r'(?m)^([ \t]*\d+[.\)])[ \t]*\n[ \t]*', r'\1 ', text)


def transliterate_text(
    turkish_text: str,
    use_ollama_refine: bool = True,
    progress_callback=None,
) -> str:
    turkish_text = _merge_orphan_numbers(turkish_text)
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
    return "".join(result)


def full_pipeline(
    raw_text: str,
    use_ollama_refine: bool = True,
    progress_callback=None,
) -> dict:
    """Tam hat: dil tespiti -> (gerekirse) Türkçeye çeviri -> Osmanlıca çeviri."""
    lang = detect_language(raw_text)
    ollama_up = ollama_client.is_available()

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
