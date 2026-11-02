"""Osmanlıca çevirici Tur X yaması (2 Kasım 2026, Tur W'nin üstüne): kaynak kısaltmaları (Zahir onayı).
bkz./bk. باقكز, vb./vs. الخ, vd. و مابعدی, s. 12 ص ١٢, c. 2 ج ٢ (önce harf harf: بقز. س. ود. وب.).
Değişen: app/engine/transliterator.py (_KISALTMA), testlerde eski بقز beklentileri (imla, izafet, tur_e, tur_j); yeni tests/test_tur_x.py.
Tekrar çalıştırılabilir. Kullanım (kod klasöründe): python3 osm_tur_x_yama.py"""
import hashlib, os, sys
MD5 = {'app/engine/transliterator.py': ('c1d34cd00b445123fd0b25f1fe95d5b8', 'b3d3bddf599464445f51ec646ae21763'), 'tests/test_imla.py': ('87858d206635658773ccb0f8c385fd4e', '820763fc3545dea516cf1c6c9f5ccd91'), 'tests/test_izafet.py': ('09edaabb34ae458ace251b9bf3adc60f', '785efeb5385010c6f6faaedec40a4689'), 'tests/test_tur_e.py': ('7c3c633e30255f2819b396557f69d1e2', '7ad13d7d8bcbccf70628d21facd021c4'), 'tests/test_tur_j.py': ('9511249a936ab99325a3a691d859f8fe', '08b32ce9124a3df7bafe83f762a84fcc')}
DEG = {'app/engine/transliterator.py': [('    (re.compile(r"(?<![\\w.])r\\.\\s?a\\.?(?![\\w])", re.I), "رضی الله عنه"),\n]\n', '    (re.compile(r"(?<![\\w.])r\\.\\s?a\\.?(?![\\w])", re.I), "رضی الله عنه"),\n    # Tur X (2 Kasım 2026, Zahir onayı): kaynak kısaltmaları Osmanlı/Arap kaynak yazımıyla (harf harf بقز، ود، وب değil)\n    (re.compile(r"(?<![\\w.])(?:bkz\\.?|bk\\.)(?!\\w)", re.I), "باقكز"),                       # bakınız\n    (re.compile(r"(?<![\\w.])(?:vb\\.?|vs\\.)(?!\\w)", re.I), "الخ"),                           # ve benzeri, vesaire\n    (re.compile(r"(?<![\\w.])vd\\.?(?!\\w)", re.I), "و مابعدی"),                               # ve devamı\n    (re.compile(r"(?<![\\w.])ss?\\.\\s*(?=\\d)"), "ص "),                                      # s. 12 / ss. 12-15 sayfa\n    (re.compile(r"(?<![\\w.])[cC]\\.\\s*(?=(?:\\d|[IVXLC]+\\b))"), "ج "),                     # c. 2 / C. II cilt\n]\n')], 'tests/test_imla.py': [('    "Bkz. Essai de Chronologie des oeuvres de al-Ghazali, Paris 1959.":\n        "بقز. Essai de Chronologie des oeuvres de al-Ghazali, Paris 1959.",\n    "Sokrates “Know thyself, said Socrates.” demiştir.": "سقراط \\"Know thyself, said Socrates.\\" دیمشدر.",\n', '    "Bkz. Essai de Chronologie des oeuvres de al-Ghazali, Paris 1959.":\n        "باقكز Essai de Chronologie des oeuvres de al-Ghazali, Paris 1959.",\n    "Sokrates “Know thyself, said Socrates.” demiştir.": "سقراط \\"Know thyself, said Socrates.\\" دیمشدر.",\n')], 'tests/test_izafet.py': [('    ("Kur’an’ın", "قرآنڭ"), ("fıkh-ı ekber", "فقه اكبر"),\n    ("Bkz. Essai de Chronologie des oeuvres de al-Ghazali, Paris 1959.", "بقز. Essai de Chronologie des oeuvres de al-Ghazali, Paris 1959."),\n]\n', '    ("Kur’an’ın", "قرآنڭ"), ("fıkh-ı ekber", "فقه اكبر"),\n    ("Bkz. Essai de Chronologie des oeuvres de al-Ghazali, Paris 1959.", "باقكز Essai de Chronologie des oeuvres de al-Ghazali, Paris 1959."),\n]\n')], 'tests/test_tur_e.py': [('    ("bunun", "بونڭ"), ("onun", "اونڭ"), ("dinin", "دینڭ"), ("babanın", "بابانڭ"), ("dünyanın", "دنیانڭ"), ("devenin", "دوه\u200cنڭ"),\n    ("bakiye", "بقیه"), ("karı", "قاری"), ("su", "صو"), ("pazar", "پازار"), ("Bkz. s. 45", "بقز. س. ٤٥"), ("sonun", "صوڭڭ"),\n]\n', '    ("bunun", "بونڭ"), ("onun", "اونڭ"), ("dinin", "دینڭ"), ("babanın", "بابانڭ"), ("dünyanın", "دنیانڭ"), ("devenin", "دوه\u200cنڭ"),\n    ("bakiye", "بقیه"), ("karı", "قاری"), ("su", "صو"), ("pazar", "پازار"), ("Bkz. s. 45", "باقكز ص ٤٥"), ("sonun", "صوڭڭ"),\n]\n')], 'tests/test_tur_j.py': [("    ('58. secde ederek (boyun e\\u011ferek) girin', '\\u0665\\u0668. \\u0633\\u062c\\u062f\\u0647 \\u0627\\u06cc\\u062f\\u0631\\u0643 (\\u0628\\u0648\\u06cc\\u0648\\u0646 \\u0627\\u0643\\u0647\\u200c\\u0631\\u0643) \\u0643\\u06cc\\u0631\\u06ad'),\n    ('Bu kitapta (bkz. s. 12) ve (Allah) ge\\xe7er.', '\\u0628\\u0648 \\u0643\\u062a\\u0627\\u0628\\u062f\\u0647 (\\u0628\\u0642\\u0632. \\u0633. \\u0661\\u0662) \\u0648 (\\u0627\\u0644\\u0644\\u0647) \\u0643\\u0686\\u0631.'),\n]\n", "    ('58. secde ederek (boyun e\\u011ferek) girin', '\\u0665\\u0668. \\u0633\\u062c\\u062f\\u0647 \\u0627\\u06cc\\u062f\\u0631\\u0643 (\\u0628\\u0648\\u06cc\\u0648\\u0646 \\u0627\\u0643\\u0647\\u200c\\u0631\\u0643) \\u0643\\u06cc\\u0631\\u06ad'),\n    ('Bu kitapta (bkz. s. 12) ve (Allah) ge\\xe7er.', '\\u0628\\u0648 \\u0643\\u062a\\u0627\\u0628\\u062f\\u0647 (\\u0628\\u0627\\u0642\\u0643\\u0632 \\u0635 \\u0661\\u0662) \\u0648 (\\u0627\\u0644\\u0644\\u0647) \\u0643\\u0686\\u0631.'),\n]\n")]}
YENI = {'tests/test_tur_x.py': '"""Tur X (2 Kasım 2026): kaynak kısaltmaları (bkz. باقكز، vb./vs. الخ، vd. و مابعدی، s. ص، c. ج).\nCalistirma: docker run --rm -v "$PWD":/k -w /k berzahbey/osmanlica-cevirici:latest python tests/test_tur_x.py"""\nimport logging\nimport os\nimport sys\n\nlogging.disable(50)\nsys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app"))\nfrom engine.transliterator import transliterate_text as T  # noqa: E402\n\nDURUMLAR = [("(bkz. s. 12, vd.)", "(باقكز ص ١٢، و مابعدی)"), ("Bkz. c. 2, s. 45.", "باقكز ج ٢، ص ٤٥."),\n            ("kitaplar vb. şeyler", "كتابلر الخ شیلر"), ("ev, bağ vs. var", "او، باغ الخ وار"), ("C. II, ss. 10-15", "ج ٢، ص ١٠-١٥"),\n            ("bk. Taberî", "باقكز طبری")]\nDOKUNMA = ["Hz. Muhammed (s.a.v.) dedi.", "Ahmed b. Hanbel", "vb ile", "c harfi", "s harfi"]\n\n\ndef main():\n    kalan = 0\n    for latin, beklenen in DURUMLAR:\n        c = T(latin).strip()\n        if c != beklenen:\n            kalan += 1\n            print("KALDI", latin, "->", c, "(beklenen", beklenen + ")")\n    for w in DOKUNMA:\n        print("bilgi:", w, "->", T(w).strip())\n    print("SONUC:", "HEPSI GECTI" if not kalan else f"{kalan} TEST KALDI")\n\n\nmain()\n'}


