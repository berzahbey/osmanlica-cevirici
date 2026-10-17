"""Hayrat sinavi 3 (Tur L): sinav 2 + olculen eserde yalniz o esere ait Hayrat kelimeleri hayrat_tek'ten gecici cikarilir
(ezber olcmemek icin; OSM_HAYRAT_TEK ile kapatilmaz). Hayrat sinavi 2: ceviriciyi Hayrat'in kendi Latin metniyle calistirir, Hayrat'in Osmanlicasiyla kelime kelime karsilastirir.
Kullanim: python hayrat_sinav2.py <hayrat klasoru> <rapor.tsv> [eser slug ... | hepsi]
Sayilmaz: noktalama, dua yazimi. Ayri sayilir: Hayrat'in kendi cift yazimi (ayni Latin kelime Hayrat'ta bu yazimla da geciyor)."""
import json, os, re, sys, time, difflib, collections, unicodedata
sys.path[:0] = [os.environ.get('SINAV_KOD', '/app')]   # yamali kodla: -e SINAV_KOD=/k/app
from bs4 import BeautifulSoup, NavigableString
from engine.transliterator import transliterate_text as tt
from engine import dictionary as D
from engine.alphabet import turkish_lower

KOK, OUT = sys.argv[1], sys.argv[2]
SECIM = sys.argv[3:] or ['hepsi']
NOKTALAMA = set('\u060c\u061b\u061f\u066d\u06d4\u066b\u066c')


def n(s):
    s = s.replace('\u06d5', '\u0647').replace('\u06af', '\u0643').replace('\u06c0', '\u0647').replace('\u200c', '')
    s = s.replace('\u0623', '\u0627').replace('\u0625', '\u0627').replace('\u064a', '\u06cc').replace('\u0649', '\u06cc')
    s = ''.join(c for c in s if not unicodedata.category(c).startswith('M') and c not in '\u0610\u0611\u0612\u0613\u0608')
    return re.sub('^\u0626\u0648', '\u0627\u0648', s)


TOK = re.compile('[\u0600-\u06ff\u200c]+')


def kelimeler(metin):
    out = []
    for w in TOK.findall(metin):
        w = ''.join(c for c in w if c not in NOKTALAMA).strip('\u200c')
        if w and n(w):
            out.append(w)
    return out


DUA = [n(x) for x in ('\u0639\u0644\u06cc\u0647 \u0627\u0644\u0635\u0644\u0627\u0629 \u0648\u0627\u0644\u0633\u0644\u0627\u0645',
                      '\u0639\u0644\u06cc\u0647 \u0627\u0644\u0633\u0644\u0627\u0645', '\u0639\u0644\u06cc\u0647\u0645 \u0627\u0644\u0633\u0644\u0627\u0645',
                      '\u0631\u0636\u06cc \u0627\u0644\u0644\u0647 \u0639\u0646\u0647', '\u0631\u0636\u06cc \u0627\u0644\u0644\u0647 \u0639\u0646\u0647\u0627',
                      '\u0631\u0636\u06cc \u0627\u0644\u0644\u0647 \u0639\u0646\u0647\u0645', '\u0631\u0647', '\u0642 \u0633', '\u0642\u062f\u0633 \u0633\u0631\u0647',
                      '\u0631\u062d\u0645\u0629 \u0627\u0644\u0644\u0647 \u0639\u0644\u06cc\u0647', '\u0631\u062d\u0645\u062a \u0627\u0644\u0644\u0647 \u0639\u0644\u06cc\u0647',
                      '\u0635\u0644\u06cc \u0627\u0644\u0644\u0647 \u0639\u0644\u06cc\u0647 \u0648\u0633\u0644\u0645')]
DUA_KELIME = set(w for d in DUA for w in d.split())


def dua_mi(h, c):
    """fark yalniz dua yaziminda mi (cevirici acik yaziyor, Hayrat isaret ya da kisaltma kullaniyor)"""
    hw = [n(x) for x in h]
    cw = [n(x) for x in c]
    return bool(cw or hw) and all(w in DUA_KELIME for w in cw + hw)


def veri(d):
    return (d.get('data') or []) if isinstance(d, dict) else (d or [])


def duz(t):
    return re.sub(r'\s+', ' ', t or '').strip()


# Hayrat'ta ayni Latin kelimenin butun yazimlari (cift yazim denetimi)
CIFT = collections.defaultdict(set)
for line in open(os.path.join(KOK, 'kelime_ciftleri.tsv'), encoding='utf-8'):
    p = line.rstrip('\n').split('\t')
    if len(p) >= 2:
        CIFT[p[0].lower()].add(n(p[1]).replace(' ', ''))

eserler = sorted(os.listdir(os.path.join(KOK, 'ham')))
# her Latin kelimenin hangi eserlerde gectigi (hayrat_tek kayitlari icin)
TEK_ESER = collections.defaultdict(set)
for _slug in eserler:
    _kl = os.path.join(KOK, 'ham', _slug)
    for _f in os.listdir(_kl):
        if _f.startswith('osmanlica_') and _f.endswith('.json'):
            for _p in veri(json.load(open(os.path.join(_kl, _f), encoding='utf-8'))):
                for _l in re.findall(r'data-latince="([^"]+)"', _p.get('osmanlica_html') or ''):
                    _k = turkish_lower(duz(_l)).replace('\u2019', "'").replace('\u2018', "'")
                    if _k in D.HAYRAT_TEK:
                        TEK_ESER[_k].add(_slug)
