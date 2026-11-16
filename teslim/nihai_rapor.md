# TÜİK 2024 — 81 ilin sosyoekonomik özelliklerine göre kümelenmesi

## 1. Projenin amacı

Amaç, Türkiye'deki 81 ili 2024 TÜİK sosyoekonomik göstergelerine göre benzerlikleri açısından incelemektir. K-Means, DBSCAN ve Gaussian Mixture Model (GMM) denetimsiz öğrenme yöntemleriyle uygulandı. Küme etiketleri önceden bilinen doğru sınıflar değildir; ortaya çıkan gruplar istatistiksel benzerlikleri gösterir. Küme numaraları başarı veya gelişmişlik sırası taşımaz.

## 2. Veri setinin tanıtımı

Altı TÜİK Excel dosyasındaki 2024 il değerleri birleştirildi:

- `İl bazında kişi başına gayrisafi yurt içi hasıla 2020-2024.xlsx`
- `İl düzeyinde işgücüne katılma oranı.xlsx`
- `İl düzeyinde işsizlik oranı.xlsx`
- `İl düzeyinde istihdam oranı.xlsx`
- `İllere göre ortalama eğitim süresi.xlsx`
- `İl ve cinsiyete göre il_ilçe merkezi, belde_köy nüfusu ve nüfus yoğunluğu.xlsx`

Birleşik tabloda 81 il, il kodu ve adı ile altı özellik bulunur. Model girdisi için beş özellik seçildi: kişi başına GSYH (TL), işsizlik (%), istihdam (%), ortalama eğitim süresi (yıl), nüfus yoğunluğu (kişi/km²). İl kodu ve adı hiçbir modelin sayısal girdisine dahil edilmedi. Kaynak ve sayfa ayrıntıları `veri_kalite_raporu.md` dosyasındadır.

## 3. Eksik veri kontrolü

Kaynak birleştirme raporu 81/81 il eşleşmesi, sıfır eşleşmeyen, tekrarlanan veya seçili sayısal alanda eksik kayıt bildirdi. Bu son rapor hazırlanırken birleşik veri, ölçekli veri ve üç algoritmanın il listesi yeniden il kodu ve adına göre kontrol edildi: hepsinde 81 benzersiz il var. Eksik veya sonlu olmayan model girdisi yok. Eksik değer doldurma veya gerçek veriyi değiştirme yapılmadı. Türkiye toplam satırı il olarak alınmadı.

## 4. Özellik seçimi ve ölçeklendirme

EDA'da işgücüne katılma ve istihdam oranlarının Pearson korelasyonu `0,9708` bulundu. Aynı işgücü boyutuna fazla ağırlık vermemek için katılma oranı model girdisinden çıkarıldı. Kalan beş özelliğe StandardScaler uygulandı: her özellikten 81 il ortalaması çıkarılıp standart sapmaya bölündü. Böylece TL, yüzde, yıl ve kişi/km² farklı büyüklüklerinin uzaklık hesaplarını yalnız birim nedeniyle belirlemesi azaltıldı. Ölçekli negatif değer hata değildir. Train/test ayrımı yapılmadı; denetimsiz keşif için 81 il birlikte kullanıldı.

**Sayılar nasıl ölçeklendi?** Her özellik için `z=(x−81 il ortalaması)/(81 il standart sapması)` uygulandı; standart sapma `ddof=0` ile hesaplandı. Örneğin kişi başına GSYH'nin ortalaması 387.261,55 TL, standart sapması 121.298,58 TL. İstanbul'un 802.669,24 TL değeri bu formülle 3,425 ölçekli değere dönüştü. Bu dönüşüm il koduna veya adına uygulanmadı.

EDA, GSYH ve nüfus yoğunluğunda sağa çarpıklık ve aykırı değer adayları gösterdi. Sonraki aşamalar için yalnız StandardScaler'lı beş özellikli B senaryosu seçildi. Bu nedenle uç illerin etkisi yorumda dikkate alınmalıdır. Hazırlık kararı ve parametreleri `preprocessing/ozellik_hazirlama_raporu.md` ve `preprocessing/donusum_bilgileri.json` içindedir.

## 5. K-Means ve küme sayısının belirlenmesi

