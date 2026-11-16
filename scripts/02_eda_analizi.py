"""TÜİK 2024 il verileri için keşifsel analiz.

Çalıştırma: python scripts/02_eda_analizi.py
Kaynak CSV değiştirilmez. Betik yalnızca outputs/eda/ altına çıktı yazar.
"""

from __future__ import annotations

from pathlib import Path
import re

import matplotlib

matplotlib.use("Agg")  # Grafikler dosyaya kaydedilir; pencere açılmaz.
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "outputs" / "tuik_2024_81_il_birlesik.csv"
OUTPUT = ROOT / "outputs" / "eda"
GRAPHS = OUTPUT / "grafikler"

FEATURES = {
    "kisi_basi_gsyh_tl": ("Kişi başına GSYH", "TL"),
    "isgucune_katilma_orani": ("İşgücüne katılma oranı", "%"),
    "issizlik_orani": ("İşsizlik oranı", "%"),
    "istihdam_orani": ("İstihdam oranı", "%"),
    "ortalama_egitim_suresi": ("Ortalama eğitim süresi", "yıl"),
    "nufus_yogunlugu": ("Nüfus yoğunluğu", "kişi/km²"),
}
CORRELATION_LIMIT = 0.80
SKEW_LIMIT = 1.0


def configure_fonts() -> None:
    """Matplotlib'in Türkçe karakterleri gösterebilen yaygın yazı tiplerini kullan."""
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans", "Arial", "Liberation Sans"],
        "axes.unicode_minus": False,
        "figure.dpi": 120,
        "savefig.dpi": 160,
    })


def load_and_check() -> pd.DataFrame:
    """Şemayı ve 81 il kapsamını doğrula; veri temizliği veya doldurma yapma."""
    if not SOURCE.is_file():
        raise FileNotFoundError(f"Birleşik CSV bulunamadı: {SOURCE}")
    data = pd.read_csv(SOURCE, encoding="utf-8-sig")
    required = ["il_kodu", "il_adi", *FEATURES]
    if list(data.columns) != required:
        raise ValueError(f"Beklenmeyen sütunlar: {list(data.columns)}; beklenen: {required}")

    print(f"Kaynak: {SOURCE}")
    print(f"Satır sayısı: {len(data)}, sütun sayısı: {len(data.columns)}")
    print("Sütunlar ve veri türleri:")
    print(data.dtypes.to_string())
    print("Eksik değer sayıları:")
    print(data.isna().sum().to_string())
    duplicate_codes = data.loc[data.duplicated("il_kodu", keep=False), "il_kodu"].tolist()
    print(f"Tekrar eden il kodları: {duplicate_codes}")

    problems = []
    if len(data) != 81:
        problems.append(f"81 yerine {len(data)} satır var")
    if data["il_kodu"].isna().any() or set(data["il_kodu"]) != set(range(1, 82)):
        problems.append("il kodları 1–81 kümesini oluşturmuyor")
    if duplicate_codes:
        problems.append("tekrar eden il kodu var")
    if data["il_adi"].isna().any() or data["il_adi"].astype(str).str.strip().eq("").any():
        problems.append("eksik il adı var")
    if data["il_adi"].duplicated().any():
        problems.append("tekrar eden il adı var")
    if data.isna().any().any():
        problems.append("eksik değer var")
    for feature in FEATURES:
        if not pd.api.types.is_numeric_dtype(data[feature]):
            problems.append(f"{feature} sayısal değil")
        elif not np.isfinite(data[feature].to_numpy(dtype=float)).all():
            problems.append(f"{feature} sonlu olmayan değer içeriyor")
    if problems:
        raise ValueError("EDA durduruldu: " + "; ".join(problems))
    print("Kapsam kontrolü: 81 il, benzersiz kodlar, eksiksiz sayısal veriler.\n")
    return data


