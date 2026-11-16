"""Üç kümeleme sonucunu PCA ve t-SNE ile iki boyutta gösterir.

Çalıştırma: python scripts/07_gorsellestirme.py
PCA ve t-SNE koordinatları yalnız görselleştirme içindir; model girdisi değildir.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "outputs" / "preprocessing" / "iller_olceklendirilmis.csv"
LABEL_FILES = {
    "K-Means": ROOT / "outputs" / "kmeans" / "iller_kmeans_k3.csv",
    "DBSCAN": ROOT / "outputs" / "dbscan" / "iller_dbscan.csv",
    "GMM": ROOT / "outputs" / "gmm" / "iller_gmm.csv",
}
OUTPUT = ROOT / "outputs" / "visualization"
IDENTIFIERS = ["il_kodu", "il_adi"]
FEATURES = [
    "kisi_basi_gsyh_tl",
    "issizlik_orani",
    "istihdam_orani",
    "ortalama_egitim_suresi",
    "nufus_yogunlugu",
]
PERPLEXITY = 20
RANDOM_STATE = 42
TSNE_MAX_ITER = 1000
ANNOTATED_CITIES = ("Ankara", "İstanbul", "İzmir", "Kocaeli")


def read_data() -> pd.DataFrame:
    """Beş özellikli 81 il verisini doğrula."""
    if not SOURCE.is_file():
        raise FileNotFoundError(f"Ölçekli veri bulunamadı: {SOURCE}")
    data = pd.read_csv(SOURCE, encoding="utf-8-sig")
    if list(data.columns) != IDENTIFIERS + FEATURES:
        raise ValueError(f"Beklenmeyen sütunlar: {list(data.columns)}")
    if len(data) != 81 or data["il_kodu"].duplicated().any():
        raise ValueError("Tam ve benzersiz 81 il bulunmalı")
    if set(data["il_kodu"]) != set(range(1, 82)):
        raise ValueError("İl kodları 1–81 kümesini oluşturmuyor")
    if data.isna().any().any() or data["il_adi"].astype(str).str.strip().eq("").any():
        raise ValueError("Eksik değer veya boş il adı var")
    for feature in FEATURES:
        if not pd.api.types.is_numeric_dtype(data[feature]):
            raise TypeError(f"Sayısal olmayan özellik: {feature}")
    if not np.isfinite(data[FEATURES].to_numpy(dtype=float)).all():
        raise ValueError("Sonsuz veya geçersiz özellik değeri var")
    print("Girdi doğrulandı: 81 il, 5 ölçekli özellik; kimlik sütunları modele alınmıyor.")
    return data


def read_labels(data: pd.DataFrame) -> dict[str, np.ndarray]:
    """Üç algoritmanın etiketlerini il kodu ve adıyla aynı sıraya getir."""
    result = {}
    for algorithm, path in LABEL_FILES.items():
        if not path.is_file():
            raise FileNotFoundError(f"{algorithm} etiket dosyası bulunamadı: {path}")
        labels = pd.read_csv(path, encoding="utf-8-sig")
        if not set(IDENTIFIERS + ["kume"]).issubset(labels.columns):
            raise ValueError(f"{algorithm}: kimlik veya küme sütunu eksik")
        if len(labels) != 81 or labels["il_kodu"].duplicated().any():
            raise ValueError(f"{algorithm}: 81 benzersiz il bulunmalı")
        if labels[IDENTIFIERS].isna().any().any() or labels["kume"].isna().any():
            raise ValueError(f"{algorithm}: eksik kimlik/küme değeri")
        if not pd.api.types.is_integer_dtype(labels["kume"]):
            raise TypeError(f"{algorithm}: küme etiketleri tamsayı değil")
        ordered = data[IDENTIFIERS].merge(
            labels[IDENTIFIERS + ["kume"]], on="il_kodu", how="left",
            validate="one_to_one", suffixes=("_girdi", "_etiket"),
        )
        if ordered["kume"].isna().any() or not ordered["il_adi_girdi"].equals(
            ordered["il_adi_etiket"]
        ):
            raise ValueError(f"{algorithm}: il kodu/adı eşleşmiyor")
        values = ordered["kume"].to_numpy(dtype=int)
        if algorithm != "DBSCAN" and (values < 0).any():
            raise ValueError(f"{algorithm}: negatif küme etiketi var")
        if algorithm == "DBSCAN" and (values < -1).any():
            raise ValueError("DBSCAN: -1 dışında negatif etiket var")
        result[algorithm] = values
        numbers, sizes = np.unique(values, return_counts=True)
        counts = {int(number): int(size) for number, size in zip(numbers, sizes)}
        print(f"{algorithm} etiketleri doğrulandı: 81 il; küme sayıları {counts}.")
    return result


def calculate_coordinates(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame,
                                                       PCA, float]:
    """PCA ve t-SNE'yi aynı beş boyutlu girdiye ayrı ayrı uygula."""
    values = data[FEATURES].to_numpy(dtype=float)
    pca = PCA(n_components=2)
    pca_values = pca.fit_transform(values)
    tsne = TSNE(
        n_components=2,
        perplexity=PERPLEXITY,
        random_state=RANDOM_STATE,
        init="pca",
        learning_rate="auto",
        max_iter=TSNE_MAX_ITER,
    )
    tsne_values = tsne.fit_transform(values)
    if (pca_values.shape != (81, 2) or tsne_values.shape != (81, 2)
            or not np.isfinite(pca_values).all() or not np.isfinite(tsne_values).all()):
        raise ValueError("İki boyutlu koordinatlarda boyut veya değer hatası")
    pca_frame = data[IDENTIFIERS].copy()
    pca_frame[["pca_1", "pca_2"]] = pca_values
    tsne_frame = data[IDENTIFIERS].copy()
    tsne_frame[["tsne_1", "tsne_2"]] = tsne_values
    variance = float(pca.explained_variance_ratio_.sum())
    print("PCA: 2 bileşen hesaplandı; açıklanan varyans "
          f"%{variance * 100:.2f}.")
    print(f"t-SNE: perplexity={PERPLEXITY}, random_state={RANDOM_STATE}, "
          f"max_iter={TSNE_MAX_ITER}; 81 il için 2B koordinatlar hesaplandı.")
    return pca_frame, tsne_frame, pca, float(tsne.kl_divergence_)


