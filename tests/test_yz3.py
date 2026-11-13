"""Tur YZ3: güvenilir modelin Arapça/Farsça kaydı sözlüğe kök olarak girer; Lite kaydı girmez ve yeniden sorulur."""
import json
import os
import sys
import tempfile
from pathlib import Path

os.environ["YZ_SOZLUK"] = tempfile.mktemp(suffix=".tsv")
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))
from engine import yz_kayit  # noqa: E402
from engine.transliterator import transliterate_text  # noqa: E402

hata = 0


def bak(ad, olan, beklenen):
    global hata
    if olan != beklenen:
        hata += 1
        print("HATA", ad, repr(olan), "beklenen", repr(beklenen))


# harf uyumu: son ses sertleşmesi (dert درد, kast قصد)
bak("dert", yz_kayit.harf_uyumu("dert", "درد"), True)
bak("kast", yz_kayit.harf_uyumu("kast", "قصد"), True)
bak("zengin-yanlis", yz_kayit.harf_uyumu("zengin", "سنگین"), False)

# Lite kaydı: saklanır ama uygulanmaz; kelime yeniden sorulur
yz_kayit.ekle([{"kelime": "Mahmuzzuyla", "koken": "fa", "kok": "mahmuzz", "yazilis": "مهمیز", "model": "gemini-3.5-flash-lite"}])
bak("lite yeniden sorulur", "Mahmuzzuyla" in yz_kayit.bilinmeyenler("Mahmuzzuyla geldi"), True)
# güçlü model aynı kelimeyi yazınca uygulanır ve bir daha sorulmaz
yz_kayit.ekle([{"kelime": "Mahmuzzuyla", "koken": "fa", "kok": "mahmuzz", "yazilis": "مهمیز", "model": "gemini-4-hydrogen"}])
bak("guclu sorulmaz", yz_kayit.bilinmeyenler("Mahmuzzuyla geldi"), [])
bak("guclu uygulanir", "مهمیز" in transliterate_text("mahmuzzuyla"), True)
# Türkçe kelime Lite'ın Arapça sandığı yazılışla bozulmaz
yz_kayit.ekle([{"kelime": "sonuçtanz", "koken": "ar", "kok": "sonuçtanz", "yazilis": "سنوچتانز", "model": "gemini-3.5-flash-lite"}])
bak("lite uygulanmaz", "sonuçtanz" in yz_kayit.dictionary.DICTIONARY, False)
os.remove(os.environ["YZ_SOZLUK"])
print("SONUC:", "HEPSI GECTI" if not hata else f"{hata} HATA")
