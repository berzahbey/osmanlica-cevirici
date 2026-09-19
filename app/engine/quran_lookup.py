# -*- coding: utf-8 -*-
"""
Kur'an'in tam Arapca metnine (Tanzil/risan-quran-json kaynagi,
verbatim/degistirilmeden kullanilir, kaynak: risan/quran-json GitHub,
Uthmani metin The Noble Quran Encyclopedia'dan) sure:ayet ile erisim.

Kullanim amaci: Kur'an cevirisi sirasinda karsilasilan nadir/teknik
Arapca kelimeler icin (orn. "kuvviret", "succirat") kural motorunun
tahmin etmesi yerine, GERCEK ayet metninden dogru kelimeyi bulmak.
"""
import json
from pathlib import Path

DATA_FILE = Path(__file__).parent.parent / "data" / "quran_arabic.json"

_quran_data = None


def _load():
    global _quran_data
    if _quran_data is None:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            _quran_data = json.load(f)
    return _quran_data


def get_ayah(sura: int, ayah: int) -> str:
    """Verilen sure ve ayet numarasina karsilik gelen Arapca metni dondurur.
    Bulunamazsa None doner. sura/ayah 1-tabanlidir (Kur'an'daki gibi)."""
    data = _load()
    sura_list = data.get(str(sura))
    if not sura_list:
        return None
    if ayah < 1 or ayah > len(sura_list):
        return None
    return sura_list[ayah - 1]["text"]


def search_word_in_sura(sura: int, latin_hint: str) -> list:
    """Bir surenin tum ayetlerini dondurur (ayet_no, arapca_metin) - kullanici/
    Claude, hangi ayette hangi kelimenin gectigini gozle kontrol edebilsin diye.
    latin_hint su an sadece dokumantasyon amacli, filtreleme yapmiyor
    (Arapca kok eslestirme karmasik oldugu icin bilingual arama yapilmiyor)."""
    data = _load()
    sura_list = data.get(str(sura))
    if not sura_list:
        return []
    return [(v["verse"], v["text"]) for v in sura_list]


def sura_count() -> int:
    return len(_load())


def ayah_count(sura: int) -> int:
    data = _load()
    sura_list = data.get(str(sura))
    return len(sura_list) if sura_list else 0
