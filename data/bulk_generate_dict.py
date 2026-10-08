# -*- coding: utf-8 -*-
import sys, os, re, time
sys.path.insert(0, "/app")
from engine.ollama_client import _generate, OLLAMA_MODEL

DICT_FILE = "/app/data/ottoman_dict.tsv"
BATCH_SIZE = int(os.environ.get("DICT_BATCH_SIZE", "30"))

SYSTEM = (
    "Sen Osmanlı Türkçesi (Osmanlıca) imlası konusunda uzman bir dil bilginisin. "
    "Sana numaralanmış Türkçe kelime listesi verilecek. Her kelime için: "
    "(a) doğru klasik Osmanlıca (Arap harfli) yazımını, "
    "(b) kökenini (ar=Arapça, fa=Farsça, tr=Türkçe, other=diğer) belirt.\n"
    "ÇOK ÖNEMLİ ÇIKTI FORMATI: SADECE şu formatta, aynı sayıda satır döndür:\n"
    "1) <osmanlica_yazim><TAB><koken>\n2) <osmanlica_yazim><TAB><koken>\n...\n"
    "Açıklama yazma. Emin olmadığın kelimeler için en olası yazımı ver, boş bırakma."
)

def already_done():
    done = set()
    if os.path.exists(DICT_FILE):
        with open(DICT_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("#") or not line.strip():
                    continue
                parts = line.split("\t")
                if parts:
                    done.add(parts[0].strip().lower())
    return done

def process_batch(words):
    numbered = "\n".join(f"{i+1}) {w}" for i, w in enumerate(words))
    prompt = f"{numbered}\n\nYukarıdaki kelimelerin Osmanlıca yazımı ve kökeni:"
    raw = _generate(prompt, system=SYSTEM)
    results = [None] * len(words)
    for line in raw.split("\n"):
        line = line.strip()
        m = re.match(r"^(\d+)\)\s*(.+)$", line)
        if not m:
            continue
        idx = int(m.group(1)) - 1
        if not (0 <= idx < len(words)):
            continue
        rest = m.group(2).strip()
        if "\t" in rest:
            osmanli, koken = rest.split("\t", 1)
        else:
            parts = rest.rsplit(None, 1)
            if len(parts) == 2 and parts[1].lower() in ("ar", "fa", "tr", "other"):
                osmanli, koken = parts[0], parts[1]
            else:
                osmanli, koken = rest, "other"
        results[idx] = (osmanli.strip(), koken.strip().lower())
    return results

def main():
    if len(sys.argv) < 2:
        print("Kullanım: bulk_generate_dict.py <vocab_missing.txt>")
        sys.exit(1)
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        words = [w.strip() for w in f if w.strip()]
    done = already_done()
    todo = [w for w in words if w.lower() not in done]
    print(f"Toplam: {len(words)}, zaten var: {len(words)-len(todo)}, işlenecek: {len(todo)}")
    print(f"Model: {OLLAMA_MODEL}, batch: {BATCH_SIZE}")
    with open(DICT_FILE, "a", encoding="utf-8") as out:
        for start in range(0, len(todo), BATCH_SIZE):
            batch = todo[start:start + BATCH_SIZE]
            t0 = time.time()
            try:
                results = process_batch(batch)
            except Exception as e:
                print(f"[HATA] batch {start}: {e}, atlanıyor")
                continue
            for word, res in zip(batch, results):
                if res is None:
                    print(f"  [atlandı] {word}")
                    continue
                osmanli, koken = res
                out.write(f"{word}\t{osmanli}\t{koken}\n")
            out.flush()
            print(f"[{min(start+BATCH_SIZE,len(todo))}/{len(todo)}] tamamlandı ({time.time()-t0:.1f}s)")
    print("Bitti. ottoman_dict.tsv güncellendi.")

if __name__ == "__main__":
    main()
