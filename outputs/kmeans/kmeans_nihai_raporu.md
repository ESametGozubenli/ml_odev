# Nihai K-Means raporu — K=3

## Veri ve hesaplama yöntemi

81 ilin beş StandardScaler ile ölçeklendirilmiş özelliği kullanıldı: `kisi_basi_gsyh_tl`, `issizlik_orani`, `istihdam_orani`, `ortalama_egitim_suresi`, `nufus_yogunlugu`. `il_kodu` ve `il_adi` modele verilmedi. K=2–10 aralığındaki her değer için ayrı bir K-Means modeli `random_state=42` ve `n_init=20` ile uyduruldu. `n_init=20`, 20 farklı başlangıç arasından en düşük WCSS'li çözümü seçer. Böylece sonuç başlangıç merkezlerine daha az bağımlıdır.

**WCSS (inertia)**, her ilin beş boyutlu ölçekli konumu ile kendi küme merkezi arasındaki uzaklığın karesinin toplamıdır: `Σ_i ||x_i - μ_küme(i)||²`. Daha küçük değer daha sıkı kümeler demektir; K arttıkça WCSS doğal olarak düşer. Elbow yöntemi, düşüşün belirgin biçimde yavaşladığı K'yi arar.

**Silhouette Score** için her ilin kendi kümesindeki diğer illere ortalama uzaklığı `a`, en yakın başka kümeye ortalama uzaklığı `b` olarak hesaplanır. İl skoru `(b-a)/max(a,b)`; tabloda 81 ilin ortalaması yer alır. Değerin yüksek olması genellikle daha iyi ayrışma gösterir. Tek elemanlı kümedeki ilin Silhouette değeri sklearn tarafından 0 kabul edilir.

## Neden K=3 seçildi?

K=2: WCSS 282.935, Silhouette 0.3314; iki küme 25 ve 56 il içeriyor. K=3: WCSS 195.755, Silhouette 0.3530; 55, 25 ve 1 illik kümeler oluştu. K=4: WCSS 141.816, Silhouette 0.3182; 42, 14, 24 ve 1 illik kümeler oluştu.

K=3, denenen değerler içinde en yüksek Silhouette skorunu verdi. K=2'den K=3'e geçişte WCSS belirgin düştü. Elbow grafiğinde yavaşlama K=4 civarında görülüyor; tek ve tartışmasız bir dirsek yok. K=4'ün Silhouette skoru K=3'ten düşük. K=3'te tek illik küme bulunması kararın önemli sınırlamasıdır: bu il ayrı bir şehir profili olabilir, fakat genel küme kalitesini tek başına kanıtlamaz. K=2 daha dengeli bir karşılaştırma seçeneğidir. Bu gerekçelerle K=3 kullanıcı onayıyla nihai K-Means modeli olarak seçildi.

## Nihai sonuç

Silhouette Score: **0.3530**. Küme numaraları yalnızca kimliktir; sıralama veya başarı derecesi belirtmez. Tek illik küme bir hesaplama hatası değildir, ancak diğer algoritmalarla karşılaştırırken özellikle dikkate alınmalıdır.

| Küme | İl sayısı | İller |
| ---: | ---: | --- |
| 0 | 55 | Afyonkarahisar, Amasya, Ankara, Antalya, Artvin, Aydın, Balıkesir, Bilecik, Bolu, Burdur, Bursa, Çanakkale, Çankırı, Çorum, Denizli, Edirne, Elazığ, Erzincan, Erzurum, Eskişehir, Giresun, Isparta, Mersin, İzmir, Kars, Kastamonu, Kayseri, Kırklareli, Kocaeli, Konya, Kütahya, Malatya, Manisa, Muğla, Nevşehir, Niğde, Ordu, Rize, Sakarya, Samsun, Sinop, Sivas, Tekirdağ, Tokat, Trabzon, Tunceli, Uşak, Yozgat, Aksaray, Bayburt, Karaman, Bartın, Ardahan, Yalova, Düzce |
| 1 | 25 | Adana, Adıyaman, Ağrı, Bingöl, Bitlis, Diyarbakır, Gaziantep, Gümüşhane, Hakkari, Hatay, Kırşehir, Kahramanmaraş, Mardin, Muş, Siirt, Şanlıurfa, Van, Zonguldak, Kırıkkale, Batman, Şırnak, Iğdır, Karabük, Kilis, Osmaniye |
| 2 | 1 | İstanbul |

## Küme merkezleri (ölçeklendirilmiş değerler)

| Küme | kisi_basi_gsyh_tl | issizlik_orani | istihdam_orani | ortalama_egitim_suresi | nufus_yogunlugu |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 0.302 | -0.505 | 0.493 | 0.185 | -0.107 |
| 1 | -0.801 | 1.105 | -1.122 | -0.492 | -0.106 |
| 2 | 3.425 | 0.162 | 0.945 | 2.128 | 8.529 |

Merkezlerde 0 yaklaşık 81 il ortalamasını; pozitif/negatif değerler ortalamanın üstünü/altını gösterir.

## Orijinal TÜİK ölçeğinde küme ortalamaları

Bu tablo yorum için orijinal birleşik veri setinden hesaplandı. GSYH TL, işsizlik ve istihdam %, eğitim yıl, yoğunluk kişi/km² birimindedir. Özellikle tek illik kümenin ortalaması o ilin değeridir.

| Küme | İl sayısı | GSYH (TL) | İşsizlik (%) | İstihdam (%) | Eğitim (yıl) | Yoğunluk (kişi/km²) |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 55 | 423,882.51 | 7.08 | 50.62 | 9.11 | 100.93 |
| 1 | 25 | 290,079.14 | 11.35 | 42.74 | 8.73 | 101.39 |
| 2 | 1 | 802,669.24 | 8.85 | 52.83 | 10.22 | 2,933.63 |

Küme profilleri ortalamaları gösterir; bir kümedeki bütün illerin aynı özelliklere sahip olduğu anlamına gelmez. İl bazında etiketler `iller_kmeans_k3.csv` dosyasındadır.
