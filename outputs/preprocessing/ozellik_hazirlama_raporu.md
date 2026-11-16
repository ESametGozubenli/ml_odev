# Özellik seçimi ve ölçeklendirme notu

2024 TÜİK verisindeki 81 il için beş özellik kullanıldı: `kisi_basi_gsyh_tl`, `issizlik_orani`, `istihdam_orani`, `ortalama_egitim_suresi`, `nufus_yogunlugu`.

İşgücüne katılma oranı, istihdam oranıyla EDA'da yüksek Pearson korelasyonu (0,9708) gösterdiği için çıkarıldı. Böylece işgücü boyutunun kümelemede gereğinden fazla ağırlık taşıması azaltılmaya çalışıldı. Bu karar, en iyi modelin seçildiği anlamına gelmez.

Beş özelliğin tümüne `StandardScaler` uygulandı: her değerden o özelliğin 81 ildeki ortalaması çıkarıldı ve sonuç standart sapmaya bölündü. Keşifsel, denetimsiz kümeleme için ölçekleyici 81 ilin tamamına uyduruldu; train/test ayrımı yapılmadı. Negatif sonuçlar hata değildir, ortalamanın altındaki değerleri gösterir.

Kaynak veriler değiştirilmedi. Çıktıda 81 il, benzersiz il kodları ve aynı il sırası doğrulandı; eksik veya geçersiz değer oluşmadı. `il_kodu` ve `il_adi` yalnız tanımlama içindir, modele girdi olarak verilmemelidir.

Kaynak: `outputs/tuik_2024_81_il_birlesik.csv`. SHA-256: `f3011d92711a4664a25ba8879210c54bc20e6721aa810a893a568185ae679636`.
Ölçekleyici: `outputs/preprocessing/iller_olceklendirilmis_scaler.joblib`. Özellik sırası ve parametreler `donusum_bilgileri.json` içindedir. Yeni veri için aynı sırayla kaydedilmiş ölçekleyicinin `transform` yöntemi kullanılmalıdır; yeniden `fit` yapılmamalıdır.

## Parametreler

| Özellik | Ortalama | Standart sapma |
| --- | ---: | ---: |
| kisi_basi_gsyh_tl | 387261.55 | 121298.58 |
| issizlik_orani | 8.4189086 | 2.6503921 |
| istihdam_orani | 48.218788 | 4.8809311 |
| ortalama_egitim_suresi | 9.0067542 | 0.56913111 |
| nufus_yogunlugu | 136.04474 | 327.99426 |

## İlk beş il

| il_kodu | il_adi | kisi_basi_gsyh_tl | issizlik_orani | istihdam_orani | ortalama_egitim_suresi | nufus_yogunlugu |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Adana | -0.2991 | 1.1252 | -0.3320 | 0.5069 | 0.1016 |
| 2 | Adıyaman | -0.4926 | 1.0229 | -0.9100 | -0.4765 | -0.1654 |
| 3 | Afyonkarahisar | -0.4205 | -0.9364 | 0.7556 | -0.6450 | -0.2483 |
| 4 | Ağrı | -1.5878 | 1.7545 | -0.9581 | -2.6514 | -0.2796 |
| 5 | Amasya | -0.3371 | -0.5705 | 0.3910 | 0.0135 | -0.2301 |