def plot_clusters(frame: pd.DataFrame, labels: np.ndarray, algorithm: str,
                  method: str, variance_ratios: np.ndarray | None) -> None:
    """Küme renkleri ve DBSCAN gürültüsüyle okunabilir grafik üret."""
    plt.rcParams["font.family"] = "DejaVu Sans"
    plt.rcParams["axes.unicode_minus"] = False
    xcol, ycol = ("pca_1", "pca_2") if method == "pca" else ("tsne_1", "tsne_2")
    fig, ax = plt.subplots(figsize=(9, 6))
    palette = plt.get_cmap("tab10")
    for number in sorted(np.unique(labels)):
        mask = labels == number
        if number == -1:
            ax.scatter(frame.loc[mask, xcol], frame.loc[mask, ycol],
                       marker="X", s=90, c="#202020", alpha=0.9,
                       edgecolors="white", linewidths=0.6,
                       label=f"Gürültü ({int(mask.sum())})")
        else:
            ax.scatter(frame.loc[mask, xcol], frame.loc[mask, ycol],
                       marker="o", s=66, color=palette(int(number) % 10),
                       alpha=0.85, edgecolors="white", linewidths=0.6,
                       label=f"Küme {number} ({int(mask.sum())})")
    offsets = {
        "İstanbul": (-8, 7),
        "Ankara": (7, 7),
        "İzmir": (7, 7),
        "Kocaeli": (7, -11),
    }
    for city in ANNOTATED_CITIES:
        row = frame.loc[frame["il_adi"] == city]
        if len(row) == 1:
            dx, dy = offsets[city]
            ax.annotate(city, (row.iloc[0][xcol], row.iloc[0][ycol]),
                        xytext=(dx, dy), textcoords="offset points", fontsize=8,
                        ha="right" if city == "İstanbul" else "left")
    if method == "pca":
        ax.set_xlabel(f"PCA 1 (%{variance_ratios[0] * 100:.1f} varyans)")
        ax.set_ylabel(f"PCA 2 (%{variance_ratios[1] * 100:.1f} varyans)")
        method_label = "PCA"
    else:
        ax.set_xlabel("t-SNE 1 (keyfî ölçek)")
        ax.set_ylabel("t-SNE 2 (keyfî ölçek)")
        method_label = "t-SNE"
    ax.set_title(f"{algorithm} kümeleri — {method_label} 2B görünüm")
    ax.grid(alpha=0.2)
    ax.margins(x=0.18, y=0.12)
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1),
              frameon=True, framealpha=1.0, facecolor="white")
    fig.tight_layout()
    name = {"K-Means": "kmeans", "DBSCAN": "dbscan", "GMM": "gmm"}[algorithm]
    fig.savefig(OUTPUT / f"{method}_{name}.png", dpi=180)
    plt.close(fig)
    print(f"Grafik kaydedildi: {method}_{name}.png")