def summarize(data: pd.DataFrame) -> pd.DataFrame:
    """Altı sayısal özelliğin temel dağılım ölçülerini hesapla."""
    summary = data[list(FEATURES)].agg(["min", "max", "mean", "median", "std", "skew"]).T
    summary = summary.rename(columns={
        "min": "minimum", "max": "maksimum", "mean": "ortalama",
        "median": "medyan", "std": "standart_sapma", "skew": "carpiklik",
    })
    summary.index.name = "ozellik"
    print("Sayısal özet:")
    print(summary.round(4).to_string())
    return summary


def safe_name(value: str) -> str:
    """Sabit özellik adlarından güvenli dosya adı üret."""
    return re.sub(r"[^a-z0-9_]+", "_", value.lower())


def plot_distributions(data: pd.DataFrame) -> None:
    """Her özellik için histogram ve yatay kutu grafiği kaydet."""
    for feature, (label, unit) in FEATURES.items():
        values = data[feature]
        fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), layout="constrained")
        axes[0].hist(values, bins="auto", color="#3572A5", edgecolor="white")
        axes[0].set(title=f"{label} — histogram", xlabel=unit, ylabel="İl sayısı")
        axes[1].boxplot(values, vert=False, patch_artist=True,
                        boxprops={"facecolor": "#8CB6D9"}, medianprops={"color": "#9A3412"})
        axes[1].set(title=f"{label} — kutu grafiği", xlabel=unit, yticks=[])
        fig.savefig(GRAPHS / f"{safe_name(feature)}_dagilim.png", bbox_inches="tight")
        plt.close(fig)
        print(f"Grafik kaydedildi: {feature} (81 il)")


def correlations(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, list[tuple[str, str, float, float]]]:
    """Pearson/Spearman matrislerini ve yüksek korelasyonlu çiftleri döndür."""
    values = data[list(FEATURES)]
    pearson = values.corr(method="pearson")
    spearman = values.corr(method="spearman")
    pairs = []
    keys = list(FEATURES)
    for i, left in enumerate(keys):
        for right in keys[i + 1:]:
            p, s = float(pearson.loc[left, right]), float(spearman.loc[left, right])
            if abs(p) >= CORRELATION_LIMIT or abs(s) >= CORRELATION_LIMIT:
                pairs.append((left, right, p, s))
    print(f"Yüksek korelasyonlu çift sayısı (|r| ≥ {CORRELATION_LIMIT}): {len(pairs)}")
    for left, right, p, s in pairs:
        print(f"  {left} / {right}: Pearson={p:.3f}, Spearman={s:.3f}")
    return pearson, spearman, pairs


def plot_heatmap(matrix: pd.DataFrame, method: str) -> None:
    """Korelasyon ısı haritasını ek paket gerektirmeden Matplotlib ile üret."""
    labels = [FEATURES[key][0] for key in matrix.index]
    fig, ax = plt.subplots(figsize=(10, 8), layout="constrained")
    image = ax.imshow(matrix.to_numpy(), cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(len(labels)), labels, rotation=40, ha="right")
    ax.set_yticks(range(len(labels)), labels)
    for i in range(len(labels)):
        for j in range(len(labels)):
            value = matrix.iloc[i, j]
            ax.text(j, i, f"{value:.2f}", ha="center", va="center",
                    color="white" if abs(value) > 0.6 else "black")
    ax.set_title(f"{method} korelasyon ısı haritası")
    fig.colorbar(image, ax=ax, label="Korelasyon katsayısı")
    fig.savefig(GRAPHS / f"{method.lower()}_isi_haritasi.png", bbox_inches="tight")
    plt.close(fig)