def md5s(s):
    return hashlib.md5(s.encode("utf-8")).hexdigest()


if not os.path.isfile("app/engine/openiti.py"):
    sys.exit("HATA: önce Tur W (osm_tur_w_yama.py) kurulmalı; osmanlica kod klasöründe çalıştırın")
yaz = {}
for p, (e, y) in MD5.items():
    s = open(p, encoding="utf-8", newline="").read()
    if md5s(s) == y:
        print("zaten yamalı:", p)
        continue
    if md5s(s) != e:
        sys.exit(f"HATA: {p} beklenen sürüm değil (md5 {md5s(s)}); hiçbir dosya değişmedi")
    for a, b in DEG[p]:
        if s.count(a) != 1:
            sys.exit(f"HATA: {p} içinde değişecek yer bulunamadı; hiçbir dosya değişmedi")
        s = s.replace(a, b)
    if md5s(s) != y:
        sys.exit(f"HATA: {p} yamadan sonra md5 tutmadı; hiçbir dosya değişmedi")
    yaz[p] = s
for p, s in yaz.items():
    open(p, "w", encoding="utf-8", newline="").write(s)
    print("yamalandı:", p)
for p, icerik in YENI.items():
    open(p, "w", encoding="utf-8", newline="").write(icerik)
    print("yazıldı:", p)
print("TAMAM: Tur X")