**Arama ve sabit ayarlar.** Aynı beş boyutlu ölçekli veriyle K=2, 3, ..., 10 için dokuz ayrı model kuruldu. `random_state=42` rastgele başlangıçların tekrar üretilebilmesi için sabitlendi; bir arama sonucu değildir. `n_init=20`, her K için 20 farklı başlangıç denenip en düşük WCSS'li çözümün kullanılması demektir; bu sayı da önceden sabitlendi. İl kodu ve adı modele alınmadı.

**Ölçüler nasıl hesaplandı?** WCSS/inertia, her ilin ölçekli beş özellik vektörü `xᵢ` ile atandığı küme merkezinin `μ` arasındaki kareli Öklid uzaklıklarının toplamıdır: `Σᵢ ||xᵢ−μ_küme(i)||²`. Daha küçük WCSS, illerin merkezlerine daha yakın olduğunu gösterir; K büyüdükçe doğal olarak azalır. Elbow yöntemi, bu azalmanın belirgin biçimde yavaşladığı noktayı arar. Silhouette için her ilin kendi kümesindeki illere ortalama uzaklığı `a`, en yakın diğer kümeye ortalama uzaklığı `b` alınır; il skoru `(b−a)/max(a,b)`, 81 ilin ortalaması raporlanır. Tek elemanlı kümenin il skoru 0'dır. Skor yükseldikçe kümeler genellikle daha iyi ayrışır.

**K=2–10 sonuçları:**

| K | WCSS | Silhouette | Küme büyüklükleri |
| ---: | ---: | ---: | --- |
| 2 | 282,935 | 0,3314 | 25, 56 |
| 3 | 195,755 | 0,3530 | 55, 25, 1 |
| 4 | 141,816 | 0,3182 | 42, 14, 24, 1 |
| 5 | 119,889 | 0,2835 | 37, 15, 1, 19, 9 |
| 6 | 103,022 | 0,2741 | 23, 9, 1, 26, 3, 19 |
| 7 | 91,544 | 0,2533 | 9, 19, 26, 1, 2, 13, 11 |
| 8 | 80,151 | 0,2556 | 20, 12, 13, 25, 1, 7, 1, 2 |
| 9 | 74,212 | 0,2354 | 5, 15, 18, 3, 1, 18, 7, 12, 2 |
| 10 | 66,987 | 0,2343 | 13, 14, 14, 1, 19, 2, 7, 8, 2, 1 |

**Neden K=3?** K=2'den K=3'e geçerken WCSS 87,180 azaldı; K=3'ten K=4'e geçişte azalma 53,939, K=4'ten K=5'e geçişte 21,927 oldu. Elbow grafiğinde yavaşlama K=4 civarında görülür, ancak tek ve kesin bir dirsek yoktur. Silhouette K=3'te 0,3530 ile denenen değerler içinde en yüksek; K=2'de 0,3314, K=4'te 0,3182. K=3'te kümeler 55, 25 ve 1 il içerir. Bir ilin tek başına ayrılması açık bir sınırlamadır; K=2 daha dengelidir. En yüksek Silhouette, WCSS'deki düşüş ve sonuçların yorumlanabilirliği birlikte değerlendirilip bu ödünleşim kullanıcıya sunuldu; onayla K=3 seçildi. Bu seçim algoritmanın kesin olarak en iyi olduğunu göstermez.

**Küme 0 (55 il):** Afyonkarahisar, Amasya, Ankara, Antalya, Artvin, Aydın, Balıkesir, Bilecik, Bolu, Burdur, Bursa, Çanakkale, Çankırı, Çorum, Denizli, Edirne, Elazığ, Erzincan, Erzurum, Eskişehir, Giresun, Isparta, Mersin, İzmir, Kars, Kastamonu, Kayseri, Kırklareli, Kocaeli, Konya, Kütahya, Malatya, Manisa, Muğla, Nevşehir, Niğde, Ordu, Rize, Sakarya, Samsun, Sinop, Sivas, Tekirdağ, Tokat, Trabzon, Tunceli, Uşak, Yozgat, Aksaray, Bayburt, Karaman, Bartın, Ardahan, Yalova, Düzce.

**Küme 1 (25 il):** Adana, Adıyaman, Ağrı, Bingöl, Bitlis, Diyarbakır, Gaziantep, Gümüşhane, Hakkari, Hatay, Kırşehir, Kahramanmaraş, Mardin, Muş, Siirt, Şanlıurfa, Van, Zonguldak, Kırıkkale, Batman, Şırnak, Iğdır, Karabük, Kilis, Osmaniye.

**Küme 2 (1 il):** İstanbul.

