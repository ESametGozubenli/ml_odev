# K-Means küme sayısı araştırması

Veri: `outputs/preprocessing/iller_olceklendirilmis.csv` (81 il, 5 özellik). `il_kodu` ve `il_adi` modele alınmadı. `random_state=42`, `n_init=20`.

| K | WCSS (inertia) | Silhouette | En küçük küme | En büyük küme | Küme büyüklükleri |
| ---: | ---: | ---: | ---: | ---: | --- |
| 2 | 282.935 | 0.3314 | 25 | 56 | [25, 56] |
| 3 | 195.755 | 0.3530 | 1 | 55 | [55, 25, 1] |
| 4 | 141.816 | 0.3182 | 1 | 42 | [42, 14, 24, 1] |
| 5 | 119.889 | 0.2835 | 1 | 37 | [37, 15, 1, 19, 9] |
| 6 | 103.022 | 0.2741 | 1 | 26 | [23, 9, 1, 26, 3, 19] |
| 7 | 91.544 | 0.2533 | 1 | 26 | [9, 19, 26, 1, 2, 13, 11] |
| 8 | 80.151 | 0.2556 | 1 | 25 | [20, 12, 13, 25, 1, 7, 1, 2] |
| 9 | 74.212 | 0.2354 | 1 | 18 | [5, 15, 18, 3, 1, 18, 7, 12, 2] |
| 10 | 66.987 | 0.2343 | 1 | 19 | [13, 14, 14, 1, 19, 2, 7, 8, 2, 1] |

En yüksek Silhouette: K=3, skor=0.3530. Bu tek başına nihai seçim değildir.

WCSS'nin azalma hızını Elbow grafiğinde, Silhouette değerlerini ikinci grafikte ve küme büyüklüklerini birlikte inceleyin. Dirsek belirsizse bunu karar gerekçesinde açıkça belirtin.

Bu araştırma tablosu K seçimi için hazırlanmıştır. Onaylanan K=3'ün il etiketleri ve yorumları `kmeans_nihai_raporu.md` içindedir.
