"""Tur KE (13 Kasım 2026): kök+ek turu.
1) Kökü sözlükte doğru olan kelimenin ekli hâli: isim + ek-fiil kural motorunca fiil sanılmaz (talip+tiler, hazır+lıklı+ydılar), kökün ilk
   harfi kural motorunda ط/ت farkıyla yazılsa da kök sözlükteki yazımla değişir (tarih+çilerininse), Hayrat kök sözlüğünde olmayan kök
   sözlükteki Arapça/Farsça kayıttan alınır (sadık+sa). Hayrat'ta kelime çıkarılarak ölçüldü: 92 düzelen, 2 bozulan (takaddes, takaddüs).
2) Güçlü modelin Türkçe kaydının kökü bilinen sayılır: aynı kökün yeni ekli hâli yapay zekâya yeniden sorulmaz.
Calistirma: python tests/test_tur_ke.py"""
import logging
import os
import sys
import tempfile

logging.disable(50)
os.environ["YZ_SOZLUK"] = tempfile.mktemp(suffix=".tsv")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app"))
from engine import yz_kayit  # noqa: E402
from engine.transliterator import transliterate_text as T  # noqa: E402

D = [("taliptiler", "طالبدیلر"), ("hassastılar", "حساسدیلر"), ("sadıksa", "صادقسه"), ("tarihçilerininse", "تاریخچیلرینینسه"),
     ("hazırlıklıydılar", "حاضر", "bas"), ("eyaletindeki", "ایالتنده‌كی"),
     # dokunulmaması gerekenler (Türkçe türev, fiil, ünlüyle biten kök)
     ("ağlattı", "آغلاتدی"), ("basarsa", "باصارسه"), ("veremem", "ویره‌مم"), ("geleyim", "كله‌یم"), ("katan", "قاتان"),
     ("karardı", "قراردی"), ("kürsüye", "كرسی یه"),
     # Tur KE2: mi/ki ünlü he'den sonra ZWNJ ile bitişir (Hayrat البسه‌می); ünsüz h bitişik (günah mı)
     ("şişe mi", "شیشه‌می"), ("ince ki", "اینجه‌كه"), ("kazayla mı", "قضایله‌می"), ("günah mı", "كناهمی"), ("bilmem ki", "بیلممكه")]


def main():
    kalan = 0
    for t in D:
        a, b = t[0], t[1]
        c = T(a).strip()
        if (c.startswith(b) if len(t) > 2 else c == b):
            continue
        kalan += 1
        print("KALDI", a, "->", c, "(beklenen", b + ")")
    yz_kayit.ekle([{"kelime": "yorumlazmaktan", "koken": "tr", "kok": "yorumlaz", "model": "gemini-4-hydrogen"}])
    for w, beklenen in (("yorumlazdığı", []), ("yorumlazmış", []),
                        # Tur KE3: kök başına sorulur, Türkçe fiil çekimi sorulmaz, özel ad (cümle ortasında büyük harf) önce
                        ("kemirdi kemirecekler", []), ("Dün Halimezq geldi, qorbazlar qorbazları gördü.", ["Halimezq", "qorbazlar"])):
        olan = yz_kayit.bilinmeyenler(w)
        if olan != beklenen:
            kalan += 1
            print("KALDI bilinmeyen", w, olan, "(beklenen", beklenen, ")")
    yz_kayit.ekle([{"kelime": "çorbazlarımız", "koken": "tr", "kok": "çorbaz", "model": "gemini-3.5-flash-lite"}])
    if yz_kayit.bilinmeyenler("çorbazdı") != ["çorbazdı"]:
        kalan += 1
        print("KALDI Lite kökü bilinen sayılmamalı")
    print("SONUC:", "HEPSI GECTI" if not kalan else f"{kalan} TEST KALDI")


main()
