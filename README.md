# TÜİK 2024: 81 İlin Sosyoekonomik Kümelenmesi

Bu makine öğrenmesi dersi projesi, Türkiye'deki 81 ili 2024 TÜİK göstergelerine göre **K-Means, DBSCAN ve Gaussian Mixture Model (GMM)** ile inceler. Küme sayısı ve parametreler Elbow, Silhouette, k-distance, BIC ve AIC sonuçlarıyla değerlendirildi. PCA ve t-SNE yalnız görselleştirme için kullanıldı.

**İncelemeye başlamak için:** [teslim paketi ve proje açıklaması](teslim/proje_aciklamasi.md) · [ayrıntılı nihai rapor](teslim/nihai_rapor.md)

## Veri ve yöntem

Altı TÜİK Excel dosyasından hazırlanan birleşik 2024 tablosu `outputs/tuik_2024_81_il_birlesik.csv` içindedir. Kaynak dosyalar proje kökünde, veri kalite raporu `outputs/veri_kalite_raporu.md` dosyasındadır. Model girdisi olarak kişi başına GSYH, işsizlik, istihdam, ortalama eğitim süresi ve nüfus yoğunluğu kullanıldı. İşgücüne katılma oranı, istihdamla yüksek korelasyonu (Pearson 0,9708) nedeniyle model girdisinden çıkarıldı. Beş özelliğe StandardScaler uygulandı; il kodu ve adı modellere verilmedi.

| Algoritma | Seçilen ayar | Küme büyüklükleri | Gürültü | Silhouette kapsamı |
| --- | --- | --- | ---: | --- |
| K-Means | K=3 | 55, 25, 1 | 0 | 0,3530 · 81 il |
| DBSCAN | `eps=1,128677`, `min_samples=4` | 65, 4 | 12 | 0,3801 · 69 il |
| GMM | 3 bileşen, tam kovaryans | 50, 27, 4 | 0 | 0,2964 · 81 il |

DBSCAN Silhouette değerinde 12 gürültü ili dışarıda bırakıldı; bu değer diğer iki skorla doğrudan eşdeğer değildir. Küme numaraları gelişmişlik sırası değildir. Parametrelerin nasıl bulunduğu, tüm denemeler ve orijinal TÜİK ölçeğindeki küme profilleri [nihai raporda](teslim/nihai_rapor.md) açıklanır.

## Kümeleri gör

- [K-Means nokta grafiği](teslim/grafikler/kume_nokta_kmeans.png)
- [DBSCAN nokta grafiği](teslim/grafikler/kume_nokta_dbscan.png)
- [GMM nokta grafiği](teslim/grafikler/kume_nokta_gmm.png)

Bu grafiklerde her nokta bir ili gösterir. Nokta konumları beş özellikli verinin PCA ile iki boyuta yansıtılmış hâlidir; modeller beş boyutlu veride kurulmuştur. Diğer model seçimi ve görselleştirme grafikleri `teslim/grafikler/` içindedir.

## Klasörler ve yeniden üretim

- `scripts/`: EDA, ölçeklendirme, üç algoritma, görselleştirme ve rapor betikleri.
- `outputs/`: birleşik veri, ara tablolar, model sonuçları ve ayrıntılı aşama raporları.
- `teslim/`: okunacak açıklama, nihai rapor ve model grafiklerinin bir araya getirildiği paket.

Gerekli Python paketleri `requirements.txt` dosyasında listelenir. Mevcut birleşik CSV ile analizleri yeniden üretmek için proje kökünde sırasıyla aşağıdaki betikler çalıştırılabilir:

```powershell
python -m pip install -r requirements.txt
python scripts/02_eda_analizi.py
python scripts/03_ozellik_hazirlama.py
python scripts/04_kmeans.py
python scripts/05_dbscan.py
python scripts/06_gmm.py
python scripts/07_gorsellestirme.py
python scripts/09_kume_nokta_grafikleri.py
python scripts/08_nihai_rapor.py
```

Kaynak Excel dosyalarından birleşik CSV'nin ilk oluşturulma adımı bu betik dizisinde yer almaz; proje, doğrulanmış birleşik CSV'yi içerir. Betikler çalıştırıldığında ilgili `outputs/` dosyaları yeniden yazılır. Projede kullanılan veri ve yöntemlerin sınırları ayrıntılı raporda belirtilmiştir.
