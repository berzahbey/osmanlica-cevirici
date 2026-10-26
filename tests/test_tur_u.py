"""Tur U (27 Ekim): unluden sonra ek-fiil -ymIs, kalin olumsuz istek -mAyAsIn, sapkali kelime + kesmeli -ki eki (ayin degil), Irak + ek,
harf-i tarif (sapkali unlu, tiresiz bosluklu bicim, Vadi, ulu), kitap sozlugu Tur U bolumu.
Calistirma: docker run --rm -v "$PWD":/k -w /k berzahbey/osmanlica-cevirici:latest python tests/test_tur_u.py"""
import logging
import os
import sys

logging.disable(50)
KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app")
sys.path.insert(0, KOK)
from engine.transliterator import full_pipeline, transliterate_text as T  # noqa: E402

KELIMELER = [('k\u0131rmayas\u0131n', '\u0642\u06cc\u0631\u0645\u0627\u06cc\u0627\u0633\u06ad'), ('olmayas\u0131n', '\u0627\u0648\u0644\u0645\u0627\u06cc\u0627\u0633\u06ad'), ('kalmayas\u0131n', '\u0642\u0627\u0644\u0645\u0627\u06cc\u0627\u0633\u06ad'), ('g\xf6rmeyesin', '\u0643\u0648\u0631\u0645\u0647\u200c\u06cc\u0647\u200c\u0633\u06ad'), ('i\xe7indeymi\u015f', '\u0627\u06cc\u0686\u0646\u062f\u0647\u200c\u06cc\u0645\u0634'), ('kar\u015f\u0131s\u0131ndaym\u0131\u015f', '\u0642\u0627\u0631\u0634\u0648\u0633\u0646\u062f\u0647\u200c\u06cc\u0645\u0634'), ('kelimeymi\u015f', '\u0643\u0644\u0645\u0647\u200c\u06cc\u0645\u0634'), ('ki\u015fiymi\u015f', '\u0643\u06cc\u0634\u06cc\u0645\u0634'), ('vermeliymi\u015f', '\u0648\u06cc\u0631\u0645\u0644\u06cc\u0645\u0634'), ('adam\u0131ym\u0131\u015f', '\u0622\u062f\u0645\u06cc\u0645\u0634'), ('romanlar\u0131ym\u0131\u015f', '\u0631\u0648\u0645\u0627\u0646\u0644\u0631\u06cc\u0645\u0634'), ('hastaym\u0131\u015f', '\u062e\u0633\u062a\u0647\u200c\u06cc\u0645\u0634'), ('kaym\u0131\u015f', '\u0642\u0627\u06cc\u0645\u0634'), ('koymu\u015f', '\u0642\u0648\u06cc\u0645\u0634'), ('duymu\u015f', '\u062f\u0648\u06cc\u0645\u0634'), ('giymi\u015f', '\u0643\u06cc\u06cc\u0645\u0634'), ('al\u0131koymu\u015f', '\u0622\u0644\u06cc\u0642\u0648\u06cc\u0645\u0634'), ("Ker\xeem'deki", '\u0643\u0631\u06cc\u0645\u062f\u0647\u200c\u0643\u06cc'), ("Amm\xfbriye'deki", '\u0627\u0645\u0648\u0631\u06cc\u0647\u200c\u062f\u0647\u200c\u0643\u06cc'), ("M\xe2ver\xe2\xfcnnehir'deki", '\u0645\u0627\u0648\u0631\u0627\u0646\u062d\u0631\u062f\u0647\u200c\u0643\u06cc'), ("Kur'\xe2n'daki", '\u0642\u0631\u0622\u0646\u062f\u0647\u200c\u0643\u06cc'), ("Medine'deki", '\u0645\u062f\u06cc\u0646\u0647\u200c\u062f\u0647\u200c\u0643\u06cc'), ("ma'n\xe2", '\u0645\u0639\u0646\u0627'), ("te'm\xeen", '\u062a\u0623\u0645\u06cc\u0646'), ("L\xe2hikas\u0131'ndaki", '\u0644\u0627\u062d\u0642\u0647\u200c\u0633\u0646\u062f\u0647\u200c\u0643\u06cc'), ("Irak'taki", '\u0639\u0631\u0627\u0642\u062f\u0647\u200c\u0643\u06cc'), ("Irak'ta", '\u0639\u0631\u0627\u0642\u062f\u0647'), ("Irak'takiler", '\u0639\u0631\u0627\u0642\u062f\u0647\u200c\u0643\u06cc\u0644\u0631'), ('Irak', '\u0639\u0631\u0627\u0642'), ('def\u02bbadaki', '\u062f\u0641\u0639\u0647\u200c\u062f\u0647\u200c\u0643\u06cc'), ('\u0130sl\xe2mk\xf6y\u2019\xfcndeki', '\u0627\u0633\u0644\u0627\u0645 \u0643\u0648\u06cc\u0646\u062f\u0647\u200c\u0643\u06cc'), ('mes\u2019elelerdeki', '\u0645\u0633\u0626\u0644\u0647\u200c\u0644\u0631\u062f\u0647\u200c\u0643\u06cc')]
CUMLELER = [('Eb\xfb\u2019l-Hasan geldi.', '\u0627\u0628\u0648 \u0627\u0644\u062d\u0633\u0646 \u0643\u0644\u062f\u06cc.'), ("Ebu'l-Hasan geldi.", '\u0627\u0628\u0648 \u0627\u0644\u062d\u0633\u0646 \u0643\u0644\u062f\u06cc.'), ("V\xe2di'l-Kur\xe2'da", '\u0648\u0627\u062f\u06cc \u0627\u0644\u0642\u0631\u0627\u062f\u0647'), ('R\xfbh\xfc\u2019l-Bey\xe2n', '\u0631\u0648\u062d \u0627\u0644\u0628\u06cc\u0627\u0646'), ('Z\xfcl\u2019celal-ve\u2019l-ikram', '\u0630\u0648\u0627\u0644\u062c\u0644\u0627\u0644 \u0648\u0627\u0644\u0627\u0643\u0631\u0627\u0645'), ('Mans\xfbra\u2019l-Hall\xe2c', '\u0645\u0646\u0635\u0648\u0631 \u0627\u0644\u062d\u0644\u0651\u0627\u062c'), ('Beyt\xfc\u2019l Makdis', '\u0628\u06cc\u062a \u0627\u0644\u0645\u0642\u062f\u0633'), ('\xdcmm\xfc\u2019l Kitab', '\u0627\u0645\u0651 \u0627\u0644\u0643\u062a\u0627\u0628'), ("Ebu'l Abbas", '\u0627\u0628\u0648 \u0627\u0644\u0639\u0628\u0651\u0627\u0633'), ('bi\u2019l hakki', '\u0628\u0627\u0644\u062d\u0642\u0651\u06cc'), ('fi\u2019l \xfc evsaf\u0131n', '\u0641\u0639\u0644 \u0648 \u0627\u0648\u0635\u0627\u0641\u06ad'), ('l\xe2\u2019l renkli', '\u0644\u0639\u0644 \u0631\u0646\u0643\u0644\u06cc'), ('ayne\u2019l yakin', '\u0639\u06cc\u0646 \u0627\u0644\u06cc\u0642\u06cc\u0646'), ('hakka\u2019l yak\xeen', '\u062d\u0642\u0651 \u0627\u0644\u06cc\u0642\u06cc\u0646'), ("ul\xfb'l-emre", '\u0627\u0648\u0644\u0648 \u0627\u0644\u0627\u0645\u0631\u0647'), ("Mekke'l-M\xfckerreme", '\u0645\u0643\u0651\u0647 \u0627\u0644\u0645\u0643\u0631\u0651\u0645\u0647'), ("D\xe2r\xfc'l-Harb", '\u062f\u0627\u0631 \u0627\u0644\u062d\u0631\u0628'), ('Eb\xfb\u2019s-Sa\xeed', '\u0627\u0628\u0648 \u0627\u0644\u0633\u0639\u06cc\u062f'), ("Kit\xe2b\xfc't-Tevh\xeed", '\u0643\u062a\u0627\u0628 \u0627\u0644\u062a\u0648\u062d\u06cc\u062f'), ('el-Bakara', '\u0627\u0644\u0628\u0642\u0631\u0647'), ('ale\u2019l-hus\xfbs', '\u0639\u0644\u06cc \u0627\u0644\u062e\u0635\u0648\u0635'), ('maa\u2019t-teess\xfcf', '\u0645\u0639 \u0627\u0644\u062a\u0623\u0633\u0651\u0641'), ('ile\u2019l-merkeziye', '\u0627\u0644\u06cc \u0627\u0644\u0645\u0631\u0643\u0632\u06cc\u0647'), ('tahte\u2019l-bahr', '\u062a\u062d\u062a \u0627\u0644\u0628\u062d\u0631'), ('s\xfcmme\u2019t-ted\xe2rik', '\u062b\u0645\u0651 \u0627\u0644\u062a\u062f\u0627\u0631\u0643'), ('Eyy\xfche\u2019n-nefs', '\u0627\u06cc\u0651\u0647\u0627 \u0627\u0644\u0646\u0641\u0633'), ('Rabbe\u2019l-\xe2lem\xeen', '\u0631\u0628\u0651 \u0627\u0644\u0639\u0627\u0644\u0645\u06cc\u0646'), ('\xc2yete\u2019l-K\xfcrs\xee', '\u0622\u06cc\u062a \u0627\u0644\u0643\u0631\u0633\u06cc'), ('Ris\xe2lete\u2019n-N\xfbr\u2019dan', '\u0631\u0633\u0627\u0644\u062a \u0627\u0644\u0646\u0648\u0631\u062f\u0646'), ('beyne\u2019l-milel', '\u0628\u06cc\u0646 \u0627\u0644\u0645\u0644\u0644'), ('kable\u2019l-b\xfcl\xfb\u011f', '\u0642\u0628\u0644 \u0627\u0644\u0628\u0644\u0648\u063a'), ("Ene'l-Hakk dedi.", '\u0627\u0646\u0627 \u0627\u0644\u062d\u0642\u0651 \u062f\u06cc\u062f\u06cc.'), ("H\xfcve'l-Hakk", '\u0647\u0648 \u0627\u0644\u062d\u0642\u0651'), ('El \u0130th\xe2f\xe2t\xfc\u2019s-Seniyye f\xee\u2019l-Ah\xe2disi\u2019l-Kudsiyye, Haydar\xe2b\xe2d', '\u0627\u0644\u0627\u062a\u062d\u0627\u0641\u0627\u062a \u0627\u0644\u0633\u0646\u06cc\u0651\u0647 \u0641\u06cc \u0627\u0644\u0627\u062d\u0627\u062f\u0633 \u0627\u0644\u0642\u062f\u0633\u06cc\u0647\u060c \u062d\u06cc\u062f\u0631\u0627\u0628\u0627\u062f'), ('Al-\u0130ns\xe2na\u2019l-K\xe2mil\u2019ine', '\u0627\u0644\u0627\u0646\u0633\u0627\u0646 \u0627\u0644\u0643\u0627\u0645\u0644\u0646\u0647'), ('el-Hizb\xfc\u2019l-Ekberi\u2019l-Kur\u2019\xe2n\xee\u2019nin', '\u0627\u0644\u062d\u0632\u0628 \u0627\u0644\u0627\u0643\u0628\u0631 \u0627\u0644\u0642\u0631\u0622\u0646\u06cc\u0646\u06ad'), ("keyfe tuhy\xee'l-mevt\xe2", '\u0643\u06cc\u0641\u0647 \u062a\u062d\u06cc\u06cc \u0627\u0644\u0645\u0648\u062a\u0627'), ('l\xe2\u2019l-g\xfbn', '\u0644\u0639\u0644 \u0643\u0648\u0646')]


