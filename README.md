# Osmanlıca Çevirici

Türkçe metni ya da dosyayı (pdf, epub, txt, jpg, png) Osmanlıcaya (Arap harfli) çeviren Docker uygulaması.
Kişisel, ticari olmayan proje; Dedplay Stüdyo'nun parçası olarak ZimaOS sunucusunda çalışır (stack servisi `osmanlica`, port 8089).

## Nasıl çalışır
1. **Hayrat çok kelimeli ifadeler** (`app/data/hayrat_ifade.tsv`).
2. **Sözlük**: `ottoman_dict.tsv` -> `duzeltmeler.tsv` -> `hayrat.tsv` (en son yüklenen ezer; Hayrat tek ölçü).
3. **Kural motoru**: sözlükte olmayan kelimeler için Türkçe imlâ kuralları.

Yapay zekâ (Ollama) kullanılmaz: aynı metin her zaman aynı Osmanlıcayı verir, testler bunu sınar.
Yalnız Türkçe metin alınır (çeviri yok).

## İmlâ ölçüsü
Risale-i Nur'un orijinal Osmanlıca nüshası (Hayrat). g sesi kef (ك); Arapça/Farsça kelimeler aslî imlâsıyla, şedde açık.

## Testler
```
docker run --rm -v "$PWD":/k -w /k berzahbey/osmanlica-cevirici:latest python tests/test_imla.py
```
Hayrat araçları: `tools/` (hayrat_test, hayrat_sinav, hayrat_sozluk_uret). Kur'an mealleri test seti: `tests/mealler/`.
