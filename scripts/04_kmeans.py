"""K-Means için K=2–10 araştırması ve onaylanmış K=3 nihai modeli.

Çalıştırma: python scripts/04_kmeans.py
Nihai K=3, araştırma sonuçları kullanıcıya sunulup onaylandıktan sonra eklendi.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "outputs" / "preprocessing" / "iller_olceklendirilmis.csv"
ORIGINAL = ROOT / "outputs" / "tuik_2024_81_il_birlesik.csv"
OUTPUT = ROOT / "outputs" / "kmeans"
FEATURES = [
    "kisi_basi_gsyh_tl",
    "issizlik_orani",
    "istihdam_orani",
    "ortalama_egitim_suresi",
    "nufus_yogunlugu",
]
IDENTIFIERS = ["il_kodu", "il_adi"]


def read_data() -> pd.DataFrame:
    """Ölçeklenmiş B verisinin kapsamını ve model girdilerini doğrula."""
    if not SOURCE.is_file():
        raise FileNotFoundError(f"Ölçeklenmiş veri bulunamadı: {SOURCE}")
    data = pd.read_csv(SOURCE, encoding="utf-8-sig")
    if list(data.columns) != IDENTIFIERS + FEATURES:
        raise ValueError(f"Beklenmeyen sütunlar: {list(data.columns)}")
    if len(data) != 81 or data["il_kodu"].duplicated().any():
        raise ValueError("Veride tam ve benzersiz 81 il bulunmalı")
    if set(data["il_kodu"]) != set(range(1, 82)):
        raise ValueError("İl kodları 1–81 kümesini oluşturmuyor")
    if data.isna().any().any() or data["il_adi"].astype(str).str.strip().eq("").any():
        raise ValueError("Eksik değer veya boş il adı var")
    for feature in FEATURES:
        if not pd.api.types.is_numeric_dtype(data[feature]):
            raise TypeError(f"Sayısal olmayan özellik: {feature}")
    if not np.isfinite(data[FEATURES].to_numpy(dtype=float)).all():
        raise ValueError("Model girdisinde sonsuz veya geçersiz değer var")
    print("Veri doğrulandı: 81 il, 5 sayısal özellik; il kodu ve adı modele alınmayacak.")
    return data


def explore(data: pd.DataFrame) -> pd.DataFrame:
    """Her K için WCSS, Silhouette ve küme büyüklüklerini hesapla."""
    values = data[FEATURES].to_numpy(dtype=float)
    records = []
    for k in range(2, 11):
        model = KMeans(n_clusters=k, random_state=42, n_init=20)
        labels = model.fit_predict(values)
        sizes = np.bincount(labels, minlength=k)
        if np.count_nonzero(sizes) != k:
            raise ValueError(f"K={k}: boş küme oluştu; Silhouette değerlendirmesi durduruldu")
        score = silhouette_score(values, labels)
        record = {"k": k, "wcss_inertia": float(model.inertia_),
                  "silhouette_score": float(score),
                  "en_kucuk_kume": int(sizes.min()),
                  "en_buyuk_kume": int(sizes.max())}
        record.update({f"kume_{number}_il_sayisi": int(sizes[number])
                       if number < k else np.nan for number in range(10)})
        records.append(record)
        print(f"K={k:2d} | WCSS={model.inertia_:9.3f} | Silhouette={score:.4f} | "
              f"Küme büyüklükleri: {sizes.tolist()} (toplam {sizes.sum()} il)")
    return pd.DataFrame.from_records(records)


def save_plot(results: pd.DataFrame, metric: str, ylabel: str, title: str,
              filename: str) -> None:
    """Türkçe başlıklı, açık eksenli grafiği dosyaya kaydet."""
    plt.rcParams["font.family"] = "DejaVu Sans"
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(results["k"], results[metric], marker="o", linewidth=2)
    ax.set_xticks(range(2, 11))
    ax.set_xlabel("Küme sayısı (K)")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUTPUT / filename, dpi=160)
    plt.close(fig)


def build_report(results: pd.DataFrame) -> str:
    """K=2–10 araştırma ölçümlerini ayrı raporla."""
    lines = [
        "# K-Means küme sayısı araştırması", "",
        "Veri: `outputs/preprocessing/iller_olceklendirilmis.csv` (81 il, 5 özellik). "
        "`il_kodu` ve `il_adi` modele alınmadı. `random_state=42`, `n_init=20`.", "",
        "| K | WCSS (inertia) | Silhouette | En küçük küme | En büyük küme | Küme büyüklükleri |",
        "| ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in results.itertuples(index=False):
        sizes = [int(getattr(row, f"kume_{i}_il_sayisi")) for i in range(row.k)]
        lines.append(f"| {row.k} | {row.wcss_inertia:.3f} | "
                     f"{row.silhouette_score:.4f} | {row.en_kucuk_kume} | "
                     f"{row.en_buyuk_kume} | {sizes} |")
    best = results.loc[results["silhouette_score"].idxmax()]
    lines += [
        "", f"En yüksek Silhouette: K={int(best['k'])}, "
        f"skor={best['silhouette_score']:.4f}. Bu tek başına nihai seçim değildir.",
        "", "WCSS'nin azalma hızını Elbow grafiğinde, Silhouette değerlerini "
        "ikinci grafikte ve küme büyüklüklerini birlikte inceleyin. "
        "Dirsek belirsizse bunu karar gerekçesinde açıkça belirtin.",
        "", "Bu araştırma tablosu K seçimi için hazırlanmıştır. Onaylanan "
        "K=3'ün il etiketleri ve yorumları `kmeans_nihai_raporu.md` içindedir.", "",
    ]
    return "\n".join(lines)


def read_original(data: pd.DataFrame) -> pd.DataFrame:
    """Küme yorumları için ham TÜİK değerlerini kimlik sırasıyla doğrula."""
    if not ORIGINAL.is_file():
        raise FileNotFoundError(f"Orijinal ölçekli veri bulunamadı: {ORIGINAL}")
    original = pd.read_csv(ORIGINAL, encoding="utf-8-sig")
    if len(original) != 81 or original.isna().any().any():
        raise ValueError("Orijinal veri 81 tam il içermiyor")
    if not original[IDENTIFIERS].equals(data[IDENTIFIERS]):
        raise ValueError("Ölçekli ve orijinal veride il kodu/adı/sırası uyuşmuyor")
    if not np.isfinite(original[FEATURES].to_numpy(dtype=float)).all():
        raise ValueError("Orijinal özelliklerde geçersiz sayı var")
    return original


def final_model(data: pd.DataFrame, original: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, float]:
    """Onaylanan K=3 modeliyle etiket, merkez ve ham ölçekli profil üret."""
    values = data[FEATURES].to_numpy(dtype=float)
    model = KMeans(n_clusters=3, random_state=42, n_init=20)
    labels = model.fit_predict(values)
    counts = np.bincount(labels, minlength=3)
    if counts.sum() != 81 or np.any(counts == 0):
        raise ValueError("Nihai modelde boş küme veya eksik il var")
    score = float(silhouette_score(values, labels))
    assignments = data[IDENTIFIERS].copy()
    assignments["kume"] = labels
    centers = pd.DataFrame(model.cluster_centers_, columns=FEATURES)
    centers.insert(0, "kume", range(3))
    raw = original[IDENTIFIERS + FEATURES].copy()
    raw["kume"] = labels
    profiles = raw.groupby("kume", sort=True)[FEATURES].mean().reset_index()
    profiles.insert(1, "il_sayisi", counts)
    print(f"Onaylanan K=3 modeli: WCSS={model.inertia_:.3f}, "
          f"Silhouette={score:.4f}; küme büyüklükleri={counts.tolist()}.")
    for cluster in range(3):
        cities = assignments.loc[assignments["kume"] == cluster, "il_adi"].tolist()
        print(f"Küme {cluster} ({len(cities)} il): {', '.join(cities)}")
    return assignments, centers, profiles, score


def build_final_report(assignments: pd.DataFrame, centers: pd.DataFrame,
                       profiles: pd.DataFrame, score: float,
                       research: pd.DataFrame) -> str:
    """K seçimini, hesaplama yöntemini ve ham ölçekli küme özelliklerini anlat."""
    line3 = research.loc[research["k"] == 3].iloc[0]
    line2 = research.loc[research["k"] == 2].iloc[0]
    line4 = research.loc[research["k"] == 4].iloc[0]
    lines = [
        "# Nihai K-Means raporu — K=3", "",
        "## Veri ve hesaplama yöntemi", "",
        "81 ilin beş StandardScaler ile ölçeklendirilmiş özelliği kullanıldı: "
        + ", ".join(f"`{name}`" for name in FEATURES) + ". "
        "`il_kodu` ve `il_adi` modele verilmedi. K=2–10 aralığındaki her değer "
        "için ayrı bir K-Means modeli `random_state=42` ve `n_init=20` ile "
        "uyduruldu. `n_init=20`, 20 farklı başlangıç arasından en düşük "
        "WCSS'li çözümü seçer. Böylece sonuç başlangıç merkezlerine daha az bağımlıdır.", "",
        "**WCSS (inertia)**, her ilin beş boyutlu ölçekli konumu ile kendi küme "
        "merkezi arasındaki uzaklığın karesinin toplamıdır: "
        "`Σ_i ||x_i - μ_küme(i)||²`. Daha küçük değer daha sıkı kümeler "
        "demektir; K arttıkça WCSS doğal olarak düşer. Elbow yöntemi, "
        "düşüşün belirgin biçimde yavaşladığı K'yi arar.", "",
        "**Silhouette Score** için her ilin kendi kümesindeki diğer illere "
        "ortalama uzaklığı `a`, en yakın başka kümeye ortalama uzaklığı `b` "
        "olarak hesaplanır. İl skoru `(b-a)/max(a,b)`; tabloda 81 ilin "
        "ortalaması yer alır. Değerin yüksek olması genellikle daha iyi "
        "ayrışma gösterir. Tek elemanlı kümedeki ilin Silhouette değeri "
        "sklearn tarafından 0 kabul edilir.", "",
        "## Neden K=3 seçildi?", "",
        f"K=2: WCSS {line2['wcss_inertia']:.3f}, Silhouette "
        f"{line2['silhouette_score']:.4f}; iki küme 25 ve 56 il içeriyor. "
        f"K=3: WCSS {line3['wcss_inertia']:.3f}, Silhouette "
        f"{line3['silhouette_score']:.4f}; 55, 25 ve 1 illik kümeler oluştu. "
        f"K=4: WCSS {line4['wcss_inertia']:.3f}, Silhouette "
        f"{line4['silhouette_score']:.4f}; 42, 14, 24 ve 1 illik kümeler oluştu.", "",
        "K=3, denenen değerler içinde en yüksek Silhouette skorunu verdi. "
        "K=2'den K=3'e geçişte WCSS belirgin düştü. Elbow grafiğinde "
        "yavaşlama K=4 civarında görülüyor; tek ve tartışmasız bir dirsek "
        "yok. K=4'ün Silhouette skoru K=3'ten düşük. K=3'te tek "
        "illik küme bulunması kararın önemli sınırlamasıdır: bu il "
        "ayrı bir şehir profili olabilir, fakat genel küme kalitesini "
        "tek başına kanıtlamaz. K=2 daha dengeli bir karşılaştırma seçeneğidir. "
        "Bu gerekçelerle K=3 kullanıcı onayıyla nihai K-Means modeli olarak seçildi.", "",
        "## Nihai sonuç", "",
        f"Silhouette Score: **{score:.4f}**. Küme numaraları yalnızca "
        "kimliktir; sıralama veya başarı derecesi belirtmez. "
        "Tek illik küme bir hesaplama hatası değildir, ancak diğer "
        "algoritmalarla karşılaştırırken özellikle dikkate alınmalıdır.", "",
        "| Küme | İl sayısı | İller |", "| ---: | ---: | --- |",
    ]
    for cluster in range(3):
        cities = assignments.loc[assignments["kume"] == cluster, "il_adi"].tolist()
        lines.append(f"| {cluster} | {len(cities)} | {', '.join(cities)} |")
    lines += ["", "## Küme merkezleri (ölçeklendirilmiş değerler)", "",
              "| Küme | " + " | ".join(FEATURES) + " |",
              "| ---: | " + " | ".join("---:" for _ in FEATURES) + " |"]
    for row in centers.itertuples(index=False, name=None):
        lines.append("| " + str(row[0]) + " | "
                     + " | ".join(f"{v:.3f}" for v in row[1:]) + " |")
    lines += ["", "Merkezlerde 0 yaklaşık 81 il ortalamasını; pozitif/negatif "
              "değerler ortalamanın üstünü/altını gösterir.", "",
              "## Orijinal TÜİK ölçeğinde küme ortalamaları", "",
              "Bu tablo yorum için orijinal birleşik veri setinden hesaplandı. "
              "GSYH TL, işsizlik ve istihdam %, eğitim yıl, yoğunluk kişi/km² "
              "birimindedir. Özellikle tek illik kümenin ortalaması o ilin değeridir.", "",
              "| Küme | İl sayısı | GSYH (TL) | İşsizlik (%) | İstihdam (%) | "
              "Eğitim (yıl) | Yoğunluk (kişi/km²) |",
              "| ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for row in profiles.itertuples(index=False, name=None):
        lines.append(f"| {row[0]} | {row[1]} | "
                     + " | ".join(f"{v:,.2f}" for v in row[2:]) + " |")
    lines += ["", "Küme profilleri ortalamaları gösterir; bir kümedeki bütün "
              "illerin aynı özelliklere sahip olduğu anlamına gelmez. "
              "İl bazında etiketler `iller_kmeans_k3.csv` dosyasındadır.", ""]
    return "\n".join(lines)


def main() -> None:
    data = read_data()
    results = explore(data)
    original = read_original(data)
    assignments, centers, profiles, score = final_model(data, original)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    results.to_csv(OUTPUT / "k_arastirmasi.csv", index=False, encoding="utf-8-sig")
    save_plot(results, "wcss_inertia", "WCSS (inertia)",
              "K-Means Elbow grafiği", "elbow.png")
    save_plot(results, "silhouette_score", "Silhouette Score",
              "K-Means Silhouette grafiği", "silhouette.png")
    (OUTPUT / "k_arastirmasi_raporu.md").write_text(
        build_report(results), encoding="utf-8"
    )
    assignments.to_csv(OUTPUT / "iller_kmeans_k3.csv", index=False, encoding="utf-8-sig")
    centers.to_csv(OUTPUT / "kume_merkezleri_olcekli.csv", index=False, encoding="utf-8-sig")
    profiles.to_csv(OUTPUT / "kume_profilleri_orijinal.csv", index=False, encoding="utf-8-sig")
    (OUTPUT / "kmeans_nihai_raporu.md").write_text(
        build_final_report(assignments, centers, profiles, score, results), encoding="utf-8"
    )
    print(f"K-Means aşaması tamamlandı. Çıktı klasörü: {OUTPUT}")
    print("DBSCAN, GMM veya görselleştirme aşamasına geçilmedi.")


if __name__ == "__main__":
    main()
