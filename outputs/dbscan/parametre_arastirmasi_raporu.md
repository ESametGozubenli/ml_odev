# DBSCAN parametre araştırması

Girdi: `outputs/preprocessing/iller_olceklendirilmis.csv`; 81 il ve beş StandardScaler ile ölçekli özellik. İl kodu ve adı modele verilmedi. Uzaklık ölçüsü Öklid uzaklığıdır.

**eps**, bir noktanın komşusu sayılabilecek noktalar için en büyük uzaklıktır. **min_samples**, bir noktanın çekirdek nokta sayılması için eps çevresinde (kendisi dahil) bulunması gereken en az nokta sayısıdır. Kümeye bağlanamayan iller `-1` etiketiyle gürültü olarak işaretlenir.

Her `min_samples` değeri için illerin kendileri dahil ilgili sıradaki en yakın komşuya uzaklıkları sıralanıp k-distance grafiği çizildi. eps adayları bu uzaklıkların %50, %60, %70, %80, %90 ve %95 yüzdeliklerinden alındı. Yüzdelikler otomatik nihai karar değildir; grafikteki eğim, küme yapısı ve gürültü oranı birlikte yorumlanmalıdır.

Silhouette yalnızca **gürültü dışındaki** illerde en az iki küme oluştuğunda hesaplandı. Gürültü illeri bu skorun paydasında yer almaz. Bu skor K-Means veya gürültüyü dahil eden bir skorla doğrudan eşdeğer değildir. Tek küme oluştuğunda skor boş bırakıldı.

| min_samples | eps yüzdelik | eps | Küme | Gürültü | Gürültü % | Küme büyüklükleri | Silhouette (gürültü hariç) |
| ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| 3 | %50 | 0.7374 | 4 | 32 | 39.5 | 6, 27, 12, 4 | 0.2461 |
| 3 | %60 | 0.8320 | 4 | 22 | 27.2 | 46, 6, 3, 4 | 0.2244 |
| 3 | %70 | 0.9088 | 3 | 17 | 21.0 | 57, 3, 4 | 0.1476 |
| 3 | %80 | 1.1674 | 2 | 10 | 12.3 | 67, 4 | 0.3609 |
| 3 | %90 | 1.3851 | 1 | 7 | 8.6 | 74 | — |
| 3 | %95 | 1.9657 | 1 | 4 | 4.9 | 77 | — |
| 4 | %50 | 0.8580 | 3 | 26 | 32.1 | 6, 45, 4 | 0.3156 |
| 4 | %60 | 0.8955 | 2 | 24 | 29.6 | 53, 4 | 0.4248 |
| 4 | %70 | 1.1287 | 2 | 12 | 14.8 | 65, 4 | 0.3801 |
| 4 | %80 | 1.2428 | 1 | 9 | 11.1 | 72 | — |
| 4 | %90 | 1.5669 | 1 | 5 | 6.2 | 76 | — |
| 4 | %95 | 2.0419 | 1 | 4 | 4.9 | 77 | — |
| 5 | %50 | 0.9373 | 1 | 26 | 32.1 | 55 | — |
| 5 | %60 | 1.0289 | 1 | 23 | 28.4 | 58 | — |
| 5 | %70 | 1.2230 | 1 | 10 | 12.3 | 71 | — |
| 5 | %80 | 1.3430 | 1 | 9 | 11.1 | 72 | — |
| 5 | %90 | 1.5748 | 1 | 5 | 6.2 | 76 | — |
| 5 | %95 | 2.1940 | 1 | 4 | 4.9 | 77 | — |
| 7 | %50 | 1.0544 | 1 | 22 | 27.2 | 59 | — |
| 7 | %60 | 1.1364 | 1 | 19 | 23.5 | 62 | — |
| 7 | %70 | 1.3274 | 1 | 9 | 11.1 | 72 | — |
| 7 | %80 | 1.5244 | 1 | 7 | 8.6 | 74 | — |
| 7 | %90 | 1.8417 | 1 | 5 | 6.2 | 76 | — |
| 7 | %95 | 2.4557 | 1 | 3 | 3.7 | 78 | — |

## Ön değerlendirme

Öneri adayı `min_samples=4`, `eps=1.1287`: 2 küme (65, 4 il), 12 gürültü il (%14.8) ve gürültü hariç Silhouette 0.3801. Bu çözüm de dengesizdir; küçük küme yalnız dört il içerir.

`min_samples=4`, `eps=0.8955` denemesinde Silhouette daha yüksek (0.4248), ancak 24 il (%29.6) gürültü olur. Bu nedenle en yüksek skoru tek başına seçmek uygun değildir. min_samples=5 ve 7 denemelerinde tek küme oluştu. Grafikte kesin bir kırılma yok; son birkaç ilin uzaklığı hızla yükseliyor. Parametre önerisi bu sınırlamalarla kullanıcı onayına sunulmalıdır.

Bu aşamada nihai parametre, il bazında küme etiketi veya gürültü listesi üretilmedi. Parametre önerisi grafikler ve tablo incelendikten sonra kullanıcı onayına sunulacaktır.
