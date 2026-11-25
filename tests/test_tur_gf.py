"""Tur GF (25 Kasım 2026, Zahir kararı): kef/gef Hayrat gibi. İnce ğ ve Farsça g گ (eğer اگر، değil دگل، ettiği ایتدیگی، dergâh درگاه);
kelime başı ve Türkçe kelime içi g ك (gibi كبی، sevgili سوكیلی، hangi هانكی); kalın ğ غ; eski yazım yirmi یگرمی، bey بگ."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.environ.setdefault("YZ_SOZLUK", "/yok")
from app.engine.transliterator import transliterate_text as T
from app.engine import gef
B = []
def ok(a, b):
    c = T(a); B.append(c == b); print(("GECTI " if c == b else "KALDI ") + f"{a} -> {c}" + ("" if c == b else f"  (beklenen {b})"))
for lat, osm in [("eğer", "اگر"), ("değil", "دگل"), ("ettiği", "ایتدیگی"), ("gibi", "كبی"), ("güzel", "كوزل"), ("sevgili", "سوكیلی"),
                 ("zengin", "زنكین"), ("hangi", "هانكی"), ("bugün", "بوكون"), ("yirmi", "یگرمی"), ("dergâh", "درگاه"), ("yegâne", "یگانه"),
                 ("hengâmda", "هنگامده"), ("mesleği", "مسلگی"), ("vermeye", "ویرمگه"), ("olduğunu", "اولدیغنی"), ("dağ", "طاغ"),
                 ("istiğfâr", "استغفار"), ("çiçeğin", "چیچگڭ"), ("birliğine", "برلگنه"), ("öğrenmeye", "اوگرنمگه"), ("eğri", "اگری"),
                 ("iğne", "ایگنه"), ("üzengi", "اوزنكی"), ("rüzgâr", "روزگار"), ("tebliğ", "تبلیغ")]:
    ok(lat, osm)
ok("Eğer değil ise, ettiği şey gibi güzel.", "اگر دگل ایسه، ایتدیگی شی كبی كوزل.")
ok("Ağabeyimiz Atabey'e gitti.", "آغابگمز آتابگه كیتدی.")
ok("hangi bugün gördüğüm çiçeğin yüreğinde", "هانكی بوكون كوردیگم چیچگڭ یورگنده")
# kural tek başına (Hayrat tablosu olmadan)
for lat, girdi, beklenen in [("gördüğünde", "كوردیكنده", "كوردیگنده"), ("gelmeye", "كلمكه", "كلمگه"), ("teşekkür", "تشكّر", "تشكّر"),
                            ("seyrângâh", "سیرانكاه", "سیرانگاه"), ("gönderdiğim", "كوندردیكم", "كوندردیگم")]:
    c = gef.kural(lat, girdi); B.append(c == beklenen)
    print(("GECTI " if c == beklenen else "KALDI ") + f"kural {lat} {girdi} -> {c}" + ("" if c == beklenen else f"  (beklenen {beklenen})"))
print("SONUC:", "HEPSI GECTI" if all(B) else f"{B.count(False)} KALDI")
sys.exit(0 if all(B) else 1)
