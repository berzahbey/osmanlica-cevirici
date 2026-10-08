# Osmanlıca Çevirici

Herhangi bir dildeki metni / dosyayı (pdf, epub, txt, jpg, png) alıp Osmanlı Türkçesine
(Arap harfli, Nesih tarzı — Scheherazade New fontu) çeviren, kendi ZimaOS sunucunuzda
çalışan bir Docker uygulaması.

## ⚠️ Önce oku: gerçekçi beklenti

Bu sistem üç katmandan oluşur:
1. **Sözlük** — bilinen kelimelerin standart Osmanlıca yazımı (şu an ~90 kelime, `app/data/ottoman_dict.tsv` ile büyütülebilir)
2. **Kural motoru** — sözlükte olmayan Türkçe kelimeler için yaklaşık harf çevirisi
3. **Ollama düzeltme katmanı** — yerel modelin taslağı gözden geçirip düzeltmesi

Yerel küçük bir model (7B-14B) ile sonuç **"mükemmel" olmayacak** — özellikle Arapça/Farsça
kökenli az bilinen kelimelerde hatalar görürsünüz. Sözlüğü siz büyüttükçe (ya da benimle
birlikte oturup genişlettikçe) kalite artacak. Bunu bir kerede "bitmiş ürün" değil,
**üzerinde birlikte çalışacağımız canlı bir sistem** olarak düşünün.

## Kurulum (MacBook'tan terminal ile)

### 1. Dosyaları ZimaOS sunucusuna kopyala

MacBook'unda terminali aç:

```bash
# Klasörü ZimaOS'a kopyala (IP adresini ve kullanıcı adını kendine göre değiştir)
scp -r osmanlica-cevirici KULLANICI_ADIN@ZIMAOS_IP:/home/KULLANICI_ADIN/
```

Eğer `scp` çalışmazsa, önce ZimaOS'ta SSH'ın açık olduğundan emin ol
(ZimaOS web arayüzü > Ayarlar > SSH).

### 2. ZimaOS'a SSH ile bağlan

```bash
ssh KULLANICI_ADIN@ZIMAOS_IP
cd osmanlica-cevirici
```

### 3. Ollama modelini kontrol et / indir

Ollama zaten kurulu olduğunu söylemiştin. Hangi modelin kurulu olduğunu kontrol et:

```bash
ollama list
```

Osmanlıca gibi niş bir görev için, kurulu değilse şunlardan birini indirmeni öneririm
(NAB7'nin RAM'ine göre seç — Intel N-serisi mini PC'lerde genelde 7B-8B rahat çalışır,
14B yavaş olabilir):

```bash
ollama pull qwen2.5:7b
# ya da RAM yeterliyse:
ollama pull qwen2.5:14b
```

Qwen modellerini öneriyorum çünkü Çince/Arapça/çok dilli veri setleriyle eğitildikleri
için Arapça harfli metinlerde genelde Llama serisinden daha iyi performans gösteriyor.

`docker-compose.yml` içindeki `OLLAMA_MODEL` değerini indirdiğin modelle eşleştir.

### 4. Ollama'nın adresini doğrula

Ollama'yı nasıl kurduğuna göre `docker-compose.yml` içindeki `OLLAMA_HOST` değişmeli:

- **Ollama, sunucuda doğrudan (Docker dışı) kuruluysa:** mevcut ayar (`host.docker.internal`)
  muhtemelen çalışır. Çalışmazsa ZimaOS'un gerçek LAN IP'sini yaz: `http://192.168.X.X:11434`
- **Ollama da bir Docker container ise:** aynı docker network'e alıp
  `http://ollama:11434` gibi container adını kullanman gerekir — bu durumda bana
  Ollama'yı nasıl çalıştırdığını söyle, compose dosyasını ona göre düzenleyelim.

### 5. Build et ve çalıştır

```bash
docker compose up -d --build
```

İlk build birkaç dakika sürer (font indirme, OCR paketleri, Python kütüphaneleri).

### 6. Kullan

Tarayıcıdan: `http://ZIMAOS_IP:8088`

Metin yapıştır ya da dosya yükle, "Çevir" / "Yükle ve Çevir" de. İşlem durumunu
sayfa otomatik gösterir (dosya büyükse ve Ollama devrede ise dakikalar/saatler
sürebilir — sen zaten hızın önemli olmadığını söylemiştin, bu yüzden zaman aşımını
yüksek tuttum).

### 7. Logları izlemek istersen

```bash
docker compose logs -f
```

## Sözlüğü büyütme

`app/data/ottoman_dict.tsv` dosyasını düzenle, satır formatı:

```
latin_kelime<TAB>osmanlica_yazim<TAB>koken
```

Örnek:
```
kütüphane	كتابخانه	ar-fa
```

Kaydettikten sonra container'ı yeniden başlatmana gerek yok, ama emin olmak için:
```bash
docker compose restart
```

## Bilinen sınırlamalar (v1)

- OCR (jpg/png) Türkçe+İngilizce dil paketiyle geliyor; el yazısı ya da eski Osmanlıca
  matbu OCR için ayrı, çok daha zor bir problem (bunu istersen ayrıca konuşalım)
- Kural motoru, Türkçe kökenli kelimelerde YAKLAŞIK sonuç verir; bazı kelimelerde
  akademik Osmanlıca imla ile farklılık gösterebilir
- Çok büyük dosyalarda (uzun kitaplar) Ollama katmanı devredeyse işlem gerçekten
  saatler sürebilir — bunu kapatıp (checkbox'ı kaldırarak) hızlı ama daha kaba
  sonuç da alabilirsin
- epub/pdf render'ı basit düzeyde; karmaşık sayfa düzenleri (çok sütunlu pdf,
  gömülü görseller) korunmaz, sadece metin çıkar

## Sonraki adımlar için öneriler

Bir sonraki oturumda birlikte şunları geliştirebiliriz:
- Sözlüğü ciddi şekilde büyütmek (elindeki gerçek bir Osmanlıca sözlükten kontrollü veri girişi)
- Kural motorunu daha fazla istisnaya göre iyileştirmek
- OCR kalitesini artırmak (özellikle taranmış eski kitaplar için)
- İşlem kuyruğunu kalıcı hale getirmek (şu an bellekte tutuluyor, container yeniden
  başlarsa geçmiş işler kaybolur)
