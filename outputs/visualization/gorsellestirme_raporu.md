# PCA ve t-SNE ile iki boyutlu küme görselleştirmeleri

## Veri ve doğrulama

Girdi `outputs/preprocessing/iller_olceklendirilmis.csv`: 81 il ve beş StandardScaler ile ölçekli özellik. Kullanılan özellikler: `kisi_basi_gsyh_tl`, `issizlik_orani`, `istihdam_orani`, `ortalama_egitim_suresi`, `nufus_yogunlugu`. `il_kodu` ve `il_adi` boyut indirgeme girdisine alınmadı. K-Means, DBSCAN ve GMM çıktı dosyaları il kodu ve adına göre eşleştirildi; 81 benzersiz il ve eksik/sonlu değerler doğrulandı.

## PCA: ne, neden, nasıl?

PCA, beş ölçekli özelliğin en fazla varyansını taşıyan iki birbirine dik doğrusal ekseni buldu (`n_components=2`). Böylece beş boyutlu il konumları 2B çizildi. Bu işlem yalnız görselleştirme içindir; K-Means, DBSCAN ve GMM modelleri orijinal beş boyutlu ölçekli veri üzerinde kurulmuştu.

PCA 1 açıklanan varyans: **%49.59**; PCA 2: **%28.31**; toplam: **%77.90**. Kalan varyans 2B grafikte görünmez. Eksen yükleri `pca_yukleri.csv` dosyasında kayıtlıdır; işaretlerin yönü tek başına iyi/kötü anlamına gelmez.

PCA 1 yükleri: GSYH `+0,590`, istihdam `+0,460`, eğitim `+0,475`, nüfus yoğunluğu `+0,332`, işsizlik `-0,324`. Bu veride sağa doğru hareket genellikle daha yüksek GSYH, istihdam ve eğitimle, daha düşük işsizlikle ilişkilidir. PCA 2'de en belirgin yükler işsizlik `+0,648`, yoğunluk `+0,467` ve istihdam `-0,459` değerleridir. İşaretler PCA ekseninin keyfî yönüne bağlıdır; yorum yüklerin birbirine göre ilişkisi üzerinden yapılmalıdır.

## t-SNE: ne, neden, nasıl?

t-SNE aynı beş boyutlu veride yakın illerin 2B düzlemde yakın kalmasını amaçlayan doğrusal olmayan bir görselleştirmedir. `n_components=2`, `perplexity=20`, `random_state=42`, `init='pca'`, `learning_rate='auto'`, `max_iter=1000` kullanıldı. Perplexity 81 gözlemden küçüktür. Son KL divergence: **0.2673**; bu değer algoritmanın gömme ölçüsüdür, bir küme kalitesi puanı değildir. t-SNE eksenlerinin yönü ve ölçeği keyfîdir; uzak kümeler arasındaki mutlak mesafeyi veya küme alanını sosyoekonomik farkın nicel ölçüsü gibi yorumlamayın.

## Üç algoritmanın grafikleri

PCA ve t-SNE koordinatları **birer kez** hesaplandı; üç algoritmanın mevcut etiketleri ayrı grafiklerde renklendirildi. Aynı il her algoritmanın grafiklerinde aynı koordinattadır. Küme numaraları algoritmalar arasında eşdeğer değildir; aynı renk aynı sosyoekonomik küme anlamına gelmez. İstanbul, Ankara, İzmir ve Kocaeli okunabilirlik için etiketlendi. DBSCAN gürültü illeri siyah `X` ile gösterildi.

| Algoritma | Etiket dağılımı | PCA | t-SNE |
| --- | --- | --- | --- |
| K-Means | küme 0: 55, küme 1: 25, küme 2: 1 | `pca_kmeans.png` | `tsne_kmeans.png` |
| DBSCAN | gürültü: 12, küme 0: 65, küme 1: 4 | `pca_dbscan.png` | `tsne_dbscan.png` |
| GMM | küme 0: 50, küme 1: 27, küme 2: 4 | `pca_gmm.png` | `tsne_gmm.png` |

## Grafiklerde görülen örüntüler

PCA görünümünde K-Means'in 55 ve 25 illik iki büyük grubu özellikle PCA 1 boyunca ayrılıyor; İstanbul tek illik grup olarak üst sağ tarafta duruyor. GMM, İstanbul'u Ankara, İzmir ve Kocaeli ile dört illik bir grupta gösteriyor. DBSCAN'de gürültü illeri düzlemin tek bir köşesinde toplanmıyor; farklı konumlardaki iller yoğunluk bağlantısı kuramadığı için gürültü sayılmış olabilir. Bu, grafikten görülen bir örüntüdür; DBSCAN kararı beş boyutlu uzayda verildi.

t-SNE görünümünde bazı yakın il grupları daha belirgin görünüyor; Ankara, İstanbul, İzmir ve Kocaeli alt bölgede yakın konumlarda. t-SNE yerel komşuluklara ağırlık verdiği için bu düzlemde görülen küme aralıkları nicel uzaklık olarak yorumlanmamalıdır.


## Yorum sınırları ve sonraki adım

Bir 2B grafikte yakınlık görmek, beş boyutlu uzaydaki bütün farkların korunduğu anlamına gelmez. PCA'nın açıklamadığı varyans ve t-SNE'nin yerel komşuluk vurgusu dikkate alınmalıdır. Özellikle DBSCAN gürültüsü ile diğer algoritmaların küme etiketleri farklı tanımlara dayanır. Grafikler, önceden hesaplanmış kümeleri incelemek içindir; PCA ve t-SNE koordinatları model girdisi olarak kullanılmadı ve bu kod iki boyutlu koordinatlarda yeniden kümeleme yapmaz.

Koordinatlar `pca_koordinatlari.csv` ve `tsne_koordinatlari.csv` dosyalarında saklandı. Nihai algoritma karşılaştırması bu aşamada yapılmadı.