Orijinal TÜİK ölçeğindeki küme ortalamaları:

| Grup | İl | GSYH (TL) | İşsizlik (%) | İstihdam (%) | Eğitim (yıl) | Yoğunluk (kişi/km²) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Küme 0 | 55 | 423.882,51 | 7,08 | 50,62 | 9,11 | 100,93 |
| Küme 1 | 25 | 290.079,14 | 11,35 | 42,74 | 8,73 | 101,39 |
| Küme 2 | 1 | 802.669,24 | 8,85 | 52,83 | 10,22 | 2.933,63 |

Küme 2 yalnız İstanbul'dur; yoğunluk ve GSYH bakımından uç konumu diğer illerden ayrılmasını açıklar. Tüm araştırma, Elbow ve Silhouette grafikleri ile merkezler `kmeans/` klasöründedir.

## 6. DBSCAN sonuçları

**Parametreler neyi belirliyor?** `eps`, ölçekli beş boyutlu uzayda iki ilin komşu sayılabileceği en büyük Öklid uzaklığıdır; birimi yoktur. `min_samples`, bir ilin çekirdek nokta olabilmesi için `eps` çevresinde kendisi dahil gereken en az il sayısıdır. Çekirdeğe bağlanan iller kümeye katılır; bağlanamayanlar `-1` gürültü etiketi alır. Gürültü veri hatası değildir.

**Adaylar nasıl üretildi?** `min_samples=3, 4, 5, 7` değerleri denendi. Her değerde her ilin kendisi dahil ilgili sıradaki en yakın komşuya uzaklığı hesaplandı; 81 uzaklık sıralanarak k-distance grafiği çizildi. Her eğrinin %50, %60, %70, %80, %90 ve %95 yüzdelikleri `eps` adayı yapıldı: 4×6=24 kombinasyon. Yüzdelikler matematiksel aday üretir; tek başına optimum kanıtı değildir. Grafiklerde son illerin uzaklığı hızla yükselir, ancak kesin tek kırılma görülmez. Seçilen `min_samples=4` için %70 yüzdelik `eps=1,128677` sonucunu verir. 81 sıralı uzaklıkta %70 konumu `0,70×(81−1)=56` sıfır tabanlı indekstir; yani küçükten 57. uzaklık bu eps değeridir.

**Her adayda ne ölçüldü?** Küme sayısı, her kümedeki il sayısı, gürültü sayısı/oranı ve uygun olduğunda Silhouette hesaplandı. Gürültü çıkarıldıktan sonra en az iki küme yoksa Silhouette tanımlı olmadığı için boş bırakıldı. Hesaplanan Silhouette yalnız gürültü dışındaki illerin ortalamasıdır.

**24 denemenin tamamı:**

| min_samples | eps yüzdeliği | eps | Küme | Büyüklükler | Gürültü | Gürültü % | Silhouette* |
| ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| 3 | %50 | 0,7374 | 4 | 6, 27, 12, 4 | 32 | 39,5 | 0,2461 |
| 3 | %60 | 0,8320 | 4 | 46, 6, 3, 4 | 22 | 27,2 | 0,2244 |
| 3 | %70 | 0,9088 | 3 | 57, 3, 4 | 17 | 21,0 | 0,1476 |
| 3 | %80 | 1,1674 | 2 | 67, 4 | 10 | 12,3 | 0,3609 |
| 3 | %90 | 1,3851 | 1 | 74 | 7 | 8,6 | — |
| 3 | %95 | 1,9657 | 1 | 77 | 4 | 4,9 | — |
| 4 | %50 | 0,8580 | 3 | 6, 45, 4 | 26 | 32,1 | 0,3156 |
| 4 | %60 | 0,8955 | 2 | 53, 4 | 24 | 29,6 | 0,4248 |
| 4 | %70 | 1,1287 | 2 | 65, 4 | 12 | 14,8 | 0,3801 |
| 4 | %80 | 1,2428 | 1 | 72 | 9 | 11,1 | — |
| 4 | %90 | 1,5669 | 1 | 76 | 5 | 6,2 | — |
| 4 | %95 | 2,0419 | 1 | 77 | 4 | 4,9 | — |
| 5 | %50 | 0,9373 | 1 | 55 | 26 | 32,1 | — |
| 5 | %60 | 1,0289 | 1 | 58 | 23 | 28,4 | — |
| 5 | %70 | 1,2230 | 1 | 71 | 10 | 12,3 | — |
| 5 | %80 | 1,3430 | 1 | 72 | 9 | 11,1 | — |
| 5 | %90 | 1,5748 | 1 | 76 | 5 | 6,2 | — |
| 5 | %95 | 2,1940 | 1 | 77 | 4 | 4,9 | — |
| 7 | %50 | 1,0544 | 1 | 59 | 22 | 27,2 | — |
| 7 | %60 | 1,1364 | 1 | 62 | 19 | 23,5 | — |
| 7 | %70 | 1,3274 | 1 | 72 | 9 | 11,1 | — |
| 7 | %80 | 1,5244 | 1 | 74 | 7 | 8,6 | — |
| 7 | %90 | 1,8417 | 1 | 76 | 5 | 6,2 | — |
| 7 | %95 | 2,4557 | 1 | 78 | 3 | 3,7 | — |

