# Nihai DBSCAN raporu

## 1. Veri ve amaç

K-Means ile aynı `outputs/preprocessing/iller_olceklendirilmis.csv` dosyasındaki 81 ilin beş StandardScaler ile ölçekli özelliği kullanıldı: `kisi_basi_gsyh_tl`, `issizlik_orani`, `istihdam_orani`, `ortalama_egitim_suresi`, `nufus_yogunlugu`. `il_kodu` ve `il_adi` modele verilmedi. Amaç, birbirine yakın illerin yoğun bölgelerini ve bu bölgelerin dışında kalan illeri belirlemektir.

## 2. Algoritma nasıl çalışıyor?

DBSCAN burada beş boyutlu Öklid uzaklığını kullanır. `eps` bir ilin komşusu sayılabilecek en büyük uzaklığı belirler. `min_samples` ise bir ilin çekirdek nokta olabilmesi için kendisi dahil eps içinde bulunması gereken en az il sayısıdır. Çekirdeğe bağlanan fakat kendisi çekirdek olmayan iller sınır noktasıdır. Hiçbir kümeye bağlanamayan iller `-1` koduyla gürültü sayılır. Küme numaraları büyüklük veya gelişmişlik sırası değildir.

## 3. Parametreler nasıl bulundu?

Önce `min_samples=3, 4, 5, 7` değerleri denendi. Her birinde her ilin kendisi dahil ilgili sıradaki en yakın komşusuna uzaklığı hesaplandı ve küçükten büyüğe sıralanarak k-distance grafiği çizildi. Bu uzaklıkların %50, %60, %70, %80, %90 ve %95 yüzdelikleri eps adayı alındı: toplam 24 kombinasyon. Grafiklerde son illerin komşu uzaklıkları hızla yükseliyor; tek ve kesin bir kırılma noktası yok. Bu nedenle eps yalnız grafiğe bakılarak seçilmedi.

Her denemede küme sayısı, küme büyüklükleri, gürültü sayısı ve oranı hesaplandı. Gürültü dışında en az iki küme varsa Silhouette hesaplandı. `a`, bir ilin kendi kümesine ortalama uzaklığı; `b`, en yakın diğer kümeye ortalama uzaklığıdır. İl skoru `(b-a)/max(a,b)`; rapordaki değer yalnız **gürültü dışındaki** illerin ortalamasıdır. Tek küme varsa hesap yapılmadı.

## 4. Neden bu parametreler seçildi?

Onaylanan `min_samples=4`, `eps=1.128677` (%70 yüzdelik) çözümünde 2 küme (65, 4 il), 12 gürültü il (%14.8) ve gürültü hariç Silhouette 0.3801 oluştu.

`min_samples=4`, `eps=0.8955` çözümünün Silhouette değeri daha yüksek (0.4248), fakat 24 il (%29.6) gürültüye ayrılıyor; değerlendirme yalnız 57 ili kapsıyor. `min_samples=3`, `eps=1.1674` çözümünde 10 gürültü il ve 0.3609 Silhouette var. `min_samples=5` ve `7` denemelerinin hepsi tek küme verdi. Seçilen çözüm en yüksek skor peşinde çok sayıda ili dışarıda bırakmak yerine küme ve gürültü kapsamı arasında daha ölçülü bir denge kurduğu için kullanıcı onayıyla nihai sonuç yapıldı.

## 5. Sonuç ve il listeleri

Toplam 81 il: 69 il iki kümeye girdi, 12 il gürültü. Silhouette **0.3801**, yalnız bu 69 il üzerinden hesaplandı. Gürültü illeri değerin paydasında yoktur. Bu nedenle K-Means'in 81 il üzerinden hesaplanan skoru ile doğrudan eşdeğer değildir.

### Gürültü (-1) — 12 il

Ağrı, Ankara, Antalya, Hakkari, İstanbul, Kastamonu, Kocaeli, Şanlıurfa, Van, Batman, Ardahan, Iğdır.

### Küme 0 — 65 il

