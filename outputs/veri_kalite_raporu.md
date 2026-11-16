# TÜİK 2024 veri kalite raporu

## Kaynaklar ve kullanılan alanlar

| Kaynak dosya | Sayfa | Tüm sayfalar | Başlık / veri başlangıcı | Kimlik alanları | 2024 alanı | Birim | SHA-256 |
|---|---|---|---|---|---|---|---|
| İl bazında kişi başına gayrisafi yurt içi hasıla 2020-2024.xlsx | T3 | T3 | 4 / 5 | İBBS kodu A, il adı B | kisi_basi_gsyh_tl (7. sütun) | TL | `10ba63c70429c86976ac85240a6829ded44e007e67c147bf830a8a2a91d2871a` |
| İl düzeyinde işgücüne katılma oranı.xlsx | Tablo | Tablo | 6 / 7 | İBBS kodu A, il adı B | isgucune_katilma_orani (13. sütun) | % | `3081940ec7fc2265d10309c2c9aea2c7f6826aa2898c7665b15f915bddce048f` |
| İl düzeyinde işsizlik oranı.xlsx | Tablo | Tablo | 6 / 7 | İBBS kodu A, il adı B | issizlik_orani (13. sütun) | % | `7ab98a310a98906157ac8b348c1a728b083947714350fb1c7e9979eba3e3e0a3` |
| İl düzeyinde istihdam oranı.xlsx | Tablo | Tablo | 6 / 7 | İBBS kodu A, il adı B | istihdam_orani (13. sütun) | % | `2ccfc1b4d9421adffb62657d6b6c6bdf08b3ff4173c254b2dd4e101bcf1e5043` |
| İllere göre ortalama eğitim süresi.xlsx | t9 | t9 | 6 / 7 | İl kodu A, il adı B | ortalama_egitim_suresi (8. sütun) | yıl | `9640c4a2d8f04696ceb99ddafe1bcb9c4e31f08ce059e5a3be8773ea590ef0a9` |
| İl ve cinsiyete göre il_ilçe merkezi, belde_köy nüfusu ve nüfus yoğunluğu.xlsx | t3 | t3 | 4 / 5 | İl adı A | nufus_yogunlugu (13. sütun) | kişi/km² | `2833df7efe884b7ecbae6dbacffc7a4ebb6b81bbcf4200457c05b6faf04555ae` |

Tüm seçilen değerler 2024 yılına aittir. GSYH için TL, eğitim için toplam, nüfus yoğunluğu için il toplamı kullanıldı. GSYH ve işgücü dosyalarındaki İBBS kodları il adlarıyla çapraz denetlendi; nüfus dosyası adla eşleştirildi. Türkiye toplam satırları dışarıda bırakıldı.

## Kapsam ve eşleşme

- Birleşik il sayısı: **81**. İl kodları 1–81 ve benzersiz.
- Eksik, tekrar eden veya sayısal olmayan seçilmiş değer: **0**.
- Eşleşmeyen il: **0**.
- Toplam satırları: her kaynakta 1; birleşik veriye alınmadı.

| Dosya | Eşleşen | Eşleşmeyen | Tekrar | Sayısal eksik |
|---|---:|---:|---:|---:|
| İl bazında kişi başına gayrisafi yurt içi hasıla 2020-2024.xlsx | 81 | 0 | 0 | 0 |
| İl düzeyinde işgücüne katılma oranı.xlsx | 81 | 0 | 0 | 0 |
| İl düzeyinde işsizlik oranı.xlsx | 81 | 0 | 0 | 0 |
| İl düzeyinde istihdam oranı.xlsx | 81 | 0 | 0 | 0 |
| İllere göre ortalama eğitim süresi.xlsx | 81 | 0 | 0 | 0 |
| İl ve cinsiyete göre il_ilçe merkezi, belde_köy nüfusu ve nüfus yoğunluğu.xlsx | 81 | 0 | 0 | 0 |

## Sayısal özet

| Özellik | Minimum | Maksimum | Ortalama |
|---|---:|---:|---:|
| kisi_basi_gsyh_tl | 188144.3820 | 802669.2435 | 387261.5507 |
| isgucune_katilma_orani | 41.6263 | 63.9390 | 52.5917 |
| issizlik_orani | 4.0199 | 18.2914 | 8.4189 |
| istihdam_orani | 35.2572 | 60.6296 | 48.2188 |
| ortalama_egitim_suresi | 7.4978 | 10.7955 | 9.0068 |
| nufus_yogunlugu | 11.3922 | 2933.6273 | 136.0447 |

## İşgücü göstergelerinin korelasyonu

| | Katılım | İşsizlik | İstihdam |
|---|---:|---:|---:|
| Katılım | 1.0000 | -0.4578 | 0.9708 |
| İşsizlik | -0.4578 | 1.0000 | -0.6566 |
| İstihdam | 0.9708 | -0.6566 | 1.0000 |

## Doğrulama ve sorunlar

- İşgücü özdeşliği `istihdam ≈ katılım × (1 − işsizlik/100)` için en büyük fark: **0.000000 yüzde puan**; kabul sınırı 0,2 yüzde puan. Göstergeler farklı örnekleme ve yuvarlama biçimlerine sahip olabilir.
- 30 seçilmiş kaynak hücresi birleşik veriyle karşılaştırıldı; tümü aynı.
- CSV UTF-8-SIG olarak yazılıp geri okundu.
- Kaynak hücreleri pandas tarafından sayısal türde okundu; `802.669,24` gibi metin değerleri için Türkçe ondalık dönüştürücü ayrıca tanımlandı. İstanbul GSYH kaynak değeri ve çıktı yaklaşık 802669,24354 TL.
- Seçilmiş 2024 alanlarında veri kalitesi sorunu saptanmadı.

## Sonraki aşama

- Ölçek farkları büyük olduğundan modelleme öncesinde özellikleri ölçeklendirmeyi ve uç değerleri incelemeyi düşünün. Bu aşamada hiçbir model veya ölçekleme uygulanmadı.
- Katılım, işsizlik ve istihdam bağlantılı ölçülerdir. Üçünü kullanmak işgücü durumunu ayrıntılı yansıtır; ancak aynı bilgiyi birkaç kez ağırlıklandırıp uzaklık temelli kümeleri etkileyebilir. Özellik seçimini ve küme duyarlılığını sonraki aşamada karşılaştırın.
