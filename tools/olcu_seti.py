# -*- coding: utf-8 -*-
"""Sabit olcu seti (Tur T2, 27 Ekim 2026): denetim 5'in okunmus kelimeleri ve kararlari (tools/olcu_seti.tsv).
Her turda ayni kelimeler simdiki kodla yeniden cevrilir:
  - H (hata) satiri dogru yazima ulastiysa DUZELDI, hala yanlissa KALDI;
  - D (dogru) satirinin ciktisi degistiyse BOZULDU? (okunmali: yeni yazim da dogru olabilir);
  - K, Y, T satirlari orana girmez (K: Turkce kaynak hatasi, Zahir karari; Y: yabanci/kisaltma; T: tartismali), degisirse yalniz listelenir.
ONEMLI: bu set bir GERILEME bekcisidir, dogruluk olcusu degil. Setteki hatalar duzeltildikce setin kendi orani sifira iner
(duzeltmeler bu kelimelere ozgu olabilir); genel dogruluk icin her denetimde YENI bir orneklem okunur (ayni olcutle).
Kullanim (kod klasorunde):
  docker run --rm -v "$PWD":/k -w /k -e FARK_KOD=/k/app berzahbey/osmanlica-cevirici:latest python tools/olcu_seti.py tools/olcu_seti.tsv
  (FARK_KOD=/app: imajdaki kod)"""
import os
import sys

sys.path.insert(0, os.environ.get("FARK_KOD", "/k/app"))
import logging  # noqa: E402

logging.disable(logging.CRITICAL)
from engine.transliterator import transliterate_text  # noqa: E402

TOPLAM_KELIME = 4854575      # denetim 5: 36 EPUB
KUYRUK_KUTLESI = 968052      # Hayrat disi, 200'den az gecen kelimelerin gecisi


def yalin(s):
    return s.replace("‌", "").replace("ّ", "").strip()


def main(yol):
    satirlar = []
    for satir in open(yol, encoding="utf-8"):
        if satir.startswith(("#", "katman\t")) or not satir.strip():
            continue
        katman, kelime, gecis, osm, karar, dogru, ornek = satir.rstrip("\n").split("\t")[:7]
        satirlar.append((katman, kelime, int(gecis), osm, karar, dogru))
    print("KOD:", os.environ.get("FARK_KOD", "/k/app"))
    ust_hata = ust_okunmali = 0
    k_n = k_hata = k_okunmali = 0
    for katman, kelime, gecis, osm, karar, dogru in satirlar:
        yeni = transliterate_text(kelime).strip()
        degisti = yalin(yeni) != yalin(osm)
        if karar == "H":
            durum = "DUZELDI" if yalin(yeni) == yalin(dogru) else "KALDI"
        elif karar == "D":
            durum = "BOZULDU?" if degisti else ""
        else:
            durum = (karar + " degisti") if degisti else ""
        if katman == "ust":
            if karar == "H" and durum == "KALDI":
                ust_hata += gecis
            if durum == "BOZULDU?":
                ust_okunmali += gecis
        else:
            if karar in ("D", "H"):
                k_n += 1
                k_hata += karar == "H" and durum == "KALDI"
                k_okunmali += durum == "BOZULDU?"
        if durum:
            print(f"{durum:12} {katman:6} {kelime} ({gecis}): {osm} -> {yeni}" + (f"  [dogru {dogru}]" if karar == "H" else ""))
    oran = k_hata / k_n if k_n else 0
    hata = ust_hata + oran * KUYRUK_KUTLESI
    print()
    print(f"Ust katman: kalan hata {ust_hata} gecis, okunmasi gereken degisiklik {ust_okunmali} gecis")
    print(f"Kuyruk: {k_hata}/{k_n} hata (%{100 * oran:.1f}), okunmasi gereken {k_okunmali}")
    print(f"Setin kendi hata orani %{100 * hata / TOPLAM_KELIME:.2f} (yalniz karsilastirma icin; genel dogruluk degil)")
    print("BOZULDU? satirlari okunmadan tur canliya alinmaz.")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "tools/olcu_seti.tsv")