Adana, Adıyaman, Afyonkarahisar, Amasya, Artvin, Aydın, Balıkesir, Bilecik, Bingöl, Bitlis, Bolu, Burdur, Bursa, Çanakkale, Çankırı, Çorum, Denizli, Edirne, Elazığ, Erzincan, Erzurum, Eskişehir, Gaziantep, Giresun, Gümüşhane, Hatay, Isparta, Mersin, İzmir, Kars, Kayseri, Kırklareli, Kırşehir, Konya, Kütahya, Malatya, Manisa, Kahramanmaraş, Muğla, Nevşehir, Niğde, Ordu, Rize, Sakarya, Samsun, Sinop, Sivas, Tekirdağ, Tokat, Trabzon, Tunceli, Uşak, Yozgat, Zonguldak, Aksaray, Bayburt, Karaman, Kırıkkale, Şırnak, Bartın, Yalova, Karabük, Kilis, Osmaniye, Düzce.

Çekirdek: 56; sınır: 9.

### Küme 1 — 4 il

Diyarbakır, Mardin, Muş, Siirt.

Çekirdek: 1; sınır: 3.

## 6. Kümelerin orijinal TÜİK değerleriyle profili

Aşağıdaki ortalamalar ölçekli CSV'den değil, `outputs/tuik_2024_81_il_birlesik.csv` dosyasından hesaplandı. GSYH TL, işsizlik ve istihdam %, eğitim yıl, yoğunluk kişi/km² birimindedir. Gürültü satırı, gürültü sayılan illerin kendi ortalamasıdır; ayrı bir küme değildir.

| Grup | İl sayısı | GSYH (TL) | İşsizlik (%) | İstihdam (%) | Eğitim (yıl) | Yoğunluk (kişi/km²) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Gürültü (-1) | 12 | 426,142.21 | 10.21 | 48.30 | 8.98 | 369.70 |
| Küme 0 | 65 | 388,768.15 | 7.90 | 48.80 | 9.05 | 96.21 |
| Küme 1 | 4 | 246,137.27 | 11.53 | 38.50 | 8.33 | 82.46 |

## 7. Orijinal değerlerle yorum

Dört illik Küme 1'in ortalama kişi başına GSYH'si 246,137 TL; 65 illik Küme 0'da 388,768 TL. Aradaki fark yaklaşık 142,631 TL. Küme 1'de işsizlik ortalaması %11.53, Küme 0'da %7.90; fark 3.63 yüzde puan. İstihdam Küme 1'de %38.50, Küme 0'da %48.80; Küme 1 10.30 yüzde puan daha düşük. Ortalama eğitim süresi de Küme 1'de daha düşük (8.33 ve 9.05 yıl). Bu farklar kümelerin ortalama profilini anlatır; iller için nedensel bir açıklama veya gelişmişlik sıralaması değildir.

Gürültü illeri farklı uç özellikler nedeniyle aynı etiketi alabilir. Örneğin İstanbul'un yüksek nüfus yoğunluğu bu grubun yoğunluk ortalamasını yükseltir; gürültü satırı tek tip bir sosyoekonomik küme gibi yorumlanmamalıdır.

## 8. Sınırlamalar

Küme ortalamaları bir gruptaki her ilin aynı olduğunu göstermez. Gürültü etiketi veri hatası veya önemsiz il demek değildir; bu eps ve min_samples ile yeterli yoğunluk bağlantısı kurulamadığını gösterir. Özellikle dört illik küçük küme ve gürültü oranı, parametre seçimine duyarlılık işaretidir. K-Means ile küme sayısı ve iller karşılaştırılabilir; Silhouette skorları farklı il kapsamları nedeniyle doğrudan sıralama için kullanılmamalıdır.

İl bazında kümeler, gürültü ve çekirdek/sınır bilgisi `iller_dbscan.csv` dosyasında; sayısal profiller `kume_profilleri_orijinal.csv` dosyasındadır. Bu aşamada GMM, PCA veya t-SNE uygulanmadı.
