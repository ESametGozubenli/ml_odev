"""DBSCAN parametre araştırması ve onaylanan nihai il kümeleri.

Çalıştırma: python scripts/05_dbscan.py
Nihai parametreler araştırma sonuçları kullanıcıya sunulup onaylandıktan sonra eklendi.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
from sklearn.metrics import silhouette_score
from sklearn.neighbors import NearestNeighbors


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "outputs" / "preprocessing" / "iller_olceklendirilmis.csv"
ORIGINAL = ROOT / "outputs" / "tuik_2024_81_il_birlesik.csv"
OUTPUT = ROOT / "outputs" / "dbscan"
IDENTIFIERS = ["il_kodu", "il_adi"]
FEATURES = [
    "kisi_basi_gsyh_tl",
    "issizlik_orani",
    "istihdam_orani",
    "ortalama_egitim_suresi",
    "nufus_yogunlugu",
]
MIN_SAMPLES_VALUES = (3, 4, 5, 7)
EPS_QUANTILES = (0.50, 0.60, 0.70, 0.80, 0.90, 0.95)
FINAL_MIN_SAMPLES = 4
FINAL_EPS = 1.1286768001156766  # min_samples=4 k-distance dağılımının %70 yüzdeliği


def read_data() -> pd.DataFrame:
    """K-Means ile aynı 81 il ve beş özellikli girdiyi doğrula."""
    if not SOURCE.is_file():
        raise FileNotFoundError(f"Ölçeklenmiş veri bulunamadı: {SOURCE}")
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
    print("Veri doğrulandı: 81 il, 5 ölçekli özellik; il kodu ve adı modele alınmıyor.")
    return data


def k_distances(values: np.ndarray, min_samples: int) -> np.ndarray:
    """Her ilin kendisi dahil min_samples'inci komşusuna uzaklığını bul."""
    neighbors = NearestNeighbors(n_neighbors=min_samples, metric="euclidean")
    neighbors.fit(values)
    distances, _ = neighbors.kneighbors(values)
    result = np.sort(distances[:, -1])
    if not np.isfinite(result).all():
        raise ValueError("k-distance hesabında geçersiz değer var")
    return result


def plot_k_distance(distances: np.ndarray, min_samples: int) -> None:
    """Sıralı komşu uzaklıklarını ve denenmiş eps yüzdeliklerini göster."""
    plt.rcParams["font.family"] = "DejaVu Sans"
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(range(1, len(distances) + 1), distances, linewidth=2)
    for quantile in EPS_QUANTILES:
        if quantile in (0.70, 0.90):
            value = float(np.quantile(distances, quantile))
            ax.axhline(value, linestyle="--", alpha=0.7,
                       label=f"%{int(quantile * 100)}: eps≈{value:.2f}")
    ax.set_xlabel("Sıralı il sayısı")
    ax.set_ylabel(f"{min_samples}. en yakın komşu uzaklığı")
    ax.set_title(f"DBSCAN k-distance grafiği (min_samples={min_samples})")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUTPUT / f"k_distance_min_samples_{min_samples}.png", dpi=160)
    plt.close(fig)


def evaluate(values: np.ndarray, eps: float, min_samples: int,
             quantile: float) -> dict:
    """Gürültüyü ayrı tutarak küme sayısı ve uygun Silhouette skorunu hesapla."""
    labels = DBSCAN(eps=eps, min_samples=min_samples, metric="euclidean").fit_predict(values)
    noise_mask = labels == -1
    noise_count = int(noise_mask.sum())
    cluster_labels, counts = np.unique(labels[~noise_mask], return_counts=True)
    cluster_count = len(cluster_labels)
    kept_count = len(values) - noise_count
    if cluster_count >= 2 and kept_count > cluster_count:
        score = float(silhouette_score(values[~noise_mask], labels[~noise_mask]))
        score_status = "Hesaplandı; gürültü hariç"
    else:
        score = np.nan
        score_status = "Hesaplanmadı; en az 2 uygun küme yok"
    return {
        "min_samples": min_samples,
        "eps_yuzdelik": int(quantile * 100),
        "eps": eps,
        "kume_sayisi": cluster_count,
        "gurultu_il_sayisi": noise_count,
        "gurultu_orani_yuzde": noise_count / len(values) * 100,
        "kume_ici_il_sayisi": kept_count,
        "en_kucuk_kume": int(counts.min()) if cluster_count else 0,
        "en_buyuk_kume": int(counts.max()) if cluster_count else 0,
        "kume_buyuklukleri": ", ".join(map(str, counts.tolist())),
        "silhouette_gurultu_haric": score,
        "silhouette_durumu": score_status,
    }