*Silhouette yalnız gürültü dışındaki illerde en az iki küme varsa hesaplandı; `—` tek küme oluştuğunu gösterir.

**Neden `min_samples=4`, `eps=1,128677`?** `min_samples=5` ve `7` denemelerinin tümü tek küme oluşturdu. `min_samples=3`, `eps=1,1674` çözümünde 67 ve 4 illik kümeler, 10 gürültü il ve 0,3609 Silhouette vardı. `min_samples=4`, `eps=0,8955` çözümünde Silhouette 0,4248 ile daha yüksek, fakat 24 il (%29,6) gürültü oldu; skor yalnız 57 ili kapsadı. Seçilen %70 yüzdelik çözüm 65 ve 4 illik kümeler ile 12 gürültü il (%14,8) verdi; Silhouette 0,3801 ve kapsam 69 il. Bir sonraki %80 yüzdelikte `eps=1,2428` tek küme oluştu, bu yüzden Silhouette hesaplanamadı. Daha sıkı dört noktalı çekirdek koşulu, makul gürültü oranı ve iki kümeli çözüm birlikte değerlendirilerek seçim kullanıcıya önerildi ve onaylandı. Küme 65/4 şeklinde dengesizdir; bu parametreler evrensel optimum olarak sunulmaz.

**Gürültü (-1) (12 il):** Ağrı, Ankara, Antalya, Hakkari, İstanbul, Kastamonu, Kocaeli, Şanlıurfa, Van, Batman, Ardahan, Iğdır.

**Küme 0 (65 il):** Adana, Adıyaman, Afyonkarahisar, Amasya, Artvin, Aydın, Balıkesir, Bilecik, Bingöl, Bitlis, Bolu, Burdur, Bursa, Çanakkale, Çankırı, Çorum, Denizli, Edirne, Elazığ, Erzincan, Erzurum, Eskişehir, Gaziantep, Giresun, Gümüşhane, Hatay, Isparta, Mersin, İzmir, Kars, Kayseri, Kırklareli, Kırşehir, Konya, Kütahya, Malatya, Manisa, Kahramanmaraş, Muğla, Nevşehir, Niğde, Ordu, Rize, Sakarya, Samsun, Sinop, Sivas, Tekirdağ, Tokat, Trabzon, Tunceli, Uşak, Yozgat, Zonguldak, Aksaray, Bayburt, Karaman, Kırıkkale, Şırnak, Bartın, Yalova, Karabük, Kilis, Osmaniye, Düzce.

**Küme 1 (4 il):** Diyarbakır, Mardin, Muş, Siirt.

Orijinal TÜİK ölçeğindeki grup ortalamaları (gürültü ayrı bir küme değildir):

| Grup | İl | GSYH (TL) | İşsizlik (%) | İstihdam (%) | Eğitim (yıl) | Yoğunluk (kişi/km²) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Gürültü (-1) | 12 | 426.142,21 | 10,21 | 48,30 | 8,98 | 369,70 |
| Küme 0 | 65 | 388.768,15 | 7,90 | 48,80 | 9,05 | 96,21 |
| Küme 1 | 4 | 246.137,27 | 11,53 | 38,50 | 8,33 | 82,46 |

Küme 1'deki dört ilin ortalama GSYH ve istihdamı geniş kümeye göre düşük, işsizliği yüksektir. Bu az sayılı kümede yorum parametre duyarlılığıyla birlikte yapılmalıdır. Gürültü listesi ve çekirdek/sınır bilgisi `dbscan/dbscan_nihai_raporu.md` içindedir.