def build_report(pca: PCA, kl_divergence: float,
                 labels: dict[str, np.ndarray]) -> str:
    """Hesaplama adımlarını, kapsamı ve görsellerin sınırlarını kaydet."""
    ratios = pca.explained_variance_ratio_
    lines = [
        "# PCA ve t-SNE ile iki boyutlu küme görselleştirmeleri", "",
        "## Veri ve doğrulama", "",
        "Girdi `outputs/preprocessing/iller_olceklendirilmis.csv`: "
        "81 il ve beş StandardScaler ile ölçekli özellik. Kullanılan "
        "özellikler: " + ", ".join(f"`{feature}`" for feature in FEATURES) + ". "
        "`il_kodu` ve `il_adi` boyut indirgeme girdisine alınmadı. "
        "K-Means, DBSCAN ve GMM çıktı dosyaları il kodu ve adına göre "
        "eşleştirildi; 81 benzersiz il ve eksik/sonlu değerler doğrulandı.", "",
        "## PCA: ne, neden, nasıl?", "",
        "PCA, beş ölçekli özelliğin en fazla varyansını taşıyan iki "
        "birbirine dik doğrusal ekseni buldu (`n_components=2`). "
        "Böylece beş boyutlu il konumları 2B çizildi. Bu işlem yalnız "
        "görselleştirme içindir; K-Means, DBSCAN ve GMM modelleri "
        "orijinal beş boyutlu ölçekli veri üzerinde kurulmuştu.", "",
        f"PCA 1 açıklanan varyans: **%{ratios[0] * 100:.2f}**; "
        f"PCA 2: **%{ratios[1] * 100:.2f}**; "
        f"toplam: **%{ratios.sum() * 100:.2f}**. "
        "Kalan varyans 2B grafikte görünmez. Eksen yükleri "
        "`pca_yukleri.csv` dosyasında kayıtlıdır; işaretlerin yönü "
        "tek başına iyi/kötü anlamına gelmez.", "",
        "PCA 1 yükleri: GSYH `+0,590`, istihdam `+0,460`, eğitim "
        "`+0,475`, nüfus yoğunluğu `+0,332`, işsizlik `-0,324`. "
        "Bu veride sağa doğru hareket genellikle daha yüksek GSYH, "
        "istihdam ve eğitimle, daha düşük işsizlikle ilişkilidir. "
        "PCA 2'de en belirgin yükler işsizlik `+0,648`, yoğunluk "
        "`+0,467` ve istihdam `-0,459` değerleridir. İşaretler PCA "
        "ekseninin keyfî yönüne bağlıdır; yorum yüklerin birbirine göre "
        "ilişkisi üzerinden yapılmalıdır.", "",
        "## t-SNE: ne, neden, nasıl?", "",
        "t-SNE aynı beş boyutlu veride yakın illerin 2B düzlemde "
        "yakın kalmasını amaçlayan doğrusal olmayan bir görselleştirmedir. "
        f"`n_components=2`, `perplexity={PERPLEXITY}`, "
        f"`random_state={RANDOM_STATE}`, `init='pca'`, "
        f"`learning_rate='auto'`, `max_iter={TSNE_MAX_ITER}` kullanıldı. "
        "Perplexity 81 gözlemden küçüktür. "
        f"Son KL divergence: **{kl_divergence:.4f}**; bu değer "
        "algoritmanın gömme ölçüsüdür, bir küme kalitesi puanı değildir. "
        "t-SNE eksenlerinin yönü ve ölçeği keyfîdir; uzak kümeler "
        "arasındaki mutlak mesafeyi veya küme alanını sosyoekonomik "
        "farkın nicel ölçüsü gibi yorumlamayın.", "",
        "## Üç algoritmanın grafikleri", "",
        "PCA ve t-SNE koordinatları **birer kez** hesaplandı; üç "
        "algoritmanın mevcut etiketleri ayrı grafiklerde renklendirildi. "
        "Aynı il her algoritmanın grafiklerinde aynı koordinattadır. "
        "Küme numaraları algoritmalar arasında eşdeğer değildir; aynı "
        "renk aynı sosyoekonomik küme anlamına gelmez. İstanbul, "
        "Ankara, İzmir ve Kocaeli okunabilirlik için etiketlendi. "
        "DBSCAN gürültü illeri siyah `X` ile gösterildi.", "",
        "| Algoritma | Etiket dağılımı | PCA | t-SNE |",
        "| --- | --- | --- | --- |",
    ]
    for algorithm, values in labels.items():
        numbers, counts = np.unique(values, return_counts=True)
        distribution = ", ".join(
            f"{'gürültü' if number == -1 else f'küme {number}'}: {count}"
            for number, count in zip(numbers, counts)
        )
        name = {"K-Means": "kmeans", "DBSCAN": "dbscan", "GMM": "gmm"}[algorithm]
        lines.append(f"| {algorithm} | {distribution} | `pca_{name}.png` | "
                     f"`tsne_{name}.png` |")
    lines += [
        "", "## Grafiklerde görülen örüntüler", "",
        "PCA görünümünde K-Means'in 55 ve 25 illik iki büyük grubu "
        "özellikle PCA 1 boyunca ayrılıyor; İstanbul tek illik "
        "grup olarak üst sağ tarafta duruyor. GMM, İstanbul'u "
        "Ankara, İzmir ve Kocaeli ile dört illik bir grupta gösteriyor. "
        "DBSCAN'de gürültü illeri düzlemin tek bir köşesinde "
        "toplanmıyor; farklı konumlardaki iller yoğunluk bağlantısı "
        "kuramadığı için gürültü sayılmış olabilir. Bu, grafikten "
        "görülen bir örüntüdür; DBSCAN kararı beş boyutlu uzayda verildi.", "",
        "t-SNE görünümünde bazı yakın il grupları daha belirgin "
        "görünüyor; Ankara, İstanbul, İzmir ve Kocaeli alt bölgede "
        "yakın konumlarda. t-SNE yerel komşuluklara ağırlık verdiği "
        "için bu düzlemde görülen küme aralıkları nicel uzaklık "
        "olarak yorumlanmamalıdır.", "",
        "", "## Yorum sınırları ve sonraki adım", "",
        "Bir 2B grafikte yakınlık görmek, beş boyutlu uzaydaki bütün "
        "farkların korunduğu anlamına gelmez. PCA'nın açıklamadığı "
        "varyans ve t-SNE'nin yerel komşuluk vurgusu dikkate alınmalıdır. "
        "Özellikle DBSCAN gürültüsü ile diğer algoritmaların küme "
        "etiketleri farklı tanımlara dayanır. Grafikler, önceden "
        "hesaplanmış kümeleri incelemek içindir; PCA ve t-SNE "
        "koordinatları model girdisi olarak kullanılmadı ve bu kod "
        "iki boyutlu koordinatlarda yeniden kümeleme yapmaz.", "",
        "Koordinatlar `pca_koordinatlari.csv` ve `tsne_koordinatlari.csv` "
        "dosyalarında saklandı. Nihai algoritma karşılaştırması "
        "bu aşamada yapılmadı.", "",
    ]
    return "\n".join(lines)


