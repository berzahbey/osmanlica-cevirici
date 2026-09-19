# -*- coding: utf-8 -*-
"""
Osmanlı Türkçesi (Ottoman Turkish) alfabe tabloları.

Bu dosya, harf çevirisi motorunun kullandığı temel karakter eşlemelerini içerir.
Osmanlı alfabesi, Arap alfabesinin Türkçe, Farsça ekleriyle genişletilmiş halidir.

Kaynak: Genel kabul görmüş Osmanlıca imla kuralları (Redhouse, Develioğlu ve
Osmanlı matbu eserlerinde kullanılan standart yeni-Osmanlı imlası temel alınmıştır).
Bu bir YAKLAŞIMdır; kesin/otoriter değildir ve dictionary.py ile zaman içinde
zenginleştirilmelidir.
"""

# Sesli harfler için taşıyıcı harfler (med harfleri)
ELIF = "ا"      # a, e (kelime başında her zaman; ortada bazen)
VAV = "و"       # o, ö, u, ü, v
YE = "ی"        # i, ı, î, y
HE = "ه"        # e (kelime sonunda; ayrica "h" unsuzu icin de kullanilir)
HEMZE = "ء"
HEMZE_ELIF = "أ"
MEDD_ELIF = "آ"  # â (uzun a)

# Kalın (arka) ünsüzler - Türkçe kökenli kelimelerde kalın ünlülerle (a,ı,o,u) birlikte
KALIN_KEF = "ق"   # kalın k (kapı -> kef değil kaf)
KALIN_GEF = "غ"   # kalın g/ğ (yağ, dağ)
SAGIR_KEF = "ڭ"   # nazal n (geleneksel Osmanlıca'da bazı kelimelerde, ör. "dahi"nin eski yazımı, "onun" vb.) - opsiyonel/eskicil

# İnce (ön) ünsüzler - ince ünlülerle (e,i,ö,ü) birlikte
INCE_KEF = "ك"    # ince k (ekmek, kedi)
INCE_GEF = "گ"    # ince g (gemi, gel)

# Türkçeye özgü ek harfler (Arapçada olmayan sesler için, Farsçadan alınmıştır)
PEH = "پ"    # p
CHEH = "چ"   # ç
JEH = "ژ"    # j (jandarma gibi batı kökenli kelimelerde)

# Standart Arapça harfler (Arapça/Farsça kökenli kelimelerde ORİJİNAL İMLASI korunur,
# bu yüzden bu harfler sadece köken kelimenin bilindiği sözlük eşlemesinde kullanılır,
# kural motoru saf Türkçe kelimeler için bunları ÜRETMEZ):
ARABIC_ONLY_LETTERS = {
    "ث": "peltek s (Arapça kökenli, örn: müsbet -> ثابت kökünden)",
    "ح": "gırtlaktan h (Arapça kökenli, örn: rahat)",
    "ذ": "peltek z (Arapça kökenli)",
    "ص": "kalın s (Arapça kökenli)",
    "ض": "kalın z/d (Arapça kökenli)",
    "ط": "kalın t (Arapça kökenli)",
    "ظ": "kalın z (Arapça kökenli)",
    "ع": "ayn - gırtlak sesi (Arapça kökenli)",
    "ك ile قâف arası ق": "kaf",
}

# Türkçe Latin harften Osmanlıca'ya SADE ünsüz eşlemesi
# (Bu eşleme, sözlükte bulunamayan SAF TÜRKÇE kelimeler için kural motorunda kullanılır.
#  Arapça/Farsça kökenli kelimeler İÇİN KULLANILMAZ - onlar dictionary.py'den gelir
#  ya da Ollama'nın önerdiği orijinal imla ile yazılır.)
CONSONANT_MAP_TURKISH = {
    "b": "ب", "c": "ج", "ç": CHEH, "d": "د", "f": "ف",
    "g": None,  # bağlama göre INCE_GEF / KALIN_GEF - rules.py'de çözülür
    "ğ": None,  # bağlama göre KALIN_GEF ya da düşürülür - rules.py'de çözülür
    "h": "ه", "j": JEH, "k": None,  # bağlama göre INCE_KEF / KALIN_KEF
    "l": "ل", "m": "م", "n": "ن", "p": PEH, "r": "ر",
    "s": "س", "ş": "ش", "t": "ت", "v": "و", "y": YE, "z": "ز",
    "w": "و", "x": "كس", "q": KALIN_KEF,
}

# İnce/kalın ünlü sınıfları (Türkçe ünlü uyumu için)
KALIN_UNLULER = set("aıouâû")
INCE_UNLULER = set("eiöüî")
TUM_UNLULER = KALIN_UNLULER | INCE_UNLULER

# Ünlülerin taşıyıcı harfleri (kelime başında ve bazı pozisyonlarda zorunlu)
VOWEL_CARRIER = {
    "a": ELIF, "e": ELIF, "â": MEDD_ELIF,
    "ı": YE, "i": YE, "î": YE,
    "o": VAV, "ö": VAV, "u": VAV, "ü": VAV, "û": VAV,
}


def turkish_lower(s: str) -> str:
    """Python'un standart .lower()'i Turkce noktali buyuk 'I'yi (Iistanbul)
    yanlis cevirir (goze gorunmeyen 'combining dot' karakteri ekler).
    Bu fonksiyon Turkce kurallarina gore dogru kucuk harfe cevirir:
    İ -> i, I -> ı, sonra geri kalanini normal lower() ile."""
    s = s.replace("İ", "i").replace("I", "ı")
    return s.lower()