## 7. GMM sonuçları

**GMM ne yapar?** Veriyi Gauss bileşenlerinin olasılıksal karışımıyla açıklar. Her il için her bileşene üyelik olasılığı hesaplanır; en yüksek olasılıklı bileşen rapordaki sert küme etiketi olur. K-Means'teki gibi yalnız bir merkez uzaklığına dayanmaz; her bileşenin yayılımını ve özellikler arası ortak değişimi de modelleyebilir. Uydurma sırasında EM yöntemi üyelik olasılıkları ile bileşen parametrelerini yineleyerek veri olasılığını artırır; yakınsama kontrol edilir.

**Arama ve sabit ayarlar.** 2–10 arasında dokuz bileşen sayısı denendi; seçilen hiperparametre bileşen sayısıdır. `covariance_type='full'` bütün bileşenlerde beş özelliğin kovaryansını serbest bırakan önceden belirlenmiş model biçimidir; bu projede farklı kovaryans türleri taranmadı. `random_state=42` tekrarlanabilirlik, `n_init=10` on başlangıçtan en iyi uyumu seçmek, `max_iter=500` yineleme üst sınırı, `reg_covar=0,000001` kovaryans hesabını sayısal olarak kararlı tutmak içindir. Bunlar bileşen aramasından çıkan optimum değerler değil, sabit çalışma ayarlarıdır. Dokuz modelin yakınsaması kontrol edildi.

**BIC ve AIC nasıl hesaplandı?** `logL`, modelin 81 ilin tamamı için toplam log-olasılığı, `p` serbest parametre sayısı, `n=81` olmak üzere `BIC=−2logL+p·ln(n)` ve `AIC=−2logL+2p`. İkisinde de küçük değer tercih edilir; BIC fazla karmaşıklığı AIC'den daha güçlü cezalandırır. Beş özellikli tam kovaryans modelinde `m` bileşen için `p=(m−1)+5m+15m`; üç bileşende `p=62`. Üç bileşenli modelin AIC'si 667,94; buradan toplam `logL≈-271,97` bulunur ve BIC 816,39 olur. Silhouette ise en yüksek olasılığa göre atanmış sert etiketlerin beş boyutlu uzaklık temelli ayrışmasını ölçer; GMM olasılıklarının kendisi üzerinden hesaplanmaz. Burada 81 ilin hepsi dahil edildi.

**2–10 bileşen sonuçları:**

| Bileşen | BIC | AIC | Silhouette | Küme büyüklükleri | Tek illik küme |
| ---: | ---: | ---: | ---: | --- | ---: |
| 2 | 837,00 | 738,82 | 0,5050 | 76, 5 | 0 |
| 3 | 816,39 | 667,94 | 0,2964 | 50, 27, 4 | 0 |
| 4 | 872,45 | 673,71 | 0,2231 | 45, 26, 1, 9 | 1 |
| 5 | 882,29 | 633,27 | 0,1658 | 37, 19, 3, 9, 13 | 0 |
| 6 | 900,58 | 601,28 | 0,1191 | 2, 13, 14, 1, 42, 9 | 1 |
| 7 | 878,39 | 528,80 | 0,1900 | 15, 1, 2, 2, 44, 8, 9 | 1 |
| 8 | 952,06 | 552,18 | 0,1216 | 7, 11, 14, 1, 38, 1, 5, 4 | 2 |
| 9 | 941,58 | 491,42 | 0,1607 | 5, 10, 33, 3, 1, 12, 7, 8, 2 | 1 |
| 10 | 938,09 | 437,65 | 0,1415 | 10, 4, 1, 8, 13, 3, 31, 6, 1, 4 | 2 |

**Neden üç bileşen?** İki bileşende Silhouette 0,5050 ile en yüksektir, fakat 76/5 illik ayrım çoğu ili tek büyük grupta toplar. Üç bileşende BIC 816,39 ile denenenlerin en düşüğüdür; kümeler 50, 27, 4 ilden oluşur ve tek illik küme yoktur. Silhouette 0,2964 olur. Dört bileşende BIC 872,45 değerine yükselir, Silhouette 0,2231 değerine iner ve bir tek illik küme oluşur. AIC on bileşende 437,65 ile en düşük olsa da iki tek illik küme ve çok küçük gruplar vardır; 81 il için 209 parametreli tam kovaryanslı modelin aşırı uyum riski yüksektir. BIC, Silhouette ve küme büyüklükleri birlikte yorumlanıp üç bileşen kullanıcıya önerildi ve onaylandı. Dört illik küme ayrıca incelenmelidir.