if SECIM != ['hepsi']:
    eserler = [e for e in eserler if e in SECIM]
GENEL = collections.Counter()
HATA = collections.Counter()
ORNEK = {}
TUR = {}
t0 = time.time()
for slug in eserler:
    klasor = os.path.join(KOK, 'ham', slug)
    dosyalar = sorted(os.listdir(klasor))
    lat = {}
    for f in dosyalar:
        if f.startswith('latince_') and f.endswith('.json'):
            for p in veri(json.load(open(os.path.join(klasor, f), encoding='utf-8'))):
                lat[p['id']] = p
    say = collections.Counter()
    gorulen = set()
    cikarilan = {k: D.HAYRAT_TEK.pop(k) for k, e in list(TEK_ESER.items()) if e == {slug} and k in D.HAYRAT_TEK}
    for k in cikarilan:
        D.HAYRAT_ANAHTAR.discard(k)
    for f in dosyalar:
        if not (f.startswith('osmanlica_') and f.endswith('.json')):
            continue
        for p in veri(json.load(open(os.path.join(klasor, f), encoding='utf-8'))):
            if p['id'] in gorulen:
                continue
            gorulen.add(p['id'])
            latin = duz(BeautifulSoup((lat.get(p['id']) or {}).get('latince_html') or '', 'html.parser').get_text(' '))
            if not latin:
                continue
            soup = BeautifulSoup(p.get('osmanlica_html') or '', 'html.parser')
            hk, etiket = [], []  # Hayrat kelimeleri ve her birinin Latin karsiligi
            for d in soup.descendants:
                if isinstance(d, NavigableString):
                    sp = d.find_parent('span', attrs={'data-latince': True})
                    lk = duz(sp['data-latince']) if sp else ''
                    for w in kelimeler(str(d)):
                        hk.append(w)
                        etiket.append(lk)
            ck = kelimeler(tt(latin))
            sm = difflib.SequenceMatcher(None, [n(w) for w in hk], [n(w) for w in ck], autojunk=False)
            for op, i1, i2, j1, j2 in sm.get_opcodes():
                say['kelime'] += i2 - i1
                if op == 'equal':
                    say['ayni'] += i2 - i1
                    continue
                h, c = hk[i1:i2], ck[j1:j2]
                lk = ' '.join(dict.fromkeys(x for x in etiket[i1:i2] if x))
                if dua_mi(h, c):
                    tur = 'dua'
                elif lk and n(' '.join(c)).replace(' ', '') in CIFT.get(lk.lower(), ()):
                    tur = 'hayrat_cesidi'
                elif not h:
                    tur = 'fazla'
                else:
                    tur = 'hata'
                say[tur] += max(1, i2 - i1) if tur != 'fazla' else 1
                anahtar = (lk, ' '.join(h), ' '.join(c))
                HATA[anahtar] += 1
                TUR[anahtar] = tur
                if anahtar not in ORNEK:
                    k = latin.find(lk.split(' ')[0]) if lk else -1
                    ORNEK[anahtar] = (slug, str(p.get('sayfa')), latin[max(0, k - 60):k + 80] if k >= 0 else latin[:140])
    D.HAYRAT_TEK.update(cikarilan)
    D.HAYRAT_ANAHTAR.update(cikarilan)
    hesap = say['kelime'] - say['dua']
    dogru = say['ayni'] + say['hayrat_cesidi']
    print(f"{slug:28} kelime {say['kelime']:7d} | aynı %{100 * say['ayni'] / max(1, say['kelime']):.2f} | dua {say['dua']} | Hayrat çeşidi {say['hayrat_cesidi']}"
          f" | HATA {say['hata']} (+fazla {say['fazla']}) | DOĞRULUK %{100 * dogru / max(1, hesap):.2f} (dışarıda: {len(cikarilan)})", flush=True)
    GENEL.update(say)
hesap = GENEL['kelime'] - GENEL['dua']
print(f"TOPLAM {len(eserler)} eser, kelime {GENEL['kelime']} | HATA {GENEL['hata']} | Hayrat çeşidi {GENEL['hayrat_cesidi']} | dua {GENEL['dua']}"
      f" | DOĞRULUK %{100 * (GENEL['ayni'] + GENEL['hayrat_cesidi']) / max(1, hesap):.2f} ({time.time() - t0:.0f} sn)")
print('En sık 60 hata (Latin | Hayrat | çevirici):')
for (lk, h, c), k in [x for x in HATA.most_common() if TUR[x[0]] == 'hata'][:60]:
    print(f'  {k}× {lk} | {h} | {c}   [{ORNEK[(lk, h, c)][0]} s.{ORNEK[(lk, h, c)][1]}]')
with open(OUT, 'w', encoding='utf-8') as f:
    f.write('sayi\ttur\tlatince\thayrat\tcevirici\teser\tsayfa\tbaglam\n')
    for a, k in HATA.most_common():
        e, s, b = ORNEK[a]
        f.write('\t'.join([str(k), TUR[a], a[0], a[1], a[2], e, s, b.replace('\t', ' ')]) + '\n')
print('Bütün liste:', OUT)
