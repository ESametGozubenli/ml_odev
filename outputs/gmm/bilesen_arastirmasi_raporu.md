# GMM bileşen sayısı araştırması

## Veri ve yöntem

Girdi: `outputs/preprocessing/iller_olceklendirilmis.csv`; 81 il ve beş StandardScaler ile ölçeklendirilmiş özellik. İl kodu ve adı model girdisine alınmadı. 2–10 bileşen ayrı ayrı denendi. `random_state=42`, `n_init=10`, `max_iter=500`, `reg_covar=1e-06`, `covariance_type=full` kullanıldı. Her denemede yakınsama kontrol edildi.

GMM, her ili olasılıksal olarak Gauss bileşenleriyle açıklar. BIC ve AIC modelin veriye uyumunu ve karmaşıklığını birlikte değerlendirir; ikisinde de **daha düşük** değer tercih edilir. `logL` 81 ilin toplam log-olasılığı, `p` modelin serbest parametre sayısı, `n=81` olmak üzere `BIC=-2×logL+p×ln(n)` ve `AIC=-2×logL+2p` hesaplanır. BIC, ek parametreleri AIC'den daha güçlü cezalandırır. Silhouette, en yüksek üyelik olasılığına göre atanmış etiketlerin uzaklık temelli ayrışmasını ölçer; **daha yüksek** değer tercih edilir. Bu ölçüler farklı soruları yanıtladığı için sonuçları birlikte yorumlamak gerekir.

Silhouette, en az iki dolu küme olduğunda 81 ilin tamamı üzerinden hesaplandı. Tek veya çok küçük kümeler, yüksek skora rağmen yorumun kararsız olabileceğini gösterir. Buradaki `kume_buyuklukleri` değerleri yalnız araştırma içindir; nihai il etiketleri veya üyelik olasılıkları henüz kaydedilmedi.

## Deneme sonuçları

| Bileşen | BIC | AIC | Silhouette | Küme büyüklükleri | Tek illik küme |
| ---: | ---: | ---: | ---: | --- | ---: |
| 2 | 837.00 | 738.82 | 0.5050 | 76, 5 | 0 |
| 3 | 816.39 | 667.94 | 0.2964 | 50, 27, 4 | 0 |
| 4 | 872.45 | 673.71 | 0.2231 | 45, 26, 1, 9 | 1 |
| 5 | 882.29 | 633.27 | 0.1658 | 37, 19, 3, 9, 13 | 0 |
| 6 | 900.58 | 601.28 | 0.1191 | 2, 13, 14, 1, 42, 9 | 1 |
| 7 | 878.39 | 528.80 | 0.1900 | 15, 1, 2, 2, 44, 8, 9 | 1 |
| 8 | 952.06 | 552.18 | 0.1216 | 7, 11, 14, 1, 38, 1, 5, 4 | 2 |
| 9 | 941.58 | 491.42 | 0.1607 | 5, 10, 33, 3, 1, 12, 7, 8, 2 | 1 |
| 10 | 938.09 | 437.65 | 0.1415 | 10, 4, 1, 8, 13, 3, 31, 6, 1, 4 | 2 |

## İlk ölçüt özeti

En düşük BIC: 3 bileşen (816.39). En düşük AIC: 10 bileşen (437.65).
En yüksek Silhouette: 2 bileşen (0.5050).

## Değerlendirme ve öneri

İki bileşende Silhouette en yüksek (0.5050); ancak gruplar 76, 5 il olarak oldukça dengesiz. Bu çözüm ağırlıkla küçük bir ayrı grubu geri kalan illerden ayırır; daha ayrıntılı sosyoekonomik yapı vermez.

Üç bileşende BIC en düşük (816.39). Küme büyüklükleri 50, 27, 4; Silhouette 0.2964. Dört illik küçük grup ayrıca incelenmelidir, fakat tek illik grup yoktur. Dört bileşende BIC 872.45 düzeyine yükselir, Silhouette 0.2231 düzeyine iner ve tek illik küme oluşur.

AIC on bileşene kadar düşerek 437.65 değerine ulaşır. Buna karşılık on bileşende tek illik kümeler vardır ve Silhouette 0.1415 olur. 81 il için çok sayıda tam kovaryanslı bileşen, küçük gruplara aşırı uyum riski taşır; AIC'nin tek başına en düşük değerini nihai seçim saymıyoruz.

**Öneri: 3 bileşen.** BIC bu noktada en düşük; iki bileşene göre daha açıklayıcı bir ayrım sağlar ve dört ve üstündeki tek illik/çok küçük grup sorunları henüz ağırlaşmamıştır. Bunun bir ön değerlendirme olduğu, dört illik grubun orijinal verilerle ve üyelik olasılıklarıyla incelenmesi gerektiği unutulmamalıdır. Farklı `covariance_type` seçenekleri bu aşamada eklenmedi; mevcut tam kovaryanslı çözümde öneri için yeterli karşılaştırma vardır.

Üç bileşenli nihai GMM, bu araştırma ve kullanıcı onayından sonra `gmm_nihai_raporu.md` içinde ayrıca raporlanmıştır.
