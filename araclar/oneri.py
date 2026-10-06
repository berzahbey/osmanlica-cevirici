"""Sözlükte olmayan Arapça kökenli kelime için OpenITI sıklık listesinden yazım önerisi (ünsüz iskeleti + ünlü harfleri hizalanır).
Liste: araclar/arapca_siklik.tsv.gz (OpenITI'den 14 müellifin 172 eseri: Gazâlî, İbn Arabî, Fahreddin Râzî, İbn Sînâ, İbn Rüşd,
Abdülkadir Geylânî, Kuşeyrî, Sülemî, Muhâsibî, Cüneyd, Ebû Tâlib Mekkî, Buhârî, Müslim, İbn Kayyim; 21 milyon kelime; sıklık >= 5).
Öneriler gözden geçirilmeden sözlüğe eklenmez (yarısı kadarı Türkçe kelimelerin yanlış eşleşmesi olabilir).
Kullanım: python araclar/oneri.py mükâşefe istidat tevil"""
import re, collections, sys
import gzip, os
_YOL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "arapca_siklik.tsv.gz")
SIK = {}
with gzip.open(_YOL, "rt", encoding="utf-8") as _f:
    for _s in _f:
        _w, _n = _s.rstrip("\n").split("\t")
        SIK[_w] = int(_n)
KOD={"ب":"B","پ":"B","ت":"D","ط":"D","د":"D","ث":"S","س":"S","ص":"S","ج":"C","چ":"C","ح":"H","خ":"H","ه":"H",
     "ذ":"Z","ز":"Z","ض":"Z","ظ":"Z","ر":"R","ژ":"J","ش":"Ş","غ":"K","ق":"K","ك":"K","گ":"K","ف":"F","ل":"L","م":"M","ن":"N"}
LKOD={"b":"B","p":"B","t":"D","d":"D","s":"S","c":"C","ç":"C","h":"H","z":"Z","r":"R","j":"J","ş":"Ş","g":"K","ğ":"K","k":"K","f":"F","l":"L","m":"M","n":"N"}
def ar_anahtar(w, son_he=True):
    out=[]
    for i,ch in enumerate(w):
        if ch=="ه" and i==len(w)-1 and not son_he: continue
        if ch in KOD:
            if out and out[-1]==KOD[ch] and w[i-1]==ch: continue
            out.append(KOD[ch])
    return "".join(out)
def lat_anahtar(l):
    out=[]; prev=""
    for ch in l:
        if ch in LKOD:
            if ch==prev: prev=ch; continue
            out.append(LKOD[ch])
        prev=ch
    return "".join(out)
INDEX=collections.defaultdict(list)
for w,n in SIK.items():
    if n<3 or len(w)<3: continue
    INDEX[ar_anahtar(w)].append(w)
    if w.endswith("ه"): INDEX[ar_anahtar(w,False)].append(w)
    if w.endswith("ة"): INDEX[ar_anahtar(w)+"D"].append(w)
IZIN={"b":"بپ","c":"جچ","ç":"چج","d":"دضذطت","f":"ف","g":"گغكق","ğ":"غگكی","h":"حهخ","j":"ژج","k":"كقگ","l":"ل",
      "m":"م","n":"نڭ","p":"پب","r":"ر","s":"سصث","ş":"ش","t":"تطثدة","v":"و","y":"ی","z":"زذضظ"}
UZUN={"â":"اآ","î":"ی","û":"و"}
KISA={"a":"اآ","e":"","ı":"ی","i":"یئ","u":"و","ü":"و","o":"و","ö":"و"}
def uyum(lat, ar):
    L=lat; A=ar; n,m=len(L),len(A); INF=99
    d=[[INF]*(m+1) for _ in range(n+1)]; d[0][0]=0
    for i in range(n+1):
        for j in range(m+1):
            v=d[i][j]
            if v>=INF: continue
            if i<n:
                c=L[i]
                if j<m:
                    a=A[j]; ok=False
                    if c in IZIN and a in IZIN[c]: ok=True
                    if c=="t" and a=="د" and i!=n-1: ok=False          # t -> د yalnız sonda (maksat مقصد)
                    if c=="e" and a in "اآ" and i==0: ok=True           # başta e -> ا (ehl اهل)
                    if c in "aeâ" and a=="ی" and j==m-1 and i==n-1: ok=True  # sonda elif-i maksûre (mana معنی)
                    if c in "aeıioöuüâîû" and i==0 and j<=1 and a in "اآع": ok=True   # baştaki ünlü: istidat استعداد, ilim علم
                    ek = 0.3 if (ok and c in "aıiuüoö" and 0<i<n-1 and a in "اوی" and not (c in KISA and a in KISA.get(c,"") and False)) else 0
                    if c in UZUN and a in UZUN[c]: ok=True
                    if c in KISA and a in KISA[c]: ok=True
                    if c in "ae" and a in "هة" and j==m-1: ok=True
                    if ok:
                        d[i+1][j+1]=min(d[i+1][j+1],v+ek)
                        if c not in "aeıioöuüâîû" and j+1<m and A[j+1]==a:   # yazıda iki harf, Türkçede tek
                            pass
                    if c not in "aeıioöuüâîû" and i+1<n and L[i+1]==c and ok:   # çift ünsüz = şedde, tek harf
                        d[i+2][j+1]=min(d[i+2][j+1],v)
                # Latin harfi atla
                if c in "aeıioöuü" and (i==0 or i==n-1): d[i+1][j]=min(d[i+1][j],v+1)  # baştaki/sondaki ünlü yazılır
                elif c in "aeıioöuü": d[i+1][j]=min(d[i+1][j],v)        # ortadaki kısa ünlü yazılmaz
                elif c=="y" and i>0 and L[i-1]=="i": d[i+1][j]=min(d[i+1][j],v)   # -iyet: ی tek (انسانیة)
                elif c in UZUN: d[i+1][j]=min(d[i+1][j],v+1)
                else: d[i+1][j]=min(d[i+1][j],v+2)
            if j<m:
                a=A[j]
                if a in "عءئؤأ": d[i][j+1]=min(d[i][j+1],v)
                elif a in "اویآ": d[i][j+1]=min(d[i][j+1],v+(0 if (a=="ا" and i==0 and j==0) else 1))
                elif a=="ل" and j>0 and A[j-1]=="ا": d[i][j+1]=min(d[i][j+1],v)
                else: d[i][j+1]=min(d[i][j+1],v+2)
    return d[n][m]
def oner(latin):
    l=latin.lower()
    anah=lat_anahtar(l)
    aday=set(INDEX.get(anah,[]))
    if l[-1:] in "tdpbcç":  # son ünsüz yumuşaması
        pass
    sonuc=[]
    import math
    for w in aday:
        c=uyum(l,w)
        if c<1: sonuc.append((math.log(SIK[w])-3*c,SIK[w],w))
    sonuc.sort(reverse=True)
    sonuc=[(n,w) for _,n,w in sonuc]
    if not sonuc: return None
    out=[]
    for n,w in sonuc[:3]:
        if w.endswith("ة"): w=w[:-1]+("ت" if l.endswith(("t","d")) else "ه")
        out.append((w,n))
    return out
if __name__=="__main__":
    for x in sys.argv[1:]: print(x, oner(x))