def main() -> None:
    data = read_data()
    labels = read_labels(data)
    pca_frame, tsne_frame, pca, kl_divergence = calculate_coordinates(data)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    pca_frame.to_csv(OUTPUT / "pca_koordinatlari.csv", index=False,
                     encoding="utf-8-sig")
    tsne_frame.to_csv(OUTPUT / "tsne_koordinatlari.csv", index=False,
                      encoding="utf-8-sig")
    loadings = pd.DataFrame(pca.components_.T, columns=["pca_1", "pca_2"])
    loadings.insert(0, "ozellik", FEATURES)
    loadings.to_csv(OUTPUT / "pca_yukleri.csv", index=False, encoding="utf-8-sig")
    for algorithm, values in labels.items():
        plot_clusters(pca_frame, values, algorithm, "pca",
                      pca.explained_variance_ratio_)
        plot_clusters(tsne_frame, values, algorithm, "tsne", None)
    (OUTPUT / "gorsellestirme_raporu.md").write_text(
        build_report(pca, kl_divergence, labels), encoding="utf-8"
    )
    print(f"Görselleştirme tamamlandı: 6 grafik, 2 koordinat tablosu, "
          f"PCA yükleri ve rapor. Çıktılar: {OUTPUT}")
    print("Kümeleme yeniden yapılmadı; nihai karşılaştırma aşamasına geçilmedi.")


if __name__ == "__main__":
    main()
