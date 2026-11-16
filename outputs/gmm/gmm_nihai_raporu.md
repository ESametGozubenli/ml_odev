# Nihai GMM raporu — 3 bileşen

## 1. Veri ve hazırlık

Girdi `outputs/preprocessing/iller_olceklendirilmis.csv`: 81 ilin beş StandardScaler ile ölçeklendirilmiş özelliği. `kisi_basi_gsyh_tl`, `issizlik_orani`, `istihdam_orani`, `ortalama_egitim_suresi`, `nufus_yogunlugu`. `il_kodu` ve `il_adi` model girdisi değildir; yalnız il sonuçlarını kaynakla eşleştirmek için kullanıldı. Eksik/sonsuz değer ve tekrar eden il kodu kontrol edildi. Kümelerin sosyoekonomik yorumu için orijinal birleşik TÜİK verisi ayrıca okundu ve il sırası doğrulandı.

## 2. Bileşen sayısı nasıl araştırıldı?

2–10 arası dokuz tam kovaryanslı GMM denendi. Her modelde `random_state=42`, `n_init=10`, `max_iter=500`, `reg_covar=1e-06` kullanıldı. `n_init=10` farklı başlangıçlar dener; yakınsama kontrol edildi. Her modelin BIC, AIC ve en yüksek üyelik olasılığına göre atanan etiketlerin Silhouette değeri hesaplandı. BIC/AIC için düşük, Silhouette için yüksek değer tercih edilir. `logL` toplam log-olasılık, `p` serbest parametre sayısı ve `n=81` iken `BIC=-2×logL+p×ln(n)`, `AIC=-2×logL+2p`. Tam tarama `bilesen_arastirmasi.csv` ve `bilesen_arastirmasi_raporu.md` içindedir.

## 3. Neden 3 bileşen seçildi?

İki bileşende BIC 837.00, Silhouette 0.5050; kümeler 76, 5 il. Silhouette en yüksek olsa da çoğu il tek grupta kalır. Üç bileşende BIC **816.39** ile en düşük; kümeler 50, 27, 4 il ve Silhouette 0.2964. Dört bileşende BIC 872.45 seviyesine yükselir, tek illik küme oluşur. AIC on bileşende 437.65 ile en düşük olsa da çok küçük/tek illik gruplar artar ve Silhouette düşer. Bu nedenle BIC, ayrımın yorumlanabilirliği ve küçük küme riskini birlikte değerlendirerek kullanıcı onayıyla 3 bileşen seçildi. Dört illik küme yine de dikkatle incelenmelidir.

## 4. Nihai model nasıl hesaplandı?

Aynı ayarlarla 3 bileşenli GMM yeniden uyduruldu. Model, her il için üç bileşene ait posterior üyelik olasılığını hesapladı. Her olasılık 0–1 arasındadır ve bir ilin üç olasılığı toplamı 1'dir. En yüksek olasılığa sahip bileşen ilin `kume` etiketi oldu. Nihai BIC, AIC, Silhouette ve küme büyüklükleri araştırmadaki 3 bileşen sonucuyla karşılaştırılıp doğrulandı.

Nihai BIC **816.39**, AIC **667.94**, Silhouette **0.2964**. Silhouette 81 ilin tamamını kapsar. Küme numaraları gelişmişlik sırası belirtmez.

## 5. Küme illeri

### Küme 0 — 50 il

Afyonkarahisar, Amasya, Antalya, Artvin, Balıkesir, Bilecik, Bingöl, Bolu, Burdur, Çanakkale, Çankırı, Çorum, Denizli, Edirne, Elazığ, Erzincan, Erzurum, Eskişehir, Giresun, Isparta, Mersin, Kars, Kastamonu, Kayseri, Kırklareli, Kırşehir, Konya, Kütahya, Malatya, Manisa, Muğla, Nevşehir, Niğde, Ordu, Rize, Samsun, Sinop, Sivas, Tekirdağ, Tokat, Tunceli, Uşak, Yozgat, Aksaray, Bayburt, Karaman, Şırnak, Bartın, Ardahan, Düzce.

### Küme 1 — 27 il

Adana, Adıyaman, Ağrı, Aydın, Bitlis, Bursa, Diyarbakır, Gaziantep, Gümüşhane, Hakkari, Hatay, Kahramanmaraş, Mardin, Muş, Sakarya, Siirt, Trabzon, Şanlıurfa, Van, Zonguldak, Kırıkkale, Batman, Iğdır, Yalova, Karabük, Kilis, Osmaniye.

### Küme 2 — 4 il

Ankara, İstanbul, İzmir, Kocaeli.

## 6. Orijinal TÜİK değerleriyle küme profilleri

