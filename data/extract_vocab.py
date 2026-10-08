# -*- coding: utf-8 -*-
import sys, re
sys.path.insert(0, "/app")
from extractors.extract import extract_text
from engine.dictionary import DICTIONARY

WORD_RE = re.compile(r"[A-Za-zÇçĞğİıÖöŞşÜüÂâÎîÛû]+")

def main():
    if len(sys.argv) < 3:
        print("Kullanım: extract_vocab.py <girdi_dosyasi> <cikti_txt>")
        sys.exit(1)
    text = extract_text(sys.argv[1])
    words = WORD_RE.findall(text)
    unique = sorted(set(w.lower() for w in words if len(w) > 1))
    missing = [w for w in unique if w not in DICTIONARY]
    with open(sys.argv[2], "w", encoding="utf-8") as f:
        for w in missing:
            f.write(w + "\n")
    print(f"Toplam benzersiz kelime: {len(unique)}")
    print(f"Sözlükte olmayan (eklenecek): {len(missing)}")

if __name__ == "__main__":
    main()
