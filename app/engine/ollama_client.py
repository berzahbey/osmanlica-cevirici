# -*- coding: utf-8 -*-
"""
Yerel Ollama sunucusuna bağlanıp iki iş için kullanır:
  1. Türkçe olmayan girdi metnini Türkçeye çevirmek (translate_to_turkish)
  2. Kural motorunun ürettiği Osmanlıca taslağını, orijinal cümleyle birlikte
     modele gösterip kelime kökenine göre düzelttirmek (refine_ottoman_batch)

OLLAMA_HOST ve OLLAMA_MODEL ortam değişkenleriyle yapılandırılır (bkz. docker-compose.yml).
"""
import os
import re
import requests

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://host.docker.internal:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:14b")
TIMEOUT = int(os.environ.get("OLLAMA_TIMEOUT", "300"))


def _generate(prompt: str, system: str = None) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1},
    }
    if system:
        payload["system"] = system
    resp = requests.post(f"{OLLAMA_HOST}/api/generate", json=payload, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json().get("response", "").strip()


def translate_to_turkish(text: str, source_lang_hint: str = "") -> str:
    system = (
        "Sen uzman bir çevirmensin. Sana verilen metni, anlamını ve üslubunu "
        "koruyarak akıcı, düzgün MODERN TÜRKÇEYE çevir. SADECE çeviriyi yaz, "
        "açıklama, not veya başka bir şey ekleme."
    )
    hint = f" (Kaynak dil muhtemelen: {source_lang_hint})" if source_lang_hint else ""
    prompt = f"Aşağıdaki metni Türkçeye çevir{hint}:\n\n{text}"
    return _generate(prompt, system=system)


def refine_ottoman_line(original_turkish: str, draft_ottoman: str) -> str:
    system = (
        "Sen Osmanlı Türkçesi (Osmanlıca) imlası konusunda uzman bir dil bilginisin. "
        "Sana modern Türkçe bir cümle ve bunun kaba/otomatik üretilmiş Osmanlıca "
        "(Arap harfli) taslağı verilecek. Görevin: taslaktaki imla hatalarını, "
        "kelimenin Arapça/Farsça/Türkçe kökenine göre doğru Osmanlıca yazım "
        "kurallarını uygulayarak düzeltmek. SADECE düzeltilmiş Osmanlıca metni "
        "(Arap harfleriyle) yaz. Açıklama, transkripsiyon, Latin harf yazma. "
        "Emin olmadığın kelimeleri taslaktaki haliyle bırak, uydurma."
    )
    prompt = (
        f"Orijinal Türkçe cümle:\n{original_turkish}\n\n"
        f"Kaba Osmanlıca taslağı:\n{draft_ottoman}\n\n"
        f"Düzeltilmiş Osmanlıca:"
    )
    try:
        result = _generate(prompt, system=system)
        return result if result else draft_ottoman
    except Exception:
        return draft_ottoman


def refine_ottoman_batch(pairs: list) -> list:
    """pairs: [(original_turkish, draft_ottoman), ...] - hepsini TEK istekte
    gönderir, tek tek göndermekten çok daha hızlıdır."""
    if not pairs:
        return []

    numbered_input = "\n".join(
        f"{i+1}) TÜRKÇE: {orig}\n{i+1}) TASLAK: {draft}"
        for i, (orig, draft) in enumerate(pairs)
    )
    system = (
        "Sen Osmanlı Türkçesi (Osmanlıca) imlası konusunda uzman bir dil bilginisin. "
        "Sana numaralanmış birden çok satır çifti verilecek: her numara için önce "
        "modern Türkçe cümle, sonra kaba/otomatik üretilmiş Osmanlıca (Arap harfli) "
        "taslağı var. Görevin: HER numara için taslaktaki imla hatalarını, kelimenin "
        "Arapça/Farsça/Türkçe kökenine göre doğru Osmanlıca yazım kurallarını "
        "uygulayarak düzeltmek.\n"
        "ÇOK ÖNEMLİ ÇIKTI FORMATI: SADECE şu formatta, aynı sayıda satır döndür:\n"
        "1) <düzeltilmiş osmanlıca metin>\n2) <düzeltilmiş osmanlıca metin>\n...\n"
        "Açıklama, Latin harf, Türkçe metin YAZMA. Sadece Arap harfli sonucu yaz. "
        "Emin olmadığın kelimeleri taslaktaki haliyle bırak, uydurma. Satır sayısı "
        "girdiyle birebir aynı olmalı, hiçbirini atlama ya da birleştirme."
    )
    prompt = f"{numbered_input}\n\nDüzeltilmiş Osmanlıca satırlar (yukarıdaki formatta):"

    try:
        raw = _generate(prompt, system=system)
    except Exception:
        return [draft for _, draft in pairs]

    results = [None] * len(pairs)
    for line in raw.split("\n"):
        line = line.strip()
        if not line:
            continue
        m = re.match(r"^(\d+)\)\s*(.*)$", line)
        if m:
            idx = int(m.group(1)) - 1
            if 0 <= idx < len(pairs):
                results[idx] = m.group(2).strip()

    return [
        results[i] if results[i] else pairs[i][1]
        for i in range(len(pairs))
    ]


def is_available() -> bool:
    try:
        r = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        return r.status_code == 200
    except Exception:
        return False
