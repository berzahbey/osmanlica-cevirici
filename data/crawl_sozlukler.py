# -*- coding: utf-8 -*-
"""
osmanlicasozlukler.com'dan (ucretsiz, kisitlamasiz kullanim beyanli)
Latin+Osmanlica esli sozluk maddelerini tarar.
"""
import re
import sys
import time
import requests

ENTRY_RE = re.compile(
    r'<a href="[^"]*tafsil-[^"]*\.html"\s+class="alfabe-card"\s+title="([^"]*)">.*?<span>([^<]*)</span>',
    re.DOTALL
)

def crawl(slug: str, out_path: str, max_pages: int = 500, delay: float = 0.4):
    seen = {}
    page = 1
    empty_streak = 0
    while page <= max_pages:
        url = f"https://www.osmanlicasozlukler.com/{slug}/latin.html"
        if page > 1:
            url += f"?s={page}"
        try:
            resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
        except Exception as e:
            print(f"[HATA] sayfa {page}: {e}")
            break

        matches = ENTRY_RE.findall(resp.text)
        if not matches:
            empty_streak += 1
            if empty_streak >= 3:
                print(f"Ust uste 3 bos sayfa, duruluyor (sayfa {page})")
                break
        else:
            empty_streak = 0
            for ottoman, latin in matches:
                latin_clean = latin.strip().lower()
                if latin_clean and latin_clean not in seen:
                    seen[latin_clean] = ottoman.strip()

        if page % 20 == 0:
            print(f"[{page}. sayfa] toplam benzersiz kelime: {len(seen)}")
        page += 1
        time.sleep(delay)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"# {slug} - osmanlicasozlukler.com kaynagindan taranmistir\n")
        for latin, osmanli in sorted(seen.items()):
            f.write(f"{latin}\t{osmanli}\tsozlukler\n")

    print(f"Bitti. Toplam {len(seen)} benzersiz kelime -> {out_path}")

if __name__ == "__main__":
    slug = sys.argv[1] if len(sys.argv) > 1 else "kamusiturki"
    out = sys.argv[2] if len(sys.argv) > 2 else f"/data/{slug}_sozluk.tsv"
    crawl(slug, out)
