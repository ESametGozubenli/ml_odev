"""Üç algoritmanın mevcut kümelerini anlaşılır nokta grafikleriyle gösterir.

Çalıştırma: python scripts/09_kume_nokta_grafikleri.py
Kümeleme modeli eğitmez; önceki PCA koordinatlarını ve il etiketlerini okur.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
COORDINATES = OUTPUTS / "visualization" / "pca_koordinatlari.csv"
LABEL_FILES = {
    "K-Means": OUTPUTS / "kmeans" / "iller_kmeans_k3.csv",
    "DBSCAN": OUTPUTS / "dbscan" / "iller_dbscan.csv",
    "GMM": OUTPUTS / "gmm" / "iller_gmm.csv",
}
COLORS = {0: "#0072B2", 1: "#D55E00", 2: "#009E73"}
NOTES = {
    "K-Means": "Tek illik küme:\nİstanbul",
    "DBSCAN": "Dört illik küme:\nDiyarbakır, Mardin,\nMuş, Siirt\n\nSiyah X: gürültü",
    "GMM": "Dört illik küme:\nAnkara, İstanbul,\nİzmir, Kocaeli",
}


def read_inputs() -> tuple[pd.DataFrame, dict[str, np.ndarray]]:
    """81 ilin PCA koordinatlarını ve üç modelin etiketlerini doğrula."""
    if not COORDINATES.is_file():
        raise FileNotFoundError(f"PCA koordinatları bulunamadı: {COORDINATES}")
    coordinates = pd.read_csv(COORDINATES, encoding="utf-8-sig")
    if list(coordinates.columns) != ["il_kodu", "il_adi", "pca_1", "pca_2"]:
        raise ValueError("PCA koordinat sütunları beklenen biçimde değil")
    if len(coordinates) != 81 or coordinates["il_kodu"].duplicated().any():
        raise ValueError("PCA koordinatlarında 81 benzersiz il bulunmalı")
    if coordinates.isna().any().any() or not np.isfinite(
        coordinates[["pca_1", "pca_2"]].to_numpy(dtype=float)
    ).all():
        raise ValueError("PCA koordinatları eksik veya geçersiz")
    labels = {}
    for algorithm, path in LABEL_FILES.items():
        if not path.is_file():
            raise FileNotFoundError(f"Küme sonucu bulunamadı: {path}")
        frame = pd.read_csv(path, encoding="utf-8-sig")
        if len(frame) != 81 or frame["il_kodu"].duplicated().any():
            raise ValueError(f"{algorithm}: 81 benzersiz il bulunmalı")
        if not {"il_kodu", "il_adi", "kume"}.issubset(frame.columns):
            raise ValueError(f"{algorithm}: il kimliği veya küme sütunu eksik")
        if frame[["il_kodu", "il_adi", "kume"]].isna().any().any():
            raise ValueError(f"{algorithm}: eksik etiket var")
        if not pd.api.types.is_integer_dtype(frame["kume"]):
            raise TypeError(f"{algorithm}: küme etiketleri tamsayı değil")
        aligned = coordinates[["il_kodu", "il_adi"]].merge(
            frame[["il_kodu", "il_adi", "kume"]], on="il_kodu", how="left",
            validate="one_to_one", suffixes=("_pca", "_model"),
        )
        if aligned["kume"].isna().any() or not aligned["il_adi_pca"].equals(
            aligned["il_adi_model"]
        ):
            raise ValueError(f"{algorithm}: il kodu/adı eşleşmiyor")
        labels[algorithm] = aligned["kume"].to_numpy(dtype=int)
        print(f"{algorithm}: 81 il ve küme etiketleri eşleştirildi.")
    return coordinates, labels


def make_plot(coordinates: pd.DataFrame, labels: np.ndarray,
              algorithm: str) -> None:
    """Kümeleri renkli noktalarla, DBSCAN gürültüsünü X ile göster."""
    plt.rcParams["font.family"] = "DejaVu Sans"
    plt.rcParams["axes.unicode_minus"] = False
    fig, ax = plt.subplots(figsize=(12, 7))
    fig.subplots_adjust(left=0.09, right=0.71, bottom=0.14, top=0.87)
    fig.text(0.73, 0.85, "Grafikteki gruplar", fontsize=11, weight="bold")
    for position, cluster in enumerate(sorted(np.unique(labels))):
        mask = labels == cluster
        if cluster == -1:
            ax.scatter(coordinates.loc[mask, "pca_1"],
                       coordinates.loc[mask, "pca_2"],
                       marker="X", s=115, color="#222222", alpha=0.9,
                       edgecolors="white", linewidths=0.8)
            symbol, color, label = "X", "#222222", f"Gürültü: {int(mask.sum())} il"
        else:
            ax.scatter(coordinates.loc[mask, "pca_1"],
                       coordinates.loc[mask, "pca_2"],
                       marker="o", s=90, color=COLORS[int(cluster)],
                       alpha=0.86, edgecolors="white", linewidths=0.8)
            symbol, color = "●", COLORS[int(cluster)]
            label = f"Küme {cluster}: {int(mask.sum())} il"
        y = 0.80 - position * 0.055
        fig.text(0.73, y, symbol, color=color, fontsize=17, va="center")
        fig.text(0.765, y, label, fontsize=11, va="center")
    ax.set_xlabel("PCA 1 — beş özelliğin 2B görünümü")
    ax.set_ylabel("PCA 2 — beş özelliğin 2B görünümü")
    ax.set_title(f"{algorithm}: 81 ilin küme sonucu", fontsize=15, pad=14)
    ax.grid(alpha=0.22)
    ax.margins(x=0.12, y=0.15)
    fig.text(0.73, 0.57, NOTES[algorithm], fontsize=10, va="top")
    fig.text(0.09, 0.04,
             "Noktalar PCA ile çizildi; kümeler beş özellikli ölçekli veride hesaplandı. "
             "Küme numaraları sıralama değildir.", fontsize=9)
    filename = {
        "K-Means": "kume_nokta_kmeans.png",
        "DBSCAN": "kume_nokta_dbscan.png",
        "GMM": "kume_nokta_gmm.png",
    }[algorithm]
    target = OUTPUTS / "visualization" / filename
    fig.savefig(target, dpi=180)
    plt.close(fig)
    print(f"Küme noktaları kaydedildi: {target}")


def main() -> None:
    coordinates, labels = read_inputs()
    for algorithm, values in labels.items():
        make_plot(coordinates, values, algorithm)
    print("Üç nokta grafiği hazır. Yeni kümeleme modeli eğitilmedi.")


if __name__ == "__main__":
    main()