def build_report(results: pd.DataFrame) -> str:
    """Yöntemi, ölçüm kapsamını ve tüm denemeleri Türkçe kaydet."""
    candidate = results.loc[(results["min_samples"] == 4) &
                            (results["eps_yuzdelik"] == 70)].iloc[0]
    high_score = results.loc[(results["min_samples"] == 4) &
                             (results["eps_yuzdelik"] == 60)].iloc[0]
    lines = [
        "# DBSCAN parametre araştırması", "",
        "Girdi: `outputs/preprocessing/iller_olceklendirilmis.csv`; 81 il ve "
        "beş StandardScaler ile ölçekli özellik. İl kodu ve adı modele verilmedi. "
        "Uzaklık ölçüsü Öklid uzaklığıdır.", "",
        "**eps**, bir noktanın komşusu sayılabilecek noktalar için en büyük "
        "uzaklıktır. **min_samples**, bir noktanın çekirdek nokta sayılması "
        "için eps çevresinde (kendisi dahil) bulunması gereken en az nokta sayısıdır. "
        "Kümeye bağlanamayan iller `-1` etiketiyle gürültü olarak işaretlenir.", "",
        "Her `min_samples` değeri için illerin kendileri dahil ilgili sıradaki en "
        "yakın komşuya uzaklıkları sıralanıp k-distance grafiği çizildi. "
        "eps adayları bu uzaklıkların %50, %60, %70, %80, %90 ve %95 yüzdeliklerinden "
        "alındı. Yüzdelikler otomatik nihai karar değildir; grafikteki eğim, "
        "küme yapısı ve gürültü oranı birlikte yorumlanmalıdır.", "",
        "Silhouette yalnızca **gürültü dışındaki** illerde en az iki küme "
        "oluştuğunda hesaplandı. Gürültü illeri bu skorun paydasında yer almaz. "
        "Bu skor K-Means veya gürültüyü dahil eden bir skorla doğrudan "
        "eşdeğer değildir. Tek küme oluştuğunda skor boş bırakıldı.", "",
        "| min_samples | eps yüzdelik | eps | Küme | Gürültü | Gürültü % | "
        "Küme büyüklükleri | Silhouette (gürültü hariç) |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |",
    ]
    for row in results.itertuples(index=False):
        score = "—" if pd.isna(row.silhouette_gurultu_haric) else f"{row.silhouette_gurultu_haric:.4f}"
        lines.append(f"| {row.min_samples} | %{row.eps_yuzdelik} | {row.eps:.4f} | "
                     f"{row.kume_sayisi} | {row.gurultu_il_sayisi} | "
                     f"{row.gurultu_orani_yuzde:.1f} | {row.kume_buyuklukleri or '—'} | "
                     f"{score} |")
    lines += [
        "", "## Ön değerlendirme", "",
        f"Öneri adayı `min_samples=4`, `eps={candidate['eps']:.4f}`: "
        f"{candidate['kume_sayisi']} küme ({candidate['kume_buyuklukleri']} il), "
        f"{candidate['gurultu_il_sayisi']} gürültü il (%{candidate['gurultu_orani_yuzde']:.1f}) "
        f"ve gürültü hariç Silhouette {candidate['silhouette_gurultu_haric']:.4f}. "
        "Bu çözüm de dengesizdir; küçük küme yalnız dört il içerir.", "",
        f"`min_samples=4`, `eps={high_score['eps']:.4f}` denemesinde "
        f"Silhouette daha yüksek ({high_score['silhouette_gurultu_haric']:.4f}), "
        f"ancak {high_score['gurultu_il_sayisi']} il (%{high_score['gurultu_orani_yuzde']:.1f}) "
        "gürültü olur. Bu nedenle en yüksek skoru tek başına seçmek uygun değildir. "
        "min_samples=5 ve 7 denemelerinde tek küme oluştu. Grafikte "
        "kesin bir kırılma yok; son birkaç ilin uzaklığı hızla yükseliyor. "
        "Parametre önerisi bu sınırlamalarla kullanıcı onayına sunulmalıdır.",
        "", "Bu aşamada nihai parametre, il bazında küme etiketi veya "
              "gürültü listesi üretilmedi. Parametre önerisi grafikler ve "
              "tablo incelendikten sonra kullanıcı onayına sunulacaktır.", "",
    ]
    return "\n".join(lines)


