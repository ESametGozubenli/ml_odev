# TÜİK 2024 — 81 İl Kümeleme Projesi

Bu klasör, makine öğrenmesi dersi ödevi için hazırlanan **inceleme paketidir**. Projenin amacı, Türkiye'deki 81 ilin 2024 yılı sosyoekonomik göstergelerindeki benzerlikleri K-Means, DBSCAN ve Gaussian Mixture Model (GMM) ile incelemektir. Kümeler önceden bilinen doğru sınıflar değildir; küme numaraları gelişmişlik sırası taşımaz.

## Dosyaları hangi sırayla incelemeli?

1. Bu açıklamayı okuyun.
2. [Nihai raporu](nihai_rapor.md) açın. Veri hazırlama, yöntem seçimi, il listeleri, orijinal TÜİK değerleriyle küme profilleri ve yöntemlerin karşılaştırması burada yer alır.
3. Aşağıdaki grafik bağlantılarını kullanın. Grafik dosyalarının tamamı `grafikler/` klasöründedir.

Bu paket rapor ve görselleri bir araya getirir. Kaynak Excel dosyaları, veriler, Python betikleri ve ayrıntılı aşama çıktıları proje klasörünün `outputs/` ve `scripts/` dizinlerinde korunmuştur.

## Ne yaptık?

| Aşama | Yapılan iş | Sonuç |
| --- | --- | --- |
| Veri hazırlama | Altı TÜİK Excel dosyasından 2024 il değerleri birleştirildi. | 81 il ve altı sayısal özellik; eksik/eşleşmeyen il yok. |
| EDA | Dağılımlar, korelasyonlar ve IQR aykırı değer adayları incelendi. | İşgücüne katılma ile istihdam korelasyonu 0,9708; GSYH ve yoğunluk sağa çarpık. |
| Özellik seçimi | İşgücüne katılma oranı çıkarıldı; kalan beş özelliğe StandardScaler uygulandı. | Bütün modeller aynı beş ölçekli özelliği kullandı. |
| K-Means | K=2–10 için WCSS/Elbow ve Silhouette incelendi; onayla K=3 seçildi. | Kümeler 55, 25 ve 1 il; İstanbul tek illik kümede. |
| DBSCAN | 24 `eps`/`min_samples` seçeneği ve k-distance grafikleri incelendi. | `eps=1,128677`, `min_samples=4`: 65 ve 4 illik kümeler, 12 gürültü il. |
| GMM | 2–10 bileşen için BIC, AIC, Silhouette ve küme büyüklükleri karşılaştırıldı. | BIC gerekçesiyle 3 bileşen: 50, 27 ve 4 illik kümeler. |
| Görselleştirme | PCA ve t-SNE koordinatları hesaplanıp üç yöntemin etiketleri ayrı çizildi. | Altı 2B küme grafiği; PCA iki ekseni toplam varyansın %77,90'ını açıklıyor. |
| Son değerlendirme | Küme profilleri orijinal TÜİK değerleriyle ve il bazında karşılaştırıldı. | [Nihai rapor](nihai_rapor.md) hazırlandı. |

Modelde kullanılan beş özellik: **kişi başına GSYH (TL), işsizlik oranı (%), istihdam oranı (%), ortalama eğitim süresi (yıl) ve nüfus yoğunluğu (kişi/km²)**. `il_kodu` ve `il_adi` yalnız illeri tanımlamak içindir; model girdisi değildir. Eksik değer doldurulmadı, gerçek veri değiştirilmedi. Denetimsiz keşif için 81 ilin tamamı kullanıldı; train/test ayrımı yapılmadı.

## Sonuçları nasıl okumalı?

| Yöntem | Küme büyüklükleri | Gürültü | Silhouette | Skor kapsamı |
| --- | --- | ---: | ---: | ---: |
| K-Means | 55, 25, 1 | 0 | 0,3530 | 81 il |
| DBSCAN | 65, 4 | 12 | 0,3801 | 69 il |
| GMM | 50, 27, 4 | 0 | 0,2964 | 81 il |

**DBSCAN Silhouette hesabında 12 gürültü il dışarıda bırakıldı.** Bu yüzden 0,3801 değerini K-Means ve GMM skorlarıyla doğrudan eşdeğer saymıyoruz. Ayrıca tek veya çok küçük kümeler ve uç iller sonuçları etkiliyor. Tek bir algoritma kesin olarak “en iyi” ilan edilmedi.

K-Means İstanbul'u tek başına ayırdı. GMM, İstanbul'u Ankara, İzmir ve Kocaeli ile dört illik bir gruba koydu. DBSCAN ise İstanbul'u gürültü olarak işaretledi; Diyarbakır, Mardin, Muş ve Siirt'i dört illik ayrı bir kümede topladı. Bu farklar yöntemlerin merkez, yoğunluk ve olasılık temelli yaklaşımlarından kaynaklanır. İllerin tam listeleri ve orijinal ölçekte küme ortalamaları nihai rapordadır.

## Grafikler

### Küme sonuçlarını gösteren nokta grafikleri

Bu üç grafikte **her nokta bir ili** gösterir. Renkler modelin oluşturduğu kümelerdir; DBSCAN'de siyah `X` gürültü ilidir. Noktaların konumu beş özellikli verinin PCA ile iki boyuta yansıtılmış hâlidir. Kümeleme kararları iki boyutlu noktalarla değil, beş özellikli ölçekli veriyle hesaplandı.

- [K-Means küme noktaları](grafikler/kume_nokta_kmeans.png) — İstanbul'un tek illik kümesi ayrı renkte.
- [DBSCAN küme noktaları](grafikler/kume_nokta_dbscan.png) — 65 ve 4 illik kümeler ile 12 gürültü il.
- [GMM küme noktaları](grafikler/kume_nokta_gmm.png) — 50, 27 ve 4 illik kümeler.

### Model seçimi

- [K-Means Elbow grafiği](grafikler/kmeans_elbow.png)
- [K-Means Silhouette grafiği](grafikler/kmeans_silhouette.png)
- [DBSCAN k-distance, min_samples=3](grafikler/dbscan_k_distance_min_samples_3.png)
- [DBSCAN k-distance, min_samples=4](grafikler/dbscan_k_distance_min_samples_4.png)
- [DBSCAN k-distance, min_samples=5](grafikler/dbscan_k_distance_min_samples_5.png)
- [DBSCAN k-distance, min_samples=7](grafikler/dbscan_k_distance_min_samples_7.png)
- [GMM BIC/AIC grafiği](grafikler/gmm_bic_aic.png)
- [GMM Silhouette grafiği](grafikler/gmm_silhouette.png)

### İllerin iki boyutlu görünümü

| Yöntem | PCA | t-SNE |
| --- | --- | --- |
| K-Means | [Grafik](grafikler/pca_kmeans.png) | [Grafik](grafikler/tsne_kmeans.png) |
| DBSCAN | [Grafik](grafikler/pca_dbscan.png) | [Grafik](grafikler/tsne_dbscan.png) |
| GMM | [Grafik](grafikler/pca_gmm.png) | [Grafik](grafikler/tsne_gmm.png) |

PCA/t-SNE koordinatları **kümeleme girdisi olarak kullanılmadı**. PCA görünümü beş boyutlu bilginin tamamını göstermez; t-SNE'deki eksen uzaklıkları doğrudan ekonomik fark miktarı değildir. DBSCAN grafiğinde siyah `X` işaretleri gürültü illerini gösterir. Aynı küme numarası veya renk, farklı algoritmalarda aynı anlama gelmez.
