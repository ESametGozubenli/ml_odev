"""TÜİK 81 il kümeleme projesinin doğrulanmış nihai raporunu oluşturur.

Çalıştırma: python scripts/08_nihai_rapor.py
Mevcut modellerin sonuçlarını okur; yeni model eğitmez veya verileri değiştirmez.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
ORIGINAL = OUTPUTS / "tuik_2024_81_il_birlesik.csv"
SCALED = OUTPUTS / "preprocessing" / "iller_olceklendirilmis.csv"
REPORT = OUTPUTS / "nihai_rapor.md"
LABEL_PATHS = {
    "K-Means": OUTPUTS / "kmeans" / "iller_kmeans_k3.csv",
    "DBSCAN": OUTPUTS / "dbscan" / "iller_dbscan.csv",
    "GMM": OUTPUTS / "gmm" / "iller_gmm.csv",
}
FEATURES = [
    "kisi_basi_gsyh_tl", "issizlik_orani", "istihdam_orani",
    "ortalama_egitim_suresi", "nufus_yogunlugu",
]
IDS = ["il_kodu", "il_adi"]
SOURCE_FILES = [
    "İl bazında kişi başına gayrisafi yurt içi hasıla 2020-2024.xlsx",
    "İl düzeyinde işgücüne katılma oranı.xlsx",
    "İl düzeyinde işsizlik oranı.xlsx",
    "İl düzeyinde istihdam oranı.xlsx",
    "İllere göre ortalama eğitim süresi.xlsx",
    "İl ve cinsiyete göre il_ilçe merkezi, belde_köy nüfusu ve nüfus yoğunluğu.xlsx",
]


def tr(value: float, digits: int = 2) -> str:
    """Sayıları Türkçe ondalık biçimiyle göster."""
    return f"{value:,.{digits}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def check_input() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, pd.Series]]:
    """Kaynak, ölçekli veri ve üç etiketi 81 il üzerinden eşleştir."""
    for path in [ORIGINAL, SCALED, *LABEL_PATHS.values()]:
        if not path.is_file():
            raise FileNotFoundError(f"Gerekli dosya bulunamadı: {path}")
    original = pd.read_csv(ORIGINAL, encoding="utf-8-sig")
    scaled = pd.read_csv(SCALED, encoding="utf-8-sig")
    if list(scaled.columns) != IDS + FEATURES:
        raise ValueError("Ölçekli veri beklenen beş özellikten oluşmuyor")
    if len(original) != 81 or len(scaled) != 81:
        raise ValueError("Orijinal veya ölçekli veride 81 il yok")
    if not original[IDS].equals(scaled[IDS]):
        raise ValueError("Orijinal ve ölçekli il kimlikleri/sırası uyuşmuyor")
    if original.isna().any().any() or scaled.isna().any().any():
        raise ValueError("Kaynak veya ölçekli veride eksik değer var")
    if original["il_kodu"].duplicated().any() or set(original["il_kodu"]) != set(range(1, 82)):
        raise ValueError("İl kodları benzersiz 1–81 kümesini oluşturmuyor")
    if not np.isfinite(original[FEATURES].to_numpy(dtype=float)).all() or not np.isfinite(
        scaled[FEATURES].to_numpy(dtype=float)
    ).all():
        raise ValueError("Sayısal özelliklerde geçersiz değer var")
    labels = {}
    for algorithm, path in LABEL_PATHS.items():
        frame = pd.read_csv(path, encoding="utf-8-sig")
        if not set(IDS + ["kume"]).issubset(frame.columns):
            raise ValueError(f"{algorithm}: küme veya il kimliği eksik")
        if len(frame) != 81 or frame["il_kodu"].duplicated().any():
            raise ValueError(f"{algorithm}: 81 benzersiz il yok")
        aligned = original[IDS].merge(frame[IDS + ["kume"]], on="il_kodu",
                                      how="left", validate="one_to_one",
                                      suffixes=("_kaynak", "_model"))
        if aligned["kume"].isna().any() or not aligned["il_adi_kaynak"].equals(
            aligned["il_adi_model"]
        ):
            raise ValueError(f"{algorithm}: il kodu/adı eşleşmiyor")
        if not pd.api.types.is_integer_dtype(aligned["kume"]):
            raise TypeError(f"{algorithm}: tamsayı olmayan küme etiketi")
        labels[algorithm] = aligned["kume"]
        counts = labels[algorithm].value_counts().sort_index().to_dict()
        print(f"{algorithm}: 81 il eşleşti; etiket dağılımı {counts}.")
    return original, scaled, labels


def check_metrics(scaled: pd.DataFrame, labels: dict[str, pd.Series]) -> dict:
    """Raporlanan Silhouette değerlerini aynı kapsamlarla yeniden doğrula."""
    values = scaled[FEATURES].to_numpy(dtype=float)
    kmeans = pd.read_csv(OUTPUTS / "kmeans" / "k_arastirmasi.csv", encoding="utf-8-sig")
    dbscan = pd.read_csv(OUTPUTS / "dbscan" / "parametre_arastirmasi.csv", encoding="utf-8-sig")
    gmm = pd.read_csv(OUTPUTS / "gmm" / "bilesen_arastirmasi.csv", encoding="utf-8-sig")
    km_row = kmeans.loc[kmeans["k"] == 3].iloc[0]
    db_row = dbscan.loc[(dbscan["min_samples"] == 4) &
                        np.isclose(dbscan["eps"], 1.1286768001156766)].iloc[0]
    gm_row = gmm.loc[gmm["bilesen_sayisi"] == 3].iloc[0]
    db_mask = labels["DBSCAN"].to_numpy() != -1
    if int(db_mask.sum()) != 69:
        raise ValueError("DBSCAN için 69 küme içi il bekleniyordu")
    calculated = {
        "K-Means": float(silhouette_score(values, labels["K-Means"])),
        "DBSCAN": float(silhouette_score(values[db_mask], labels["DBSCAN"][db_mask])),
        "GMM": float(silhouette_score(values, labels["GMM"])),
    }
    expected = {
        "K-Means": float(km_row["silhouette_score"]),
        "DBSCAN": float(db_row["silhouette_gurultu_haric"]),
        "GMM": float(gm_row["silhouette_score"]),
    }
    for name in calculated:
        if not np.isclose(calculated[name], expected[name], atol=1e-9):
            raise ValueError(f"{name}: Silhouette kaydedilen değerle uyuşmuyor")
        print(f"{name} Silhouette doğrulandı: {calculated[name]:.4f}; "
              f"kapsam {69 if name == 'DBSCAN' else 81} il.")
    return {
        "scores": calculated,
        "kmeans": km_row, "dbscan": db_row, "gmm": gm_row,
        "kmeans_search": kmeans, "dbscan_search": dbscan, "gmm_search": gmm,
    }


def cluster_profiles(original: pd.DataFrame,
                     labels: dict[str, pd.Series]) -> dict[str, pd.DataFrame]:
    """Küme ortalamalarını yalnız orijinal TÜİK ölçeğinde hesapla."""
    profiles = {}
    for algorithm, assignments in labels.items():
        frame = original[FEATURES].copy()
        frame["kume"] = assignments.to_numpy()
        means = frame.groupby("kume", sort=True)[FEATURES].mean().reset_index()
        means.insert(1, "il_sayisi", frame.groupby("kume", sort=True).size().to_numpy())
        profiles[algorithm] = means
    return profiles


def profile_table(profile: pd.DataFrame) -> list[str]:
    lines = [
        "| Grup | İl | GSYH (TL) | İşsizlik (%) | İstihdam (%) | Eğitim (yıl) | Yoğunluk (kişi/km²) |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in profile.itertuples(index=False, name=None):
        group = "Gürültü (-1)" if row[0] == -1 else f"Küme {row[0]}"
        lines.append(f"| {group} | {row[1]} | "
                     + " | ".join(tr(float(value)) for value in row[2:]) + " |")
    return lines


def city_sections(original: pd.DataFrame, assignments: pd.Series) -> list[str]:
    lines = []
    for number in sorted(assignments.unique()):
        mask = assignments.to_numpy() == number
        title = "Gürültü (-1)" if number == -1 else f"Küme {number}"
        cities = original.loc[mask, "il_adi"].tolist()
        lines += [f"**{title} ({len(cities)} il):** " + ", ".join(cities) + ".", ""]
    return lines


def overlap_table(left: pd.Series, right: pd.Series) -> list[str]:
    """Küme numaralarını eşdeğer saymadan kesişim sayılarını göster."""
    table = pd.crosstab(left.to_numpy(), right.to_numpy())
    cols = list(table.columns)
    lines = ["| Sol etiket / sağ etiket | "
             + " | ".join(str(col) for col in cols) + " |",
             "| --- | " + " | ".join("---:" for _ in cols) + " |"]
    for index, row in table.iterrows():
        lines.append(f"| {index} | " + " | ".join(str(int(v)) for v in row) + " |")
    return lines


def kmeans_search_table(search: pd.DataFrame) -> list[str]:
    """K=2–10 ölçümlerinin tamamını rapora aktar."""
    lines = [
        "| K | WCSS | Silhouette | Küme büyüklükleri |",
        "| ---: | ---: | ---: | --- |",
    ]
    for _, row in search.iterrows():
        k = int(row["k"])
        sizes = [int(row[f"kume_{index}_il_sayisi"]) for index in range(k)]
        lines.append(f"| {k} | {tr(float(row['wcss_inertia']), 3)} | "
                     f"{tr(float(row['silhouette_score']), 4)} | "
                     f"{', '.join(map(str, sizes))} |")
    return lines


def dbscan_search_table(search: pd.DataFrame) -> list[str]:
    """24 eps/min_samples denemesini gürültü kapsamıyla göster."""
    lines = [
        "| min_samples | eps yüzdeliği | eps | Küme | Büyüklükler | Gürültü | Gürültü % | Silhouette* |",
        "| ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: |",
    ]
    for _, row in search.iterrows():
        score = ("—" if pd.isna(row["silhouette_gurultu_haric"])
                 else tr(float(row["silhouette_gurultu_haric"]), 4))
        sizes = ("—" if pd.isna(row["kume_buyuklukleri"])
                 else str(row["kume_buyuklukleri"]))
        lines.append(f"| {int(row['min_samples'])} | %{int(row['eps_yuzdelik'])} | "
                     f"{tr(float(row['eps']), 4)} | {int(row['kume_sayisi'])} | "
                     f"{sizes} | {int(row['gurultu_il_sayisi'])} | "
                     f"{tr(float(row['gurultu_orani_yuzde']), 1)} | {score} |")
    lines += ["", "*Silhouette yalnız gürültü dışındaki illerde en az iki "
              "küme varsa hesaplandı; `—` tek küme oluştuğunu gösterir.", ""]
    return lines


def gmm_search_table(search: pd.DataFrame) -> list[str]:
    """2–10 bileşenin BIC, AIC, Silhouette ve küme boyutlarını göster."""
    lines = [
        "| Bileşen | BIC | AIC | Silhouette | Küme büyüklükleri | Tek illik küme |",
        "| ---: | ---: | ---: | ---: | --- | ---: |",
    ]
    for _, row in search.iterrows():
        score = ("—" if pd.isna(row["silhouette_score"])
                 else tr(float(row["silhouette_score"]), 4))
        lines.append(f"| {int(row['bilesen_sayisi'])} | {tr(float(row['bic']))} | "
                     f"{tr(float(row['aic']))} | {score} | "
                     f"{row['kume_buyuklukleri']} | "
                     f"{int(row['tek_illi_kume_sayisi'])} |")
    return lines


def build_report(original: pd.DataFrame, scaled: pd.DataFrame,
                 labels: dict[str, pd.Series], metrics: dict,
                 profiles: dict[str, pd.DataFrame]) -> str:
    """Ödevin on bölümünü kaynaklarla ve doğrulanmış sayılarla doldur."""
    scores = metrics["scores"]
    km = metrics["kmeans"]
    db = metrics["dbscan"]
    gm = metrics["gmm"]
    km_search = metrics["kmeans_search"]
    db_search = metrics["dbscan_search"]
    gm_search = metrics["gmm_search"]
    km2 = km_search.loc[km_search["k"] == 2].iloc[0]
    km4 = km_search.loc[km_search["k"] == 4].iloc[0]
    km5 = km_search.loc[km_search["k"] == 5].iloc[0]
    db_high = db_search.loc[(db_search["min_samples"] == 4) &
                            (db_search["eps_yuzdelik"] == 60)].iloc[0]
    db_low = db_search.loc[(db_search["min_samples"] == 3) &
                           (db_search["eps_yuzdelik"] == 80)].iloc[0]
    db_one = db_search.loc[(db_search["min_samples"] == 4) &
                           (db_search["eps_yuzdelik"] == 80)].iloc[0]
    gm2 = gm_search.loc[gm_search["bilesen_sayisi"] == 2].iloc[0]
    gm4 = gm_search.loc[gm_search["bilesen_sayisi"] == 4].iloc[0]
    gm10 = gm_search.loc[gm_search["bilesen_sayisi"] == 10].iloc[0]
    source_means = original[FEATURES].mean()
    source_stds = original[FEATURES].std(ddof=0)
    istanbul_raw = original.loc[original["il_adi"] == "İstanbul"].iloc[0]
    istanbul_scaled = scaled.loc[scaled["il_adi"] == "İstanbul"].iloc[0]
    ratios = PCA(n_components=2).fit(scaled[FEATURES]).explained_variance_ratio_
    metro = ["Ankara", "İstanbul", "İzmir", "Kocaeli"]
    db_small = original.loc[labels["DBSCAN"].to_numpy() == 1, "il_adi"].tolist()
    lines = [
        "# TÜİK 2024 — 81 ilin sosyoekonomik özelliklerine göre kümelenmesi", "",
        "## 1. Projenin amacı", "",
        "Amaç, Türkiye'deki 81 ili 2024 TÜİK sosyoekonomik göstergelerine "
        "göre benzerlikleri açısından incelemektir. K-Means, DBSCAN ve "
        "Gaussian Mixture Model (GMM) denetimsiz öğrenme yöntemleriyle "
        "uygulandı. Küme etiketleri önceden bilinen doğru sınıflar "
        "değildir; ortaya çıkan gruplar istatistiksel benzerlikleri "
        "gösterir. Küme numaraları başarı veya gelişmişlik sırası taşımaz.", "",
        "## 2. Veri setinin tanıtımı", "",
        "Altı TÜİK Excel dosyasındaki 2024 il değerleri birleştirildi:", "",
    ]
    lines += [f"- `{name}`" for name in SOURCE_FILES]
    lines += [
        "", "Birleşik tabloda 81 il, il kodu ve adı ile altı özellik bulunur. "
        "Model girdisi için beş özellik seçildi: kişi başına GSYH (TL), "
        "işsizlik (%), istihdam (%), ortalama eğitim süresi (yıl), "
        "nüfus yoğunluğu (kişi/km²). İl kodu ve adı hiçbir modelin "
        "sayısal girdisine dahil edilmedi. Kaynak ve sayfa ayrıntıları "
        "`veri_kalite_raporu.md` dosyasındadır.", "",
        "## 3. Eksik veri kontrolü", "",
        "Kaynak birleştirme raporu 81/81 il eşleşmesi, sıfır eşleşmeyen, "
        "tekrarlanan veya seçili sayısal alanda eksik kayıt bildirdi. "
        "Bu son rapor hazırlanırken birleşik veri, ölçekli veri ve üç "
        "algoritmanın il listesi yeniden il kodu ve adına göre kontrol "
        "edildi: hepsinde 81 benzersiz il var. Eksik veya sonlu olmayan "
        "model girdisi yok. Eksik değer doldurma veya gerçek veriyi "
        "değiştirme yapılmadı. Türkiye toplam satırı il olarak alınmadı.", "",
        "## 4. Özellik seçimi ve ölçeklendirme", "",
        "EDA'da işgücüne katılma ve istihdam oranlarının Pearson "
        "korelasyonu `0,9708` bulundu. Aynı işgücü boyutuna fazla "
        "ağırlık vermemek için katılma oranı model girdisinden çıkarıldı. "
        "Kalan beş özelliğe StandardScaler uygulandı: her özellikten "
        "81 il ortalaması çıkarılıp standart sapmaya bölündü. Böylece "
        "TL, yüzde, yıl ve kişi/km² farklı büyüklüklerinin uzaklık "
        "hesaplarını yalnız birim nedeniyle belirlemesi azaltıldı. "
        "Ölçekli negatif değer hata değildir. Train/test ayrımı "
        "yapılmadı; denetimsiz keşif için 81 il birlikte kullanıldı.", "",
        "**Sayılar nasıl ölçeklendi?** Her özellik için "
        "`z=(x−81 il ortalaması)/(81 il standart sapması)` "
        "uygulandı; standart sapma `ddof=0` ile hesaplandı. Örneğin "
        "kişi başına GSYH'nin ortalaması "
        f"{tr(float(source_means['kisi_basi_gsyh_tl']))} TL, "
        "standart sapması "
        f"{tr(float(source_stds['kisi_basi_gsyh_tl']))} TL. "
        f"İstanbul'un {tr(float(istanbul_raw['kisi_basi_gsyh_tl']))} TL "
        "değeri bu formülle "
        f"{tr(float(istanbul_scaled['kisi_basi_gsyh_tl']), 3)} "
        "ölçekli değere dönüştü. Bu dönüşüm il koduna veya adına "
        "uygulanmadı.", "",
        "EDA, GSYH ve nüfus yoğunluğunda sağa çarpıklık ve aykırı "
        "değer adayları gösterdi. Sonraki aşamalar için yalnız "
        "StandardScaler'lı beş özellikli B senaryosu seçildi. Bu "
        "nedenle uç illerin etkisi yorumda dikkate alınmalıdır. "
        "Hazırlık kararı ve parametreleri `preprocessing/ozellik_hazirlama_raporu.md` "
        "ve `preprocessing/donusum_bilgileri.json` içindedir.", "",
        "## 5. K-Means ve küme sayısının belirlenmesi", "",
        "**Arama ve sabit ayarlar.** Aynı beş boyutlu ölçekli veriyle "
        "K=2, 3, ..., 10 için dokuz ayrı model kuruldu. "
        "`random_state=42` rastgele başlangıçların tekrar üretilebilmesi "
        "için sabitlendi; bir arama sonucu değildir. `n_init=20`, her K "
        "için 20 farklı başlangıç denenip en düşük WCSS'li çözümün "
        "kullanılması demektir; bu sayı da önceden sabitlendi. "
        "İl kodu ve adı modele alınmadı.", "",
        "**Ölçüler nasıl hesaplandı?** WCSS/inertia, her ilin ölçekli "
        "beş özellik vektörü `xᵢ` ile atandığı küme merkezinin `μ` "
        "arasındaki kareli Öklid uzaklıklarının toplamıdır: "
        "`Σᵢ ||xᵢ−μ_küme(i)||²`. Daha küçük WCSS, illerin merkezlerine "
        "daha yakın olduğunu gösterir; K büyüdükçe doğal olarak azalır. "
        "Elbow yöntemi, bu azalmanın belirgin biçimde yavaşladığı "
        "noktayı arar. Silhouette için her ilin kendi kümesindeki "
        "illere ortalama uzaklığı `a`, en yakın diğer kümeye ortalama "
        "uzaklığı `b` alınır; il skoru `(b−a)/max(a,b)`, 81 ilin "
        "ortalaması raporlanır. Tek elemanlı kümenin il skoru 0'dır. "
        "Skor yükseldikçe kümeler genellikle daha iyi ayrışır.", "",
        "**K=2–10 sonuçları:**", "",
    ]
    lines += kmeans_search_table(km_search)
    lines += [
        "", "**Neden K=3?** K=2'den K=3'e geçerken WCSS "
        f"{tr(float(km2['wcss_inertia'] - km['wcss_inertia']), 3)} "
        "azaldı; K=3'ten K=4'e geçişte azalma "
        f"{tr(float(km['wcss_inertia'] - km4['wcss_inertia']), 3)}, "
        "K=4'ten K=5'e geçişte "
        f"{tr(float(km4['wcss_inertia'] - km5['wcss_inertia']), 3)} oldu. "
        "Elbow grafiğinde yavaşlama K=4 civarında görülür, ancak "
        "tek ve kesin bir dirsek yoktur. Silhouette K=3'te "
        f"{tr(scores['K-Means'], 4)} ile denenen değerler içinde en "
        f"yüksek; K=2'de {tr(float(km2['silhouette_score']), 4)}, "
        f"K=4'te {tr(float(km4['silhouette_score']), 4)}. "
        "K=3'te kümeler 55, 25 ve 1 il içerir. Bir ilin tek başına "
        "ayrılması açık bir sınırlamadır; K=2 daha dengelidir. "
        "En yüksek Silhouette, WCSS'deki düşüş ve sonuçların "
        "yorumlanabilirliği birlikte değerlendirilip bu ödünleşim "
        "kullanıcıya sunuldu; onayla K=3 seçildi. "
        "Bu seçim algoritmanın kesin olarak en iyi olduğunu göstermez.", "",
    ]
    lines += city_sections(original, labels["K-Means"])
    lines += ["Orijinal TÜİK ölçeğindeki küme ortalamaları:", "",
              *profile_table(profiles["K-Means"]), "",
              "Küme 2 yalnız İstanbul'dur; yoğunluk ve GSYH bakımından "
              "uç konumu diğer illerden ayrılmasını açıklar. "
              "Tüm araştırma, Elbow ve Silhouette grafikleri ile merkezler "
              "`kmeans/` klasöründedir.", "",
              "## 6. DBSCAN sonuçları", "",
              "**Parametreler neyi belirliyor?** `eps`, ölçekli beş "
              "boyutlu uzayda iki ilin komşu sayılabileceği en büyük "
              "Öklid uzaklığıdır; birimi yoktur. `min_samples`, bir "
              "ilin çekirdek nokta olabilmesi için `eps` çevresinde "
              "kendisi dahil gereken en az il sayısıdır. Çekirdeğe "
              "bağlanan iller kümeye katılır; bağlanamayanlar `-1` "
              "gürültü etiketi alır. Gürültü veri hatası değildir.", "",
              "**Adaylar nasıl üretildi?** `min_samples=3, 4, 5, 7` "
              "değerleri denendi. Her değerde her ilin kendisi dahil "
              "ilgili sıradaki en yakın komşuya uzaklığı hesaplandı; "
              "81 uzaklık sıralanarak k-distance grafiği çizildi. "
              "Her eğrinin %50, %60, %70, %80, %90 ve %95 "
              "yüzdelikleri `eps` adayı yapıldı: 4×6=24 kombinasyon. "
              "Yüzdelikler matematiksel aday üretir; tek başına optimum "
              "kanıtı değildir. Grafiklerde son illerin uzaklığı hızla "
              "yükselir, ancak kesin tek kırılma görülmez. "
              f"Seçilen `min_samples=4` için %70 yüzdelik "
              f"`eps={tr(float(db['eps']), 6)}` sonucunu verir. "
              "81 sıralı uzaklıkta %70 konumu `0,70×(81−1)=56` "
              "sıfır tabanlı indekstir; yani küçükten 57. uzaklık "
              "bu eps değeridir.", "",
              "**Her adayda ne ölçüldü?** Küme sayısı, her kümedeki il "
              "sayısı, gürültü sayısı/oranı ve uygun olduğunda "
              "Silhouette hesaplandı. Gürültü çıkarıldıktan sonra en "
              "az iki küme yoksa Silhouette tanımlı olmadığı için boş "
              "bırakıldı. Hesaplanan Silhouette yalnız gürültü "
              "dışındaki illerin ortalamasıdır.", "",
              "**24 denemenin tamamı:**", ""]
    lines += dbscan_search_table(db_search)
    lines += [
        "**Neden `min_samples=4`, `eps=1,128677`?** "
        "`min_samples=5` ve `7` denemelerinin tümü tek küme "
        "oluşturdu. `min_samples=3`, "
        f"`eps={tr(float(db_low['eps']), 4)}` çözümünde 67 ve 4 "
        f"illik kümeler, {int(db_low['gurultu_il_sayisi'])} gürültü il "
        f"ve {tr(float(db_low['silhouette_gurultu_haric']), 4)} "
        "Silhouette vardı. `min_samples=4`, "
        f"`eps={tr(float(db_high['eps']), 4)}` çözümünde Silhouette "
        f"{tr(float(db_high['silhouette_gurultu_haric']), 4)} ile "
        "daha yüksek, fakat 24 il (%29,6) gürültü oldu; skor yalnız "
        "57 ili kapsadı. Seçilen %70 yüzdelik çözüm 65 ve 4 "
        f"illik kümeler ile 12 gürültü il (%14,8) verdi; "
        f"Silhouette {tr(scores['DBSCAN'], 4)} ve kapsam 69 il. "
        f"Bir sonraki %80 yüzdelikte `eps={tr(float(db_one['eps']), 4)}` "
        "tek küme oluştu, bu yüzden Silhouette hesaplanamadı. "
        "Daha sıkı dört noktalı çekirdek koşulu, makul gürültü "
        "oranı ve iki kümeli çözüm birlikte değerlendirilerek "
        "seçim kullanıcıya önerildi ve onaylandı. Küme 65/4 "
        "şeklinde dengesizdir; bu parametreler evrensel optimum "
        "olarak sunulmaz.", "",
    ]
    lines += city_sections(original, labels["DBSCAN"])
    lines += ["Orijinal TÜİK ölçeğindeki grup ortalamaları (gürültü ayrı bir küme değildir):", "",
              *profile_table(profiles["DBSCAN"]), "",
              "Küme 1'deki dört ilin ortalama GSYH ve istihdamı geniş "
              "kümeye göre düşük, işsizliği yüksektir. Bu az sayılı "
              "kümede yorum parametre duyarlılığıyla birlikte yapılmalıdır. "
              "Gürültü listesi ve çekirdek/sınır bilgisi "
              "`dbscan/dbscan_nihai_raporu.md` içindedir.", "",
              "## 7. GMM sonuçları", "",
              "**GMM ne yapar?** Veriyi Gauss bileşenlerinin olasılıksal "
              "karışımıyla açıklar. Her il için her bileşene üyelik "
              "olasılığı hesaplanır; en yüksek olasılıklı bileşen "
              "rapordaki sert küme etiketi olur. K-Means'teki gibi "
              "yalnız bir merkez uzaklığına dayanmaz; her bileşenin "
              "yayılımını ve özellikler arası ortak değişimi de "
              "modelleyebilir. Uydurma sırasında EM yöntemi üyelik "
              "olasılıkları ile bileşen parametrelerini yineleyerek "
              "veri olasılığını artırır; yakınsama kontrol edilir.", "",
              "**Arama ve sabit ayarlar.** 2–10 arasında dokuz bileşen "
              "sayısı denendi; seçilen hiperparametre bileşen "
              "sayısıdır. `covariance_type='full'` bütün bileşenlerde "
              "beş özelliğin kovaryansını serbest bırakan önceden "
              "belirlenmiş model biçimidir; bu projede farklı "
              "kovaryans türleri taranmadı. `random_state=42` "
              "tekrarlanabilirlik, `n_init=10` on başlangıçtan en iyi "
              "uyumu seçmek, `max_iter=500` yineleme üst sınırı, "
              "`reg_covar=0,000001` kovaryans hesabını sayısal "
              "olarak kararlı tutmak içindir. Bunlar bileşen "
              "aramasından çıkan optimum değerler değil, sabit "
              "çalışma ayarlarıdır. Dokuz modelin yakınsaması "
              "kontrol edildi.", "",
              "**BIC ve AIC nasıl hesaplandı?** `logL`, modelin 81 "
              "ilin tamamı için toplam log-olasılığı, `p` serbest "
              "parametre sayısı, `n=81` olmak üzere "
              "`BIC=−2logL+p·ln(n)` ve `AIC=−2logL+2p`. "
              "İkisinde de küçük değer tercih edilir; BIC fazla "
              "karmaşıklığı AIC'den daha güçlü cezalandırır. Beş "
              "özellikli tam kovaryans modelinde `m` bileşen için "
              "`p=(m−1)+5m+15m`; üç bileşende `p=62`. "
              f"Üç bileşenli modelin AIC'si {tr(float(gm['aic']))}; "
              f"buradan toplam `logL≈{tr((124 - float(gm['aic'])) / 2)}` "
              f"bulunur ve BIC {tr(float(gm['bic']))} olur. "
              "Silhouette ise en yüksek olasılığa göre atanmış "
              "sert etiketlerin beş boyutlu uzaklık temelli "
              "ayrışmasını ölçer; GMM olasılıklarının kendisi "
              "üzerinden hesaplanmaz. Burada 81 ilin hepsi dahil edildi.", "",
              "**2–10 bileşen sonuçları:**", ""]
    lines += gmm_search_table(gm_search)
    lines += [
        "", "**Neden üç bileşen?** İki bileşende Silhouette "
        f"{tr(float(gm2['silhouette_score']), 4)} ile en yüksektir, "
        "fakat 76/5 illik ayrım çoğu ili tek büyük grupta "
        "toplar. Üç bileşende BIC "
        f"{tr(float(gm['bic']))} ile denenenlerin en düşüğüdür; "
        "kümeler 50, 27, 4 ilden oluşur ve tek illik "
        "küme yoktur. Silhouette "
        f"{tr(scores['GMM'], 4)} olur. Dört bileşende BIC "
        f"{tr(float(gm4['bic']))} değerine yükselir, Silhouette "
        f"{tr(float(gm4['silhouette_score']), 4)} değerine iner "
        "ve bir tek illik küme oluşur. AIC on bileşende "
        f"{tr(float(gm10['aic']))} ile en düşük olsa da iki "
        "tek illik küme ve çok küçük gruplar vardır; 81 il "
        "için 209 parametreli tam kovaryanslı modelin aşırı "
        "uyum riski yüksektir. BIC, Silhouette ve küme "
        "büyüklükleri birlikte yorumlanıp üç bileşen "
        "kullanıcıya önerildi ve onaylandı. Dört illik "
        "küme ayrıca incelenmelidir.", "",
    ]
    lines += city_sections(original, labels["GMM"])
    lines += ["Orijinal TÜİK ölçeğindeki küme ortalamaları:", "",
              *profile_table(profiles["GMM"]), "",
              "Küme 2 Ankara, İstanbul, İzmir ve Kocaeli'ni içerir; "
              "ortalama GSYH ve eğitim süresi yüksektir. İstanbul'un "
              "çok yüksek yoğunluğu bu dört ilin yoğunluk ortalamasını "
              "etkiler. Üyelik olasılığı 0,80'in altında kalan "
              "Karabük, Samsun ve Ordu'nun atanması daha belirsizdir. "
              "Tüm olasılıklar ve yöntem ayrıntıları `gmm/` klasöründedir.", "",
              "## 8. PCA ve t-SNE görselleştirmeleri", "",
              "PCA için `n_components=2` değeri, illeri iki eksenli "
              "grafikte göstermek amacıyla **önceden seçildi**; küme "
              "sayısı araması değildir. Beş ölçekli özellikten "
              "en çok varyans taşıyan iki doğrusal eksen hesaplandı. "
              f"İlk eksen %{tr(float(ratios[0] * 100))}, ikinci "
              f"eksen %{tr(float(ratios[1] * 100))}; birlikte "
              f"%{tr(float(ratios.sum() * 100))} varyans açıklar. "
              "Bu oran, ilk iki eksenin açıkladığı varyansların "
              "toplamıdır; kalan bilgi 2B grafikte görünmez.", "",
              "t-SNE için `n_components=2`, `perplexity=20`, "
              "`random_state=42`, `init='pca'`, "
              "`learning_rate='auto'`, `max_iter=1000` kullanıldı. "
              "Perplexity 81 ilden küçük, yerel komşulukları "
              "göstermeye yönelik **görselleştirme ayarı** olarak "
              "seçildi; Elbow, BIC veya Silhouette ile optimize "
              "edilmedi. `random_state=42` konumları tekrar "
              "üretebilmek içindir. PCA ve t-SNE koordinatları "
              "kümeleme girdisi değildi; üç model aynı beş "
              "boyutlu ölçekli veride önceden kurulmuştu. t-SNE'deki "
              "eksen ve uzaklıklar nicel sosyoekonomik fark olarak "
              "okunamaz.", "",
              "Her noktanın bir ili gösterdiği, küme renkleri ve "
              "büyüklükleri belirginleştirilmiş üç sonuç grafiği:", "",
              "- [K-Means küme noktaları](visualization/kume_nokta_kmeans.png)",
              "- [DBSCAN küme noktaları](visualization/kume_nokta_dbscan.png)",
              "- [GMM küme noktaları](visualization/kume_nokta_gmm.png)", "",
              "| Algoritma | PCA | t-SNE |",
              "| --- | --- | --- |",
              "| K-Means | [PCA grafiği](visualization/pca_kmeans.png) | [t-SNE grafiği](visualization/tsne_kmeans.png) |",
              "| DBSCAN | [PCA grafiği](visualization/pca_dbscan.png) | [t-SNE grafiği](visualization/tsne_dbscan.png) |",
              "| GMM | [PCA grafiği](visualization/pca_gmm.png) | [t-SNE grafiği](visualization/tsne_gmm.png) |",
              "", "PCA yükleri ve görsellerin yorumu "
              "`visualization/gorsellestirme_raporu.md` içindedir.", "",
              "## 9. Algoritmaların karşılaştırılması", "",
              "| Yöntem | Küme sayısı | Küme büyüklükleri | Gürültü | Silhouette | Hesaba giren il |",
              "| --- | ---: | --- | ---: | ---: | ---: |",
              f"| K-Means | 3 | 55, 25, 1 | 0 | {tr(scores['K-Means'], 4)} | 81 |",
              f"| DBSCAN | 2 | 65, 4 | 12 | {tr(scores['DBSCAN'], 4)} | 69 |",
              f"| GMM | 3 | 50, 27, 4 | 0 | {tr(scores['GMM'], 4)} | 81 |", "",
              "**Silhouette kapsamı:** K-Means ve GMM bütün 81 il, "
              "DBSCAN yalnız gürültü dışındaki 69 il üzerinden "
              "hesaplandı. Bu nedenle DBSCAN'ın 0,3801 değeri "
              "diğer iki skorla doğrudan eşdeğer değildir; tek başına "
              "algoritma üstünlüğü göstermez. Kümelerin sayısı ve "
              "büyüklüğü de yorum için gereklidir.", "",
              "K-Means ve GMM etiketlerinin kesişimi (satır K-Means, sütun GMM):", "",
              *overlap_table(labels["K-Means"], labels["GMM"]), "",
              "DBSCAN ve K-Means etiketlerinin kesişimi (DBSCAN -1 gürültüdür):", "",
              *overlap_table(labels["DBSCAN"], labels["K-Means"]), "",
              "DBSCAN ve GMM etiketlerinin kesişimi:", "",
              *overlap_table(labels["DBSCAN"], labels["GMM"]), "",
              "Bu tablolar **küme numaralarını eşit anlamlı saymaz**; "
              "yalnız hangi illerin gruplarda birlikte bulunduğunu sayar. "
              f"DBSCAN'ın dört illik küçük kümesi: {', '.join(db_small)}. "
              "K-Means bu illeri daha geniş düşük istihdam/yüksek işsizlik "
              "grubunda, GMM de kendi geniş grubunda toplar. "
              f"GMM'nin {', '.join(metro)} grubu, K-Means'te "
              "İstanbul'un tek başına ayrılmasıyla farklılaşır; "
              "DBSCAN ise İstanbul'u gürültü sayar. Yöntemlerin "
              "merkez, yoğunluk ve olasılık varsayımları farklıdır.", "",
              "## 10. Sonuç ve değerlendirme", "",
              "81 il için veri birleştirme, kalite denetimi, EDA, beş "
              "özellikli ölçeklendirme, üç algoritma ve iki görselleştirme "
              "tamamlandı. Sonuçlar geniş il grupları yanında İstanbul "
              "ve bazı farklı profilli illerin ayrışabildiğini "
              "gösteriyor. K-Means'in tek illik İstanbul kümesi, "
              "DBSCAN'ın 12 gürültü ili ve GMM'nin küçük dört illik "
              "bileşeni yöntemlerin hassasiyetlerini gösterir.", "",
              "Bu projede tek bir algoritmayı kesin 'en iyi' ilan etmek "
              "için yeterli gerekçe yoktur: Silhouette kapsamları "
              "farklıdır, küçük kümeler ve uç değerler sonucu etkiler, "
              "gerçek sınıf etiketleri yoktur. Kümelere açıklayıcı "
              "adlar yalnız orijinal ölçekli profillere bakılarak "
              "önerilebilir: örneğin GMM'deki dört illik grup için "
              "'yüksek GSYH ve eğitimli büyük merkezler'; DBSCAN'ın "
              "dört illik grubu için 'düşük ortalama istihdam ve GSYH' "
              "gibi. Bu adlar yorum kolaylığı sağlar, iller için "
              "değer yargısı değildir.", "",
              "Yeniden üretim için betikler `scripts/` klasöründedir. "
              "Kaynak Excel ve birleşik veri korunmuştur. Bu rapor, "
              "modellerin kaydedilmiş sonuçlarını kullanır; yeni "
              "kümeleme modeli eğitmez.", "",
    ]
    return "\n".join(lines)


def main() -> None:
    original, scaled, labels = check_input()
    metrics = check_metrics(scaled, labels)
    profiles = cluster_profiles(original, labels)
    text = build_report(original, scaled, labels, metrics, profiles)
    REPORT.write_text(text, encoding="utf-8")
    print(f"Nihai rapor kaydedildi: {REPORT}")
    print("10 bölüm tamamlandı; üç modelin sonuçları ve Silhouette kapsamları doğrulandı.")


if __name__ == "__main__":
    main()
