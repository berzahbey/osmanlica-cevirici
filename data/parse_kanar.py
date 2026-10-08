# -*- coding: utf-8 -*-
import fitz, re, unicodedata, sys

ARABIC_RANGE = r'\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF'
PATTERN = re.compile(
    r'([a-zA-ZâîûöüşçğıÂÎÛÖÜŞÇĞİ\'\u2019\-]+)\s*\(([A-Za-z.\-]+)\)\s*\[\s*\]([' + ARABIC_RANGE + r'\s]+)'
)

KOKEN_MAP = {
    "A.": "ar", "F.": "fa", "T.": "tr",
    "A.-F.": "ar-fa", "F.-A.": "fa-ar",
    "A.-T.": "ar-tr", "T.-A.": "tr-ar",
    "F.-T.": "fa-tr", "T.-F.": "tr-fa",
    "A.-Fr.": "ar-fr", "F.-Fr.": "fa-fr",
}

def normalize_arabic(s):
    s = unicodedata.normalize("NFKC", s)
    return s.strip()

def main():
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else "/data/kanar_sozluk.pdf"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "/data/kanar_sozluk.tsv"

    doc = fitz.open(pdf_path)
    seen = {}
    total_matches = 0

    for page in doc:
        text = page.get_text()
        for m in PATTERN.finditer(text):
            latin, koken_raw, arapca = m.groups()
            latin = latin.strip().lower().replace(chr(8217), "'")
            arapca_norm = normalize_arabic(arapca)
            koken = KOKEN_MAP.get(koken_raw.strip(), "other")
            total_matches += 1
            if latin not in seen:
                seen[latin] = (arapca_norm, koken)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("# Kanar Osmanlica sozlugunden otomatik cikarilmistir\n")
        for latin in sorted(seen.keys()):
            arapca, koken = seen[latin]
            f.write(latin + "\t" + arapca + "\t" + koken + "\n")

    print("Toplam eslesme:", total_matches)
    print("Benzersiz kelime:", len(seen))
    print("Yazildi:", out_path)

if __name__ == "__main__":
    main()