def main():
    kalan = 0
    for latin, beklenen in KELIMELER:
        cikan = T(latin).strip()
        if cikan != beklenen:
            kalan += 1
            print("KALDI", ascii(latin), "->", ascii(cikan), "(beklenen", ascii(beklenen) + ")")
    for latin, beklenen in CUMLELER:
        cikan = full_pipeline(latin, assume_turkish=True)["ottoman_text"].strip()
        if cikan != beklenen:
            kalan += 1
            print("KALDI (cumle)", ascii(latin), "->", ascii(cikan), "(beklenen", ascii(beklenen) + ")")
    yol = os.path.join(KOK, "data", "kitap_sozlugu.tsv")
    bolum = False
    for satir in open(yol, encoding="utf-8"):
        if satir.startswith("# Tur U"):
            bolum = True
            continue
        if not bolum or satir.startswith("#") or not satir.strip():
            continue
        latin, yazim = satir.rstrip("\n").split("\t")[:2]
        cikan = T(latin).strip()
        if cikan.replace("\u0651", "") != yazim.replace("\u0651", ""):
            kalan += 1
            print("KALDI (sozluk)", ascii(latin), "->", ascii(cikan), "(beklenen", ascii(yazim) + ")")
    print("SONUC: HEPSI GECTI" if not kalan else "SONUC: %d TEST KALDI" % kalan)


if __name__ == "__main__":
    main()