Aşağıdaki ortalamalar ölçeklendirilmiş sayılardan değil, orijinal TÜİK değerlerinden hesaplandı. GSYH TL, işsizlik ve istihdam %, eğitim yıl, yoğunluk kişi/km² birimindedir.

| Küme | İl sayısı | GSYH (TL) | İşsizlik (%) | İstihdam (%) | Eğitim (yıl) | Yoğunluk (kişi/km²) |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 50 | 398,051.10 | 6.77 | 50.16 | 9.00 | 64.29 |
| 1 | 27 | 315,883.48 | 11.30 | 44.13 | 8.84 | 134.70 |
| 2 | 4 | 734,194.14 | 9.56 | 51.62 | 10.23 | 1,042.12 |

Küme ortalamaları her ilin aynı özellikleri taşıdığı anlamına gelmez. Dört illik kümenin ortalaması az sayıda ile dayandığı için özellikle dikkatli yorumlanmalıdır.

### Sayısal yorum

Küme 0'da ortalama kişi başına GSYH 398,051 TL, işsizlik %6.77 ve istihdam %50.16. Küme 1'de GSYH 315,883 TL ile daha düşük; işsizlik %11.30 ile 4.52 yüzde puan daha yüksek, istihdam %44.13 ile 6.03 yüzde puan daha düşük. Bu farklar ortalama profilleri gösterir; nedensel bir ilişki veya her il için geçerli bir kural değildir.

Ankara, İstanbul, İzmir ve Kocaeli'den oluşan Küme 2'de ortalama GSYH 734,194 TL, eğitim 10.23 yıl. Bu iki ortalama diğer kümelerden yüksektir. Ortalama nüfus yoğunluğu 1,042 kişi/km² olsa da İstanbul'un çok yüksek yoğunluğu dört illik ortalamayı güçlü biçimde etkiler; dört ilin aynı derecede yoğun olduğu sonucuna varılmamalıdır.

## 7. Üyelik olasılıkları ve belirsizlik

GMM, sert etiketin yanında her ilin üç bileşene ait olasılıklarını verir. `atanma_olasiligi`, bu üç değerin en yükseğidir. Yüksek değer modelin bu il için daha net atama yaptığını gösterir; gerçek dünyada kesinlik veya nedensellik kanıtı değildir. En düşük atanma olasılığına sahip on il (tabloda `0.000` görünen olasılıklar üç ondalığa yuvarlanmıştır):

| İl | Atanan küme | Küme 0 | Küme 1 | Küme 2 | En yüksek |
| --- | ---: | ---: | ---: | ---: | ---: |
| Karabük | 1 | 0.453 | 0.547 | 0.000 | 0.547 |
| Samsun | 0 | 0.583 | 0.417 | 0.000 | 0.583 |
| Ordu | 0 | 0.640 | 0.360 | 0.000 | 0.640 |
| Düzce | 0 | 0.829 | 0.171 | 0.000 | 0.829 |
| Kırşehir | 0 | 0.855 | 0.145 | 0.000 | 0.855 |
| Sivas | 0 | 0.862 | 0.138 | 0.000 | 0.862 |
| Şırnak | 0 | 0.867 | 0.133 | 0.000 | 0.867 |
| Kayseri | 0 | 0.897 | 0.103 | 0.000 | 0.897 |
| Rize | 0 | 0.937 | 0.063 | 0.000 | 0.937 |
| Aydın | 1 | 0.039 | 0.961 | 0.000 | 0.961 |

0,80'in altında en yüksek üyelik olasılığı olan il sayısı: 3. 0,60'ın altında: 2. Tüm 81 ilin olasılıkları `uyelik_olasiliklari.csv` içindedir.

## 8. Bileşen ortalamaları ve sınırlamalar

Aşağıdaki değerler modelin ölçekli uzaydaki Gauss bileşen ortalamalarıdır; sert atanmış illerin basit aritmetik ortalamalarından farklı olabilir.

| Küme | kisi_basi_gsyh_tl | issizlik_orani | istihdam_orani | ortalama_egitim_suresi | nufus_yogunlugu |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 0.099 | -0.621 | 0.395 | -0.004 | -0.222 |
| 1 | -0.576 | 1.012 | -0.782 | -0.298 | -0.007 |
| 2 | 2.860 | 0.430 | 0.697 | 2.148 | 2.762 |

GMM olasılıkları seçilen üç bileşenli tam kovaryans modeline bağlıdır. 81 gözlem ve küçük bir küme varken olasılıklar fazla kesin görünebilir. K-Means ve DBSCAN ile farklı kümelerin oluşması algoritmaların varsayımlarından kaynaklanabilir; nihai karşılaştırma sonraki aşamada yapılacaktır. Bu aşamada PCA veya t-SNE uygulanmadı.
