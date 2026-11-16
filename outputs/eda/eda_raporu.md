# TÜİK 2024 il verileri — EDA ve özellik incelemesi

Kaynak: `outputs\tuik_2024_81_il_birlesik.csv`. Kapsam: 81 il, 8 sütun. Veri dönüştürülmedi ve model eğitilmedi.

## Genel veri kontrolü

- İl kodları 1–81 arasında benzersizdir.
- Seçilen sayısal özelliklerde eksik veya sonlu olmayan değer yoktur.
- Her özellik 81 il için hesaplandı.

## Özet istatistikler

| ozellik | minimum | maksimum | ortalama | medyan | standart_sapma | carpiklik |
|---|---|---|---|---|---|---|
| kisi_basi_gsyh_tl | 188144.3820 | 802669.2435 | 387261.5507 | 365241.3189 | 122054.3402 | 1.3345 |
| isgucune_katilma_orani | 41.6263 | 63.9390 | 52.5917 | 52.8365 | 4.5393 | -0.2365 |
| issizlik_orani | 4.0199 | 18.2914 | 8.4189 | 7.6630 | 2.6669 | 1.1055 |
| istihdam_orani | 35.2572 | 60.6296 | 48.2188 | 48.9240 | 4.9113 | -0.3627 |
| ortalama_egitim_suresi | 7.4978 | 10.7955 | 9.0068 | 9.0184 | 0.5727 | 0.1913 |
| nufus_yogunlugu | 11.3922 | 2933.6273 | 136.0447 | 62.4040 | 330.0379 | 7.8505 |

## Korelasyon

Yüksek korelasyon eşiği: mutlak Pearson veya Spearman katsayısı ≥ 0.80.

| özellik_1 | özellik_2 | Pearson | Spearman |
|---|---|---|---|
| isgucune_katilma_orani | istihdam_orani | 0.9708 | 0.9682 |

### İşgücü göstergeleri

Katılım, işsizlik ve istihdam oranları aynı işgücü yapısının bağlantılı ölçüleridir. Üçünü birlikte kullanmak ayrıntıyı koruyabilir; özellikle katılım ve istihdam yüksek korelasyonluysa uzaklık temelli kümelemede benzer bilgiyi iki kez ağırlıklandırabilir. Nihai seçim, sonraki aşamada farklı özellik kümeleri karşılaştırılarak yapılmalıdır.

| özellik | isgucune_katilma_orani | issizlik_orani | istihdam_orani |
|---|---|---|---|
| isgucune_katilma_orani | 1.0000 | -0.4578 | 0.9708 |
| issizlik_orani | -0.4578 | 1.0000 | -0.6566 |
| istihdam_orani | 0.9708 | -0.6566 | 1.0000 |

## Dağılım ve çarpıklık

- Kişi başına GSYH: çarpıklık 1.334; |çarpıklık| ≥ 1.0 ölçütüne göre belirgin çarpık.
- Nüfus yoğunluğu: çarpıklık 7.851; |çarpıklık| ≥ 1.0 ölçütüne göre belirgin çarpık.

## IQR aykırı değer adayları

Sınırlar Q1 − 1,5×IQR ve Q3 + 1,5×IQR'dir. Bu işaretler veri hatası kanıtı değildir; GSYH ve nüfus yoğunluğundaki uç iller gerçek farklılıkları yansıtabilir.

| ozellik | alt_sinir | ust_sinir | aday_sayisi |
|---|---|---|---|
| kisi_basi_gsyh_tl | 123253.1238 | 637665.4490 | 3.0000 |
| isgucune_katilma_orani | 40.5912 | 65.2118 | 0.0000 |
| issizlik_orani | 1.2721 | 15.4597 | 2.0000 |
| istihdam_orani | 35.3277 | 61.2433 | 1.0000 |
| ortalama_egitim_suresi | 7.4942 | 10.5192 | 1.0000 |
| nufus_yogunlugu | -72.7861 | 239.5319 | 7.0000 |

### Kişi başına GSYH (3 aday)

| İl | Değer | Yön |
|---|---|---|
| Ankara | 788858.9205 | üst |
| İstanbul | 802669.2435 | üst |
| Kocaeli | 788872.5901 | üst |

### İşgücüne katılma oranı (0 aday)

Aday yok.

### İşsizlik oranı (2 aday)

| İl | Değer | Yön |
|---|---|---|
| Hakkari | 18.2914 | üst |
| Van | 16.7410 | üst |

### İstihdam oranı (1 aday)

| İl | Değer | Yön |
|---|---|---|
| Hakkari | 35.2572 | alt |

### Ortalama eğitim süresi (1 aday)

| İl | Değer | Yön |
|---|---|---|
| Ankara | 10.7955 | üst |

### Nüfus yoğunluğu (7 aday)

| İl | Değer | Yön |
|---|---|---|
| Bursa | 311.9241 | üst |
| Gaziantep | 324.8692 | üst |
| Hatay | 280.7603 | üst |
| İstanbul | 2933.6273 | üst |
| İzmir | 375.4221 | üst |
| Kocaeli | 623.3886 | üst |
| Yalova | 390.1413 | üst |

## Özellik değerlendirmesi

- **Üç işgücü göstergesi gerekli mi?** Bu aşamada karar verilmedi. Yukarıdaki korelasyonlar ve göstergeler arasındaki matematiksel ilişki, birlikte kullanımın işgücüne fazla ağırlık verebileceğini gösterir.
- **Ölçekleme:** TL, yüzde, yıl ve kişi/km² birimleri farklı büyüklüktedir. StandardScaler ortalama ve standart sapmayı kullanır; uç değerler bu ölçüleri etkileyebilir. RobustScaler medyan ve çeyrekler arası aralığı kullanır; çok çarpık dağılımlarda ve uç değerlerde karşılaştırılmaya değerdir. Bu betik iki yöntemi de uygulamaz.
- **Birlikte kullanım:** Katılım ve istihdam gibi yüksek korelasyonlu ölçüler aynı boyutun ağırlığını artırabilir. GSYH ve yoğunluk da ayrı ayrı incelemeye değerdir. Hiçbir özellik silinmedi; nihai özellik seçimi yapılmadı.

## Çıktılar

Özet istatistikler, Pearson ve Spearman korelasyon CSV'leri, IQR aday tablosu ve `grafikler/` altındaki altı dağılım grafiği ile iki ısı haritası birlikte incelenmelidir.