def read_original(data: pd.DataFrame) -> pd.DataFrame:
    """Küme yorumları için ham ölçekteki il değerlerini eşleştir."""
    if not ORIGINAL.is_file():
        raise FileNotFoundError(f"Orijinal TÜİK verisi bulunamadı: {ORIGINAL}")
    original = pd.read_csv(ORIGINAL, encoding="utf-8-sig")
    if len(original) != 81 or original.isna().any().any():
        raise ValueError("Orijinal veri 81 tam il içermiyor")
    if not original[IDENTIFIERS].equals(data[IDENTIFIERS]):
        raise ValueError("Ölçekli ve orijinal veride il kodu/adı/sırası uyuşmuyor")
    if not np.isfinite(original[FEATURES].to_numpy(dtype=float)).all():
        raise ValueError("Orijinal özelliklerde geçersiz sayısal değer var")
    return original


def fit_final(data: pd.DataFrame, original: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, float]:
    """Onaylanan parametrelerle etiket, gürültü ve ham ölçekli profilleri üret."""
    values = data[FEATURES].to_numpy(dtype=float)
    eps_from_graph = float(np.quantile(k_distances(values, FINAL_MIN_SAMPLES), 0.70))
    if not np.isclose(FINAL_EPS, eps_from_graph, rtol=0, atol=1e-10):
        raise ValueError("Onaylanan eps, k-distance %70 yüzdeliğiyle uyuşmuyor")
    model = DBSCAN(eps=FINAL_EPS, min_samples=FINAL_MIN_SAMPLES,
                   metric="euclidean")
    labels = model.fit_predict(values)
    noise_mask = labels == -1
    kept_mask = ~noise_mask
    cluster_labels, counts = np.unique(labels[kept_mask], return_counts=True)
    if len(labels) != 81 or len(cluster_labels) != 2 or counts.sum() + noise_mask.sum() != 81:
        raise ValueError("Nihai DBSCAN kapsamı araştırma sonucuyla uyuşmuyor")
    if sorted(counts.tolist()) != [4, 65] or int(noise_mask.sum()) != 12:
        raise ValueError("Nihai DBSCAN küme/gürültü sayıları araştırmayla uyuşmuyor")
    score = float(silhouette_score(values[kept_mask], labels[kept_mask]))
    if not np.isfinite(score):
        raise ValueError("Nihai Silhouette geçersiz")
    core_mask = np.zeros(len(data), dtype=bool)
    core_mask[model.core_sample_indices_] = True
    kinds = np.where(noise_mask, "gürültü", np.where(core_mask, "çekirdek", "sınır"))
    assignments = data[IDENTIFIERS].copy()
    assignments["kume"] = labels
    assignments["nokta_tipi"] = kinds
    raw = original[IDENTIFIERS + FEATURES].copy()
    raw["kume"] = labels
    profiles = raw.groupby("kume", sort=True)[FEATURES].mean().reset_index()
    sizes = raw.groupby("kume", sort=True).size().reset_index(name="il_sayisi")
    profiles.insert(1, "il_sayisi", sizes["il_sayisi"])
    print(f"Nihai DBSCAN: {len(cluster_labels)} küme {counts.tolist()}, "
          f"{int(noise_mask.sum())} gürültü il; Silhouette={score:.4f} "
          "(gürültü hariç).")
    for cluster in [-1, *cluster_labels.tolist()]:
        cities = assignments.loc[assignments["kume"] == cluster, "il_adi"].tolist()
        label = "Gürültü" if cluster == -1 else f"Küme {cluster}"
        print(f"{label} ({len(cities)} il): {', '.join(cities)}")
    return assignments, profiles, score