**Küme 0 (50 il):** Afyonkarahisar, Amasya, Antalya, Artvin, Balıkesir, Bilecik, Bingöl, Bolu, Burdur, Çanakkale, Çankırı, Çorum, Denizli, Edirne, Elazığ, Erzincan, Erzurum, Eskişehir, Giresun, Isparta, Mersin, Kars, Kastamonu, Kayseri, Kırklareli, Kırşehir, Konya, Kütahya, Malatya, Manisa, Muğla, Nevşehir, Niğde, Ordu, Rize, Samsun, Sinop, Sivas, Tekirdağ, Tokat, Tunceli, Uşak, Yozgat, Aksaray, Bayburt, Karaman, Şırnak, Bartın, Ardahan, Düzce.

**Küme 1 (27 il):** Adana, Adıyaman, Ağrı, Aydın, Bitlis, Bursa, Diyarbakır, Gaziantep, Gümüşhane, Hakkari, Hatay, Kahramanmaraş, Mardin, Muş, Sakarya, Siirt, Trabzon, Şanlıurfa, Van, Zonguldak, Kırıkkale, Batman, Iğdır, Yalova, Karabük, Kilis, Osmaniye.

**Küme 2 (4 il):** Ankara, İstanbul, İzmir, Kocaeli.

Orijinal TÜİK ölçeğindeki küme ortalamaları:

| Grup | İl | GSYH (TL) | İşsizlik (%) | İstihdam (%) | Eğitim (yıl) | Yoğunluk (kişi/km²) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Küme 0 | 50 | 398.051,10 | 6,77 | 50,16 | 9,00 | 64,29 |
| Küme 1 | 27 | 315.883,48 | 11,30 | 44,13 | 8,84 | 134,70 |
| Küme 2 | 4 | 734.194,14 | 9,56 | 51,62 | 10,23 | 1.042,12 |

Küme 2 Ankara, İstanbul, İzmir ve Kocaeli'ni içerir; ortalama GSYH ve eğitim süresi yüksektir. İstanbul'un çok yüksek yoğunluğu bu dört ilin yoğunluk ortalamasını etkiler. Üyelik olasılığı 0,80'in altında kalan Karabük, Samsun ve Ordu'nun atanması daha belirsizdir. Tüm olasılıklar ve yöntem ayrıntıları `gmm/` klasöründedir.

## 8. PCA ve t-SNE görselleştirmeleri

PCA için `n_components=2` değeri, illeri iki eksenli grafikte göstermek amacıyla **önceden seçildi**; küme sayısı araması değildir. Beş ölçekli özellikten en çok varyans taşıyan iki doğrusal eksen hesaplandı. İlk eksen %49,59, ikinci eksen %28,31; birlikte %77,90 varyans açıklar. Bu oran, ilk iki eksenin açıkladığı varyansların toplamıdır; kalan bilgi 2B grafikte görünmez.

t-SNE için `n_components=2`, `perplexity=20`, `random_state=42`, `init='pca'`, `learning_rate='auto'`, `max_iter=1000` kullanıldı. Perplexity 81 ilden küçük, yerel komşulukları göstermeye yönelik **görselleştirme ayarı** olarak seçildi; Elbow, BIC veya Silhouette ile optimize edilmedi. `random_state=42` konumları tekrar üretebilmek içindir. PCA ve t-SNE koordinatları kümeleme girdisi değildi; üç model aynı beş boyutlu ölçekli veride önceden kurulmuştu. t-SNE'deki eksen ve uzaklıklar nicel sosyoekonomik fark olarak okunamaz.

Her noktanın bir ili gösterdiği, küme renkleri ve büyüklükleri belirginleştirilmiş üç sonuç grafiği:

- [K-Means küme noktaları](grafikler/kume_nokta_kmeans.png)
- [DBSCAN küme noktaları](grafikler/kume_nokta_dbscan.png)
- [GMM küme noktaları](grafikler/kume_nokta_gmm.png)

| Algoritma | PCA | t-SNE |
| --- | --- | --- |
| K-Means | [PCA grafiği](grafikler/pca_kmeans.png) | [t-SNE grafiği](grafikler/tsne_kmeans.png) |
| DBSCAN | [PCA grafiği](grafikler/pca_dbscan.png) | [t-SNE grafiği](grafikler/tsne_dbscan.png) |
| GMM | [PCA grafiği](grafikler/pca_gmm.png) | [t-SNE grafiği](grafikler/tsne_gmm.png) |