def find_outliers(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """IQR sınırları dışındaki il/değer çiftlerini aday olarak işaretle."""
    rows, bounds = [], []
    for feature in FEATURES:
        q1, q3 = data[feature].quantile([0.25, 0.75])
        iqr = q3 - q1
        low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        selection = data.loc[(data[feature] < low) | (data[feature] > high),
                             ["il_kodu", "il_adi", feature]]
        bounds.append({"ozellik": feature, "q1": q1, "q3": q3,
                       "alt_sinir": low, "ust_sinir": high, "aday_sayisi": len(selection)})
        for _, item in selection.iterrows():
            value = float(item[feature])
            rows.append({"ozellik": feature, "il_kodu": int(item["il_kodu"]),
                         "il_adi": item["il_adi"], "deger": value,
                         "yon": "alt" if value < low else "üst",
                         "alt_sinir": low, "ust_sinir": high})
        print(f"IQR {feature}: {len(selection)} aykırı değer adayı / 81 il")
    detail = pd.DataFrame(rows, columns=["ozellik", "il_kodu", "il_adi", "deger",
                                         "yon", "alt_sinir", "ust_sinir"])
    return detail, pd.DataFrame(bounds)


def markdown_table(frame: pd.DataFrame, digits: int = 4) -> list[str]:
    """Küçük veri tablolarını Markdown'a dönüştür; tabulate bağımlılığı gerekmez."""
    table = frame.copy()
    for column in table.select_dtypes(include="number").columns:
        table[column] = table[column].map(lambda value: f"{value:.{digits}f}" if pd.notna(value) else "")
    columns = list(table.columns)
    lines = ["| " + " | ".join(map(str, columns)) + " |",
             "|" + "|".join("---" for _ in columns) + "|"]
    for row in table.itertuples(index=False, name=None):
        lines.append("| " + " | ".join(str(value).replace("|", "\\|") for value in row) + " |")
    return lines


def write_report(data: pd.DataFrame, summary: pd.DataFrame, pearson: pd.DataFrame,
                 spearman: pd.DataFrame, pairs: list[tuple[str, str, float, float]],
                 outliers: pd.DataFrame, bounds: pd.DataFrame) -> None:
    """Bulguları ve henüz karar verilmemiş özellik seçeneklerini açıkla."""
    text = ["# TÜİK 2024 il verileri — EDA ve özellik incelemesi", "",
            f"Kaynak: `{SOURCE.relative_to(ROOT)}`. Kapsam: {len(data)} il, "
            f"{len(data.columns)} sütun. Veri dönüştürülmedi ve model eğitilmedi.", "",
            "## Genel veri kontrolü", "",
            "- İl kodları 1–81 arasında benzersizdir.",
            "- Seçilen sayısal özelliklerde eksik veya sonlu olmayan değer yoktur.",
            "- Her özellik 81 il için hesaplandı.", "",
            "## Özet istatistikler", "",
            *markdown_table(summary.reset_index()), "",
            "## Korelasyon", "",
            f"Yüksek korelasyon eşiği: mutlak Pearson veya Spearman katsayısı ≥ {CORRELATION_LIMIT:.2f}.", ""]
    if pairs:
        pair_frame = pd.DataFrame(pairs, columns=["özellik_1", "özellik_2", "Pearson", "Spearman"])
        text.extend(markdown_table(pair_frame))
    else:
        text.append("Bu eşiği aşan özellik çifti yok.")
    labor = ["isgucune_katilma_orani", "issizlik_orani", "istihdam_orani"]
    text += ["", "### İşgücü göstergeleri", "",
             "Katılım, işsizlik ve istihdam oranları aynı işgücü yapısının bağlantılı ölçüleridir. "
             "Üçünü birlikte kullanmak ayrıntıyı koruyabilir; özellikle katılım ve istihdam yüksek "
             "korelasyonluysa uzaklık temelli kümelemede benzer bilgiyi iki kez ağırlıklandırabilir. "
             "Nihai seçim, sonraki aşamada farklı özellik kümeleri karşılaştırılarak yapılmalıdır.", "",
             *markdown_table(pearson.loc[labor, labor].reset_index().rename(columns={"index": "özellik"})), "",
             "## Dağılım ve çarpıklık", ""]
    for feature in ["kisi_basi_gsyh_tl", "nufus_yogunlugu"]:
        skew = float(summary.loc[feature, "carpiklik"])
        state = "belirgin çarpık" if abs(skew) >= SKEW_LIMIT else "belirgin çarpık değil"
        text.append(f"- {FEATURES[feature][0]}: çarpıklık {skew:.3f}; |çarpıklık| ≥ "
                    f"{SKEW_LIMIT:.1f} ölçütüne göre {state}.")
    text += ["", "## IQR aykırı değer adayları", "",
             "Sınırlar Q1 − 1,5×IQR ve Q3 + 1,5×IQR'dir. Bu işaretler veri hatası "
             "kanıtı değildir; GSYH ve nüfus yoğunluğundaki uç iller gerçek farklılıkları yansıtabilir.", "",
             *markdown_table(bounds[["ozellik", "alt_sinir", "ust_sinir", "aday_sayisi"]]), ""]
    if outliers.empty:
        text.append("Aykırı değer adayı bulunmadı.")
    else:
        for feature in FEATURES:
            selected = outliers.loc[outliers.ozellik == feature,
                                    ["il_adi", "deger", "yon"]]
            text += [f"### {FEATURES[feature][0]} ({len(selected)} aday)", ""]
            text += markdown_table(selected.rename(columns={"il_adi": "İl", "deger": "Değer", "yon": "Yön"})) if len(selected) else ["Aday yok."]
            text.append("")
    text += ["## Özellik değerlendirmesi", "",
             "- **Üç işgücü göstergesi gerekli mi?** Bu aşamada karar verilmedi. "
             "Yukarıdaki korelasyonlar ve göstergeler arasındaki matematiksel ilişki, "
             "birlikte kullanımın işgücüne fazla ağırlık verebileceğini gösterir.",
             "- **Ölçekleme:** TL, yüzde, yıl ve kişi/km² birimleri farklı büyüklüktedir. "
             "StandardScaler ortalama ve standart sapmayı kullanır; uç değerler bu ölçüleri etkileyebilir. "
             "RobustScaler medyan ve çeyrekler arası aralığı kullanır; çok çarpık dağılımlarda ve uç "
             "değerlerde karşılaştırılmaya değerdir. Bu betik iki yöntemi de uygulamaz.",
             "- **Birlikte kullanım:** Katılım ve istihdam gibi yüksek korelasyonlu ölçüler aynı "
             "boyutun ağırlığını artırabilir. GSYH ve yoğunluk da ayrı ayrı incelemeye değerdir. "
             "Hiçbir özellik silinmedi; nihai özellik seçimi yapılmadı.", "",
             "## Çıktılar", "",
             "Özet istatistikler, Pearson ve Spearman korelasyon CSV'leri, IQR aday tablosu "
             "ve `grafikler/` altındaki altı dağılım grafiği ile iki ısı haritası birlikte incelenmelidir.", ""]
    (OUTPUT / "eda_raporu.md").write_text("\n".join(text), encoding="utf-8")


def main() -> None:
    configure_fonts()
    data = load_and_check()  # Geçersiz kaynakta hiçbir EDA çıktısı yazılmaz.
    summary = summarize(data)
    pearson, spearman, pairs = correlations(data)
    outliers, bounds = find_outliers(data)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    GRAPHS.mkdir(parents=True, exist_ok=True)
    summary.to_csv(OUTPUT / "ozet_istatistikler.csv", encoding="utf-8-sig")
    pearson.to_csv(OUTPUT / "pearson_korelasyon.csv", encoding="utf-8-sig")
    spearman.to_csv(OUTPUT / "spearman_korelasyon.csv", encoding="utf-8-sig")
    outliers.to_csv(OUTPUT / "aykiri_degerler.csv", index=False, encoding="utf-8-sig")
    plot_distributions(data)
    plot_heatmap(pearson, "Pearson")
    plot_heatmap(spearman, "Spearman")
    write_report(data, summary, pearson, spearman, pairs, outliers, bounds)
    print(f"EDA tamamlandı. Çıktılar: {OUTPUT}")


if __name__ == "__main__":
    main()