def build_final_report(assignments: pd.DataFrame, profiles: pd.DataFrame,
                       score: float, research: pd.DataFrame) -> str:
    """Parametre seçiminin nedenini ve sonuçların sınırlarını ayrıntılı anlat."""
    chosen = research.loc[(research["min_samples"] == FINAL_MIN_SAMPLES) &
                          (research["eps_yuzdelik"] == 70)].iloc[0]
    high = research.loc[(research["min_samples"] == 4) &
                        (research["eps_yuzdelik"] == 60)].iloc[0]
    comparison = research.loc[(research["min_samples"] == 3) &
                              (research["eps_yuzdelik"] == 80)].iloc[0]
    large = profiles.loc[profiles["kume"] == 0].iloc[0]
    small = profiles.loc[profiles["kume"] == 1].iloc[0]
    lines = [
        "# Nihai DBSCAN raporu", "",
        "## 1. Veri ve amaç", "",
        "K-Means ile aynı `outputs/preprocessing/iller_olceklendirilmis.csv` "
        "dosyasındaki 81 ilin beş StandardScaler ile ölçekli özelliği "
        "kullanıldı: " + ", ".join(f"`{name}`" for name in FEATURES) + ". "
        "`il_kodu` ve `il_adi` modele verilmedi. Amaç, birbirine yakın "
        "illerin yoğun bölgelerini ve bu bölgelerin dışında kalan illeri belirlemektir.", "",
        "## 2. Algoritma nasıl çalışıyor?", "",
        "DBSCAN burada beş boyutlu Öklid uzaklığını kullanır. `eps` bir ilin "
        "komşusu sayılabilecek en büyük uzaklığı belirler. `min_samples` "
        "ise bir ilin çekirdek nokta olabilmesi için kendisi dahil eps içinde "
        "bulunması gereken en az il sayısıdır. Çekirdeğe bağlanan fakat "
        "kendisi çekirdek olmayan iller sınır noktasıdır. Hiçbir kümeye "
        "bağlanamayan iller `-1` koduyla gürültü sayılır. Küme numaraları "
        "büyüklük veya gelişmişlik sırası değildir.", "",
        "## 3. Parametreler nasıl bulundu?", "",
        "Önce `min_samples=3, 4, 5, 7` değerleri denendi. Her birinde her "
        "ilin kendisi dahil ilgili sıradaki en yakın komşusuna uzaklığı "
        "hesaplandı ve küçükten büyüğe sıralanarak k-distance grafiği "
        "çizildi. Bu uzaklıkların %50, %60, %70, %80, %90 ve %95 "
        "yüzdelikleri eps adayı alındı: toplam 24 kombinasyon. Grafiklerde "
        "son illerin komşu uzaklıkları hızla yükseliyor; tek ve kesin bir "
        "kırılma noktası yok. Bu nedenle eps yalnız grafiğe bakılarak seçilmedi.", "",
        "Her denemede küme sayısı, küme büyüklükleri, gürültü sayısı ve "
        "oranı hesaplandı. Gürültü dışında en az iki küme varsa Silhouette "
        "hesaplandı. `a`, bir ilin kendi kümesine ortalama uzaklığı; `b`, "
        "en yakın diğer kümeye ortalama uzaklığıdır. İl skoru "
        "`(b-a)/max(a,b)`; rapordaki değer yalnız **gürültü dışındaki** "
        "illerin ortalamasıdır. Tek küme varsa hesap yapılmadı.", "",
        "## 4. Neden bu parametreler seçildi?", "",
        f"Onaylanan `min_samples={FINAL_MIN_SAMPLES}`, "
        f"`eps={FINAL_EPS:.6f}` (%70 yüzdelik) çözümünde "
        f"{int(chosen['kume_sayisi'])} küme ({chosen['kume_buyuklukleri']} il), "
        f"{int(chosen['gurultu_il_sayisi'])} gürültü il "
        f"(%{chosen['gurultu_orani_yuzde']:.1f}) ve gürültü hariç "
        f"Silhouette {chosen['silhouette_gurultu_haric']:.4f} oluştu.", "",
        f"`min_samples=4`, `eps={high['eps']:.4f}` çözümünün Silhouette "
        f"değeri daha yüksek ({high['silhouette_gurultu_haric']:.4f}), "
        f"fakat {int(high['gurultu_il_sayisi'])} il (%{high['gurultu_orani_yuzde']:.1f}) "
        "gürültüye ayrılıyor; değerlendirme yalnız 57 ili kapsıyor. "
        f"`min_samples=3`, `eps={comparison['eps']:.4f}` çözümünde "
        f"{int(comparison['gurultu_il_sayisi'])} gürültü il ve "
        f"{comparison['silhouette_gurultu_haric']:.4f} Silhouette var. "
        "`min_samples=5` ve `7` denemelerinin hepsi tek küme verdi. "
        "Seçilen çözüm en yüksek skor peşinde çok sayıda ili dışarıda "
        "bırakmak yerine küme ve gürültü kapsamı arasında daha ölçülü "
        "bir denge kurduğu için kullanıcı onayıyla nihai sonuç yapıldı.", "",
        "## 5. Sonuç ve il listeleri", "",
        f"Toplam 81 il: 69 il iki kümeye girdi, 12 il gürültü. "
        f"Silhouette **{score:.4f}**, yalnız bu 69 il üzerinden hesaplandı. "
        "Gürültü illeri değerin paydasında yoktur. Bu nedenle K-Means'in "
        "81 il üzerinden hesaplanan skoru ile doğrudan eşdeğer değildir.", "",
    ]
    for cluster in sorted(assignments["kume"].unique()):
        part = assignments.loc[assignments["kume"] == cluster]
        title = "Gürültü (-1)" if cluster == -1 else f"Küme {cluster}"
        counts = part["nokta_tipi"].value_counts()
        lines += [f"### {title} — {len(part)} il", "",
                  ", ".join(part["il_adi"].tolist()) + ".", ""]
        if cluster != -1:
            lines += [f"Çekirdek: {int(counts.get('çekirdek', 0))}; "
                      f"sınır: {int(counts.get('sınır', 0))}.", ""]
    lines += [
        "## 6. Kümelerin orijinal TÜİK değerleriyle profili", "",
        "Aşağıdaki ortalamalar ölçekli CSV'den değil, "
        "`outputs/tuik_2024_81_il_birlesik.csv` dosyasından hesaplandı. "
        "GSYH TL, işsizlik ve istihdam %, eğitim yıl, yoğunluk kişi/km² "
        "birimindedir. Gürültü satırı, gürültü sayılan illerin kendi "
        "ortalamasıdır; ayrı bir küme değildir.", "",
        "| Grup | İl sayısı | GSYH (TL) | İşsizlik (%) | İstihdam (%) | "
        "Eğitim (yıl) | Yoğunluk (kişi/km²) |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in profiles.itertuples(index=False, name=None):
        group = "Gürültü (-1)" if row[0] == -1 else f"Küme {row[0]}"
        lines.append(f"| {group} | {row[1]} | "
                     + " | ".join(f"{value:,.2f}" for value in row[2:]) + " |")
    lines += [
        "", "## 7. Orijinal değerlerle yorum", "",
        f"Dört illik Küme 1'in ortalama kişi başına GSYH'si "
        f"{small['kisi_basi_gsyh_tl']:,.0f} TL; 65 illik Küme 0'da "
        f"{large['kisi_basi_gsyh_tl']:,.0f} TL. Aradaki fark yaklaşık "
        f"{large['kisi_basi_gsyh_tl'] - small['kisi_basi_gsyh_tl']:,.0f} TL. "
        f"Küme 1'de işsizlik ortalaması %{small['issizlik_orani']:.2f}, "
        f"Küme 0'da %{large['issizlik_orani']:.2f}; fark "
        f"{small['issizlik_orani'] - large['issizlik_orani']:.2f} yüzde puan. "
        f"İstihdam Küme 1'de %{small['istihdam_orani']:.2f}, "
        f"Küme 0'da %{large['istihdam_orani']:.2f}; Küme 1 "
        f"{large['istihdam_orani'] - small['istihdam_orani']:.2f} yüzde puan "
        "daha düşük. Ortalama eğitim süresi de Küme 1'de daha düşük "
        f"({small['ortalama_egitim_suresi']:.2f} ve "
        f"{large['ortalama_egitim_suresi']:.2f} yıl). "
        "Bu farklar kümelerin ortalama profilini anlatır; iller için "
        "nedensel bir açıklama veya gelişmişlik sıralaması değildir.", "",
        "Gürültü illeri farklı uç özellikler nedeniyle aynı etiketi alabilir. "
        "Örneğin İstanbul'un yüksek nüfus yoğunluğu bu grubun yoğunluk "
        "ortalamasını yükseltir; gürültü satırı tek tip bir sosyoekonomik "
        "küme gibi yorumlanmamalıdır.", "",
        "## 8. Sınırlamalar", "",
        "Küme ortalamaları bir gruptaki her ilin aynı olduğunu göstermez. "
        "Gürültü etiketi veri hatası veya önemsiz il demek değildir; "
        "bu eps ve min_samples ile yeterli yoğunluk bağlantısı kurulamadığını "
        "gösterir. Özellikle dört illik küçük küme ve gürültü oranı, "
        "parametre seçimine duyarlılık işaretidir. K-Means ile küme sayısı "
        "ve iller karşılaştırılabilir; Silhouette skorları farklı il "
        "kapsamları nedeniyle doğrudan sıralama için kullanılmamalıdır.", "",
        "İl bazında kümeler, gürültü ve çekirdek/sınır bilgisi "
        "`iller_dbscan.csv` dosyasında; sayısal profiller "
        "`kume_profilleri_orijinal.csv` dosyasındadır. Bu aşamada GMM, "
        "PCA veya t-SNE uygulanmadı.", "",
    ]
    return "\n".join(lines)


def main() -> None:
    data = read_data()
    original = read_original(data)
    values = data[FEATURES].to_numpy(dtype=float)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    records = []
    for min_samples in MIN_SAMPLES_VALUES:
        distances = k_distances(values, min_samples)
        plot_k_distance(distances, min_samples)
        print(f"min_samples={min_samples}: k-distance grafiği kaydedildi.")
        for quantile in EPS_QUANTILES:
            eps = float(np.quantile(distances, quantile))
            row = evaluate(values, eps, min_samples, quantile)
            records.append(row)
            score = row["silhouette_gurultu_haric"]
            score_text = "hesaplanmadı" if np.isnan(score) else f"{score:.4f}"
            print(f"min_samples={min_samples}, eps={eps:.4f} (%{row['eps_yuzdelik']}): "
                  f"{row['kume_sayisi']} küme, {row['gurultu_il_sayisi']} gürültü, "
                  f"Silhouette={score_text}")
    results = pd.DataFrame.from_records(records)
    results.to_csv(OUTPUT / "parametre_arastirmasi.csv", index=False, encoding="utf-8-sig")
    (OUTPUT / "parametre_arastirmasi_raporu.md").write_text(
        build_report(results), encoding="utf-8"
    )
    assignments, profiles, score = fit_final(data, original)
    assignments.to_csv(OUTPUT / "iller_dbscan.csv", index=False, encoding="utf-8-sig")
    profiles.to_csv(OUTPUT / "kume_profilleri_orijinal.csv", index=False,
                    encoding="utf-8-sig")
    (OUTPUT / "dbscan_nihai_raporu.md").write_text(
        build_final_report(assignments, profiles, score, results), encoding="utf-8"
    )
    print(f"DBSCAN aşaması tamamlandı. {len(results)} kombinasyon incelendi. "
          f"Çıktılar: {OUTPUT}")
    print("GMM veya sonraki aşamalar çalıştırılmadı.")


if __name__ == "__main__":
    main()