PCA yükleri ve görsellerin yorumu `visualization/gorsellestirme_raporu.md` içindedir.

## 9. Algoritmaların karşılaştırılması

| Yöntem | Küme sayısı | Küme büyüklükleri | Gürültü | Silhouette | Hesaba giren il |
| --- | ---: | --- | ---: | ---: | ---: |
| K-Means | 3 | 55, 25, 1 | 0 | 0,3530 | 81 |
| DBSCAN | 2 | 65, 4 | 12 | 0,3801 | 69 |
| GMM | 3 | 50, 27, 4 | 0 | 0,2964 | 81 |

**Silhouette kapsamı:** K-Means ve GMM bütün 81 il, DBSCAN yalnız gürültü dışındaki 69 il üzerinden hesaplandı. Bu nedenle DBSCAN'ın 0,3801 değeri diğer iki skorla doğrudan eşdeğer değildir; tek başına algoritma üstünlüğü göstermez. Kümelerin sayısı ve büyüklüğü de yorum için gereklidir.

K-Means ve GMM etiketlerinin kesişimi (satır K-Means, sütun GMM):

| Sol etiket / sağ etiket | 0 | 1 | 2 |
| --- | ---: | ---: | ---: |
| 0 | 47 | 5 | 3 |
| 1 | 3 | 22 | 0 |
| 2 | 0 | 0 | 1 |

DBSCAN ve K-Means etiketlerinin kesişimi (DBSCAN -1 gürültüdür):

| Sol etiket / sağ etiket | 0 | 1 | 2 |
| --- | ---: | ---: | ---: |
| -1 | 5 | 6 | 1 |
| 0 | 50 | 15 | 0 |
| 1 | 0 | 4 | 0 |

DBSCAN ve GMM etiketlerinin kesişimi:

| Sol etiket / sağ etiket | 0 | 1 | 2 |
| --- | ---: | ---: | ---: |
| -1 | 3 | 6 | 3 |
| 0 | 47 | 17 | 1 |
| 1 | 0 | 4 | 0 |

Bu tablolar **küme numaralarını eşit anlamlı saymaz**; yalnız hangi illerin gruplarda birlikte bulunduğunu sayar. DBSCAN'ın dört illik küçük kümesi: Diyarbakır, Mardin, Muş, Siirt. K-Means bu illeri daha geniş düşük istihdam/yüksek işsizlik grubunda, GMM de kendi geniş grubunda toplar. GMM'nin Ankara, İstanbul, İzmir, Kocaeli grubu, K-Means'te İstanbul'un tek başına ayrılmasıyla farklılaşır; DBSCAN ise İstanbul'u gürültü sayar. Yöntemlerin merkez, yoğunluk ve olasılık varsayımları farklıdır.

## 10. Sonuç ve değerlendirme

81 il için veri birleştirme, kalite denetimi, EDA, beş özellikli ölçeklendirme, üç algoritma ve iki görselleştirme tamamlandı. Sonuçlar geniş il grupları yanında İstanbul ve bazı farklı profilli illerin ayrışabildiğini gösteriyor. K-Means'in tek illik İstanbul kümesi, DBSCAN'ın 12 gürültü ili ve GMM'nin küçük dört illik bileşeni yöntemlerin hassasiyetlerini gösterir.

Bu projede tek bir algoritmayı kesin 'en iyi' ilan etmek için yeterli gerekçe yoktur: Silhouette kapsamları farklıdır, küçük kümeler ve uç değerler sonucu etkiler, gerçek sınıf etiketleri yoktur. Kümelere açıklayıcı adlar yalnız orijinal ölçekli profillere bakılarak önerilebilir: örneğin GMM'deki dört illik grup için 'yüksek GSYH ve eğitimli büyük merkezler'; DBSCAN'ın dört illik grubu için 'düşük ortalama istihdam ve GSYH' gibi. Bu adlar yorum kolaylığı sağlar, iller için değer yargısı değildir.

Yeniden üretim için betikler `scripts/` klasöründedir. Kaynak Excel ve birleşik veri korunmuştur. Bu rapor, modellerin kaydedilmiş sonuçlarını kullanır; yeni kümeleme modeli eğitmez.

