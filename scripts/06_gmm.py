"""GMM bileşen araştırması ve onaylanan 3 bileşenli nihai sonuç.

Çalıştırma: python scripts/06_gmm.py
Nihai 3 bileşen, araştırma sonuçları kullanıcıya sunulup onaylandıktan sonra eklendi.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import joblib
from sklearn.metrics import silhouette_score
from sklearn.mixture import GaussianMixture


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "outputs" / "preprocessing" / "iller_olceklendirilmis.csv"
ORIGINAL = ROOT / "outputs" / "tuik_2024_81_il_birlesik.csv"
OUTPUT = ROOT / "outputs" / "gmm"
IDENTIFIERS = ["il_kodu", "il_adi"]
FEATURES = [
    "kisi_basi_gsyh_tl",
    "issizlik_orani",
    "istihdam_orani",
    "ortalama_egitim_suresi",
    "nufus_yogunlugu",
]
COMPONENTS = range(2, 11)
RANDOM_STATE = 42
N_INIT = 10
MAX_ITER = 500
REG_COVAR = 1e-6
COVARIANCE_TYPE = "full"
FINAL_COMPONENTS = 3


def read_data() -> pd.DataFrame:
    """K-Means ve DBSCAN ile aynı 81 il ve beş özelliği doğrula."""
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


def explore(data: pd.DataFrame) -> pd.DataFrame:
    """2–10 bileşen için BIC, AIC, Silhouette ve küme büyüklüklerini ölç."""
    values = data[FEATURES].to_numpy(dtype=float)
    records = []
    for components in COMPONENTS:
        model = GaussianMixture(
            n_components=components,
            covariance_type=COVARIANCE_TYPE,
            random_state=RANDOM_STATE,
            n_init=N_INIT,
            max_iter=MAX_ITER,
            reg_covar=REG_COVAR,
        )
        labels = model.fit_predict(values)
        if not model.converged_:
            raise RuntimeError(f"{components} bileşenli GMM yakınsamadı")
        if len(labels) != 81:
            raise ValueError(f"{components} bileşenli GMM eksik il döndürdü")
        counts = np.bincount(labels, minlength=components)
        nonempty = int(np.count_nonzero(counts))
        if 2 <= nonempty < len(values):
            score = float(silhouette_score(values, labels))
            status = "Hesaplandı; 81 il dahil"
        else:
            score = np.nan
            status = "Hesaplanmadı; en az iki dolu küme yok"
        record = {
            "bilesen_sayisi": components,
            "bic": float(model.bic(values)),
            "aic": float(model.aic(values)),
            "silhouette_score": score,
            "silhouette_durumu": status,
            "dolu_kume_sayisi": nonempty,
            "en_kucuk_dolu_kume": int(counts[counts > 0].min()),
            "en_buyuk_kume": int(counts.max()),
            "tek_illi_kume_sayisi": int(np.sum(counts == 1)),
            "iki_uc_illi_kume_sayisi": int(np.sum((counts >= 2) & (counts <= 3))),
            "kume_buyuklukleri": ", ".join(map(str, counts.tolist())),
            "yakinsama_adimi": int(model.n_iter_),
        }
        if not np.isfinite(record["bic"]) or not np.isfinite(record["aic"]):
            raise ValueError(f"{components} bileşende BIC/AIC geçersiz")
        records.append(record)
        score_text = "hesaplanmadı" if np.isnan(score) else f"{score:.4f}"
        print(f"Bileşen={components:2d} | BIC={record['bic']:9.2f} | "
              f"AIC={record['aic']:9.2f} | Silhouette={score_text} | "
              f"Küme büyüklükleri: {counts.tolist()} (toplam {counts.sum()} il)")
    return pd.DataFrame.from_records(records)


def plot_criteria(results: pd.DataFrame) -> None:
    """BIC ve AIC eğrilerini aynı bileşen ekseninde göster."""
    plt.rcParams["font.family"] = "DejaVu Sans"
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(results["bilesen_sayisi"], results["bic"], marker="o", label="BIC")
    ax.plot(results["bilesen_sayisi"], results["aic"], marker="s", label="AIC")
    ax.set_xticks(list(COMPONENTS))
    ax.set_xlabel("Bileşen sayısı")
    ax.set_ylabel("Bilgi ölçütü (düşük daha iyi)")
    ax.set_title("GMM: BIC ve AIC")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUTPUT / "bic_aic.png", dpi=160)
    plt.close(fig)


def plot_silhouette(results: pd.DataFrame) -> None:
    """Silhouette değerlerini ayrı grafikte göster."""
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(results["bilesen_sayisi"], results["silhouette_score"], marker="o")
    ax.set_xticks(list(COMPONENTS))
    ax.set_xlabel("Bileşen sayısı")
    ax.set_ylabel("Silhouette Score (yüksek daha iyi)")
    ax.set_title("GMM: Silhouette ve bileşen sayısı")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUTPUT / "silhouette.png", dpi=160)
    plt.close(fig)


def build_report(results: pd.DataFrame) -> str:
    """Araştırma yöntemi, sonuçları ve önerinin gerekçesini açıkla."""
    lines = [
        "# GMM bileşen sayısı araştırması", "",
        "## Veri ve yöntem", "",
        "Girdi: `outputs/preprocessing/iller_olceklendirilmis.csv`; 81 il ve "
        "beş StandardScaler ile ölçeklendirilmiş özellik. İl kodu ve adı "
        "model girdisine alınmadı. 2–10 bileşen ayrı ayrı denendi. "
        f"`random_state={RANDOM_STATE}`, `n_init={N_INIT}`, "
        f"`max_iter={MAX_ITER}`, `reg_covar={REG_COVAR}`, "
        f"`covariance_type={COVARIANCE_TYPE}` kullanıldı. Her denemede "
        "yakınsama kontrol edildi.", "",
        "GMM, her ili olasılıksal olarak Gauss bileşenleriyle açıklar. "
        "BIC ve AIC modelin veriye uyumunu ve karmaşıklığını birlikte "
        "değerlendirir; ikisinde de **daha düşük** değer tercih edilir. "
        "`logL` 81 ilin toplam log-olasılığı, `p` modelin serbest "
        "parametre sayısı, `n=81` olmak üzere "
        "`BIC=-2×logL+p×ln(n)` ve `AIC=-2×logL+2p` hesaplanır. "
        "BIC, ek parametreleri AIC'den daha güçlü cezalandırır. "
        "Silhouette, en yüksek üyelik olasılığına göre atanmış etiketlerin "
        "uzaklık temelli ayrışmasını ölçer; **daha yüksek** değer tercih "
        "edilir. Bu ölçüler farklı soruları yanıtladığı için sonuçları "
        "birlikte yorumlamak gerekir.", "",
        "Silhouette, en az iki dolu küme olduğunda 81 ilin tamamı "
        "üzerinden hesaplandı. Tek veya çok küçük kümeler, yüksek skora "
        "rağmen yorumun kararsız olabileceğini gösterir. Buradaki "
        "`kume_buyuklukleri` değerleri yalnız araştırma içindir; nihai "
        "il etiketleri veya üyelik olasılıkları henüz kaydedilmedi.", "",
        "## Deneme sonuçları", "",
        "| Bileşen | BIC | AIC | Silhouette | Küme büyüklükleri | Tek illik küme |",
        "| ---: | ---: | ---: | ---: | --- | ---: |",
    ]
    for row in results.itertuples(index=False):
        score = "—" if pd.isna(row.silhouette_score) else f"{row.silhouette_score:.4f}"
        lines.append(f"| {row.bilesen_sayisi} | {row.bic:.2f} | {row.aic:.2f} | "
                     f"{score} | {row.kume_buyuklukleri} | "
                     f"{row.tek_illi_kume_sayisi} |")
    bic_best = results.loc[results["bic"].idxmin()]
    aic_best = results.loc[results["aic"].idxmin()]
    valid = results.dropna(subset=["silhouette_score"])
    lines += [
        "", "## İlk ölçüt özeti", "",
        f"En düşük BIC: {int(bic_best['bilesen_sayisi'])} bileşen "
        f"({bic_best['bic']:.2f}). En düşük AIC: "
        f"{int(aic_best['bilesen_sayisi'])} bileşen ({aic_best['aic']:.2f}).",
    ]
    if not valid.empty:
        silhouette_best = valid.loc[valid["silhouette_score"].idxmax()]
        lines.append(f"En yüksek Silhouette: "
                     f"{int(silhouette_best['bilesen_sayisi'])} bileşen "
                     f"({silhouette_best['silhouette_score']:.4f}).")
    row2 = results.loc[results["bilesen_sayisi"] == 2].iloc[0]
    row3 = results.loc[results["bilesen_sayisi"] == 3].iloc[0]
    row4 = results.loc[results["bilesen_sayisi"] == 4].iloc[0]
    row10 = results.loc[results["bilesen_sayisi"] == 10].iloc[0]
    lines += [
        "", "## Değerlendirme ve öneri", "",
        f"İki bileşende Silhouette en yüksek ({row2['silhouette_score']:.4f}); "
        f"ancak gruplar {row2['kume_buyuklukleri']} il olarak oldukça "
        "dengesiz. Bu çözüm ağırlıkla küçük bir ayrı grubu geri kalan "
        "illerden ayırır; daha ayrıntılı sosyoekonomik yapı vermez.", "",
        f"Üç bileşende BIC en düşük ({row3['bic']:.2f}). "
        f"Küme büyüklükleri {row3['kume_buyuklukleri']}; "
        f"Silhouette {row3['silhouette_score']:.4f}. Dört illik küçük "
        "grup ayrıca incelenmelidir, fakat tek illik grup yoktur. "
        f"Dört bileşende BIC {row4['bic']:.2f} düzeyine yükselir, "
        f"Silhouette {row4['silhouette_score']:.4f} düzeyine iner "
        "ve tek illik küme oluşur.", "",
        f"AIC on bileşene kadar düşerek {row10['aic']:.2f} değerine "
        "ulaşır. Buna karşılık on bileşende tek illik kümeler vardır ve "
        f"Silhouette {row10['silhouette_score']:.4f} olur. "
        "81 il için çok sayıda tam kovaryanslı bileşen, küçük gruplara "
        "aşırı uyum riski taşır; AIC'nin tek başına en düşük değerini "
        "nihai seçim saymıyoruz.", "",
        "**Öneri: 3 bileşen.** BIC bu noktada en düşük; iki bileşene "
        "göre daha açıklayıcı bir ayrım sağlar ve dört ve üstündeki "
        "tek illik/çok küçük grup sorunları henüz ağırlaşmamıştır. "
        "Bunun bir ön değerlendirme olduğu, dört illik grubun "
        "orijinal verilerle ve üyelik olasılıklarıyla incelenmesi gerektiği "
        "unutulmamalıdır. Farklı `covariance_type` seçenekleri bu "
        "aşamada eklenmedi; mevcut tam kovaryanslı çözümde öneri için "
        "yeterli karşılaştırma vardır.", "",
        "Üç bileşenli nihai GMM, bu araştırma ve kullanıcı onayından "
        "sonra `gmm_nihai_raporu.md` içinde ayrıca raporlanmıştır.", "",
    ]
    return "\n".join(lines)


def read_original(data: pd.DataFrame) -> pd.DataFrame:
    """Küme yorumları için ham TÜİK değerlerini kimlikle doğrula."""
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


def fit_final(data: pd.DataFrame, original: pd.DataFrame,
              research: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame,
                                                 pd.DataFrame, GaussianMixture, float]:
    """Onaylanan modeli uydur, üyelikleri ve ham ölçekli profilleri hesapla."""
    values = data[FEATURES].to_numpy(dtype=float)
    model = GaussianMixture(
        n_components=FINAL_COMPONENTS,
        covariance_type=COVARIANCE_TYPE,
        random_state=RANDOM_STATE,
        n_init=N_INIT,
        max_iter=MAX_ITER,
        reg_covar=REG_COVAR,
    )
    model.fit(values)
    if not model.converged_:
        raise RuntimeError("Nihai üç bileşenli GMM yakınsamadı")
    probabilities = model.predict_proba(values)
    labels = model.predict(values)
    if probabilities.shape != (81, FINAL_COMPONENTS):
        raise ValueError("Üyelik olasılığı tablosunun boyutu yanlış")
    if not np.isfinite(probabilities).all() or (probabilities < 0).any():
        raise ValueError("Üyelik olasılıklarında geçersiz değer var")
    if not np.allclose(probabilities.sum(axis=1), 1.0, atol=1e-10):
        raise ValueError("Her ilin üyelik olasılıkları toplamı 1 değil")
    if not np.array_equal(labels, np.argmax(probabilities, axis=1)):
        raise ValueError("Küme etiketi en yüksek olasılıkla uyuşmuyor")
    sizes = np.bincount(labels, minlength=FINAL_COMPONENTS)
    if sizes.sum() != 81 or np.any(sizes == 0):
        raise ValueError("Nihai modelde boş küme veya eksik il var")
    score = float(silhouette_score(values, labels))
    research_row = research.loc[research["bilesen_sayisi"] == FINAL_COMPONENTS].iloc[0]
    for actual, expected, name in [
        (float(model.bic(values)), float(research_row["bic"]), "BIC"),
        (float(model.aic(values)), float(research_row["aic"]), "AIC"),
        (score, float(research_row["silhouette_score"]), "Silhouette"),
    ]:
        if not np.isclose(actual, expected, atol=1e-7):
            raise ValueError(f"Nihai {name}, araştırma sonucuyla uyuşmuyor")
    if sizes.tolist() != [int(x) for x in research_row["kume_buyuklukleri"].split(", ")]:
        raise ValueError("Nihai küme büyüklükleri araştırmayla uyuşmuyor")

    assignments = data[IDENTIFIERS].copy()
    assignments["kume"] = labels
    assignments["atanma_olasiligi"] = probabilities.max(axis=1)
    probability_table = assignments[IDENTIFIERS + ["kume"]].copy()
    for number in range(FINAL_COMPONENTS):
        probability_table[f"olasilik_kume_{number}"] = probabilities[:, number]
    probability_table["atanma_olasiligi"] = probabilities.max(axis=1)
    raw = original[IDENTIFIERS + FEATURES].copy()
    raw["kume"] = labels
    profiles = raw.groupby("kume", sort=True)[FEATURES].mean().reset_index()
    profiles.insert(1, "il_sayisi", sizes)
    component_means = pd.DataFrame(model.means_, columns=FEATURES)
    component_means.insert(0, "kume", range(FINAL_COMPONENTS))
    print(f"Nihai GMM: {FINAL_COMPONENTS} bileşen; "
          f"küme büyüklükleri {sizes.tolist()}; Silhouette={score:.4f}.")
    for cluster in range(FINAL_COMPONENTS):
        cities = assignments.loc[assignments["kume"] == cluster, "il_adi"].tolist()
        print(f"Küme {cluster} ({len(cities)} il): {', '.join(cities)}")
    return assignments, probability_table, profiles, component_means, model, score


def build_final_report(assignments: pd.DataFrame, probabilities: pd.DataFrame,
                       profiles: pd.DataFrame, component_means: pd.DataFrame,
                       score: float, research: pd.DataFrame) -> str:
    """Seçim, hesaplama, üyelik belirsizliği ve orijinal profilleri açıkla."""
    row2 = research.loc[research["bilesen_sayisi"] == 2].iloc[0]
    row3 = research.loc[research["bilesen_sayisi"] == 3].iloc[0]
    row4 = research.loc[research["bilesen_sayisi"] == 4].iloc[0]
    row10 = research.loc[research["bilesen_sayisi"] == 10].iloc[0]
    low_confidence = probabilities.nsmallest(10, "atanma_olasiligi")
    p0 = profiles.loc[profiles["kume"] == 0].iloc[0]
    p1 = profiles.loc[profiles["kume"] == 1].iloc[0]
    p2 = profiles.loc[profiles["kume"] == 2].iloc[0]
    lines = [
        "# Nihai GMM raporu — 3 bileşen", "",
        "## 1. Veri ve hazırlık", "",
        "Girdi `outputs/preprocessing/iller_olceklendirilmis.csv`: 81 ilin "
        "beş StandardScaler ile ölçeklendirilmiş özelliği. "
        + ", ".join(f"`{name}`" for name in FEATURES) + ". "
        "`il_kodu` ve `il_adi` model girdisi değildir; yalnız il sonuçlarını "
        "kaynakla eşleştirmek için kullanıldı. Eksik/sonsuz değer ve tekrar "
        "eden il kodu kontrol edildi. Kümelerin sosyoekonomik yorumu için "
        "orijinal birleşik TÜİK verisi ayrıca okundu ve il sırası doğrulandı.", "",
        "## 2. Bileşen sayısı nasıl araştırıldı?", "",
        "2–10 arası dokuz tam kovaryanslı GMM denendi. Her modelde "
        f"`random_state={RANDOM_STATE}`, `n_init={N_INIT}`, "
        f"`max_iter={MAX_ITER}`, `reg_covar={REG_COVAR}` kullanıldı. "
        "`n_init=10` farklı başlangıçlar dener; yakınsama kontrol edildi. "
        "Her modelin BIC, AIC ve en yüksek üyelik olasılığına göre "
        "atanan etiketlerin Silhouette değeri hesaplandı. BIC/AIC için "
        "düşük, Silhouette için yüksek değer tercih edilir. "
        "`logL` toplam log-olasılık, `p` serbest parametre sayısı ve "
        "`n=81` iken `BIC=-2×logL+p×ln(n)`, `AIC=-2×logL+2p`. "
        "Tam tarama `bilesen_arastirmasi.csv` ve "
        "`bilesen_arastirmasi_raporu.md` içindedir.", "",
        "## 3. Neden 3 bileşen seçildi?", "",
        f"İki bileşende BIC {row2['bic']:.2f}, Silhouette "
        f"{row2['silhouette_score']:.4f}; kümeler "
        f"{row2['kume_buyuklukleri']} il. Silhouette en yüksek olsa da "
        "çoğu il tek grupta kalır. "
        f"Üç bileşende BIC **{row3['bic']:.2f}** ile en düşük; "
        f"kümeler {row3['kume_buyuklukleri']} il ve Silhouette "
        f"{row3['silhouette_score']:.4f}. "
        f"Dört bileşende BIC {row4['bic']:.2f} seviyesine yükselir, "
        "tek illik küme oluşur. "
        f"AIC on bileşende {row10['aic']:.2f} ile en düşük olsa da "
        "çok küçük/tek illik gruplar artar ve Silhouette düşer. "
        "Bu nedenle BIC, ayrımın yorumlanabilirliği ve küçük küme "
        "riskini birlikte değerlendirerek kullanıcı onayıyla 3 bileşen "
        "seçildi. Dört illik küme yine de dikkatle incelenmelidir.", "",
        "## 4. Nihai model nasıl hesaplandı?", "",
        "Aynı ayarlarla 3 bileşenli GMM yeniden uyduruldu. Model, "
        "her il için üç bileşene ait posterior üyelik olasılığını "
        "hesapladı. Her olasılık 0–1 arasındadır ve bir ilin üç "
        "olasılığı toplamı 1'dir. En yüksek olasılığa sahip bileşen "
        "ilin `kume` etiketi oldu. Nihai BIC, AIC, Silhouette ve "
        "küme büyüklükleri araştırmadaki 3 bileşen sonucuyla "
        "karşılaştırılıp doğrulandı.", "",
        f"Nihai BIC **{row3['bic']:.2f}**, "
        f"AIC **{row3['aic']:.2f}**, "
        f"Silhouette **{score:.4f}**. Silhouette 81 ilin tamamını kapsar. "
        "Küme numaraları gelişmişlik sırası belirtmez.", "",
        "## 5. Küme illeri", "",
    ]
    for cluster in range(FINAL_COMPONENTS):
        part = assignments.loc[assignments["kume"] == cluster]
        lines += [f"### Küme {cluster} — {len(part)} il", "",
                  ", ".join(part["il_adi"].tolist()) + ".", ""]
    lines += [
        "## 6. Orijinal TÜİK değerleriyle küme profilleri", "",
        "Aşağıdaki ortalamalar ölçeklendirilmiş sayılardan değil, "
        "orijinal TÜİK değerlerinden hesaplandı. GSYH TL, işsizlik ve "
        "istihdam %, eğitim yıl, yoğunluk kişi/km² birimindedir.", "",
        "| Küme | İl sayısı | GSYH (TL) | İşsizlik (%) | İstihdam (%) | "
        "Eğitim (yıl) | Yoğunluk (kişi/km²) |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in profiles.itertuples(index=False, name=None):
        lines.append(f"| {row[0]} | {row[1]} | "
                     + " | ".join(f"{value:,.2f}" for value in row[2:]) + " |")
    lines += ["", "Küme ortalamaları her ilin aynı özellikleri taşıdığı "
              "anlamına gelmez. Dört illik kümenin ortalaması az sayıda "
              "ile dayandığı için özellikle dikkatli yorumlanmalıdır.", "",
              "### Sayısal yorum", "",
              f"Küme 0'da ortalama kişi başına GSYH {p0['kisi_basi_gsyh_tl']:,.0f} TL, "
              f"işsizlik %{p0['issizlik_orani']:.2f} ve istihdam "
              f"%{p0['istihdam_orani']:.2f}. Küme 1'de GSYH "
              f"{p1['kisi_basi_gsyh_tl']:,.0f} TL ile daha düşük; işsizlik "
              f"%{p1['issizlik_orani']:.2f} ile "
              f"{p1['issizlik_orani']-p0['issizlik_orani']:.2f} yüzde puan "
              f"daha yüksek, istihdam %{p1['istihdam_orani']:.2f} ile "
              f"{p0['istihdam_orani']-p1['istihdam_orani']:.2f} yüzde puan "
              "daha düşük. Bu farklar ortalama profilleri gösterir; "
              "nedensel bir ilişki veya her il için geçerli bir kural değildir.", "",
              f"Ankara, İstanbul, İzmir ve Kocaeli'den oluşan Küme 2'de "
              f"ortalama GSYH {p2['kisi_basi_gsyh_tl']:,.0f} TL, eğitim "
              f"{p2['ortalama_egitim_suresi']:.2f} yıl. Bu iki ortalama "
              "diğer kümelerden yüksektir. Ortalama nüfus yoğunluğu "
              f"{p2['nufus_yogunlugu']:,.0f} kişi/km² olsa da İstanbul'un "
              "çok yüksek yoğunluğu dört illik ortalamayı güçlü biçimde "
              "etkiler; dört ilin aynı derecede yoğun olduğu sonucuna "
              "varılmamalıdır.", "",
              "## 7. Üyelik olasılıkları ve belirsizlik", "",
              "GMM, sert etiketin yanında her ilin üç bileşene ait "
              "olasılıklarını verir. `atanma_olasiligi`, bu üç değerin "
              "en yükseğidir. Yüksek değer modelin bu il için daha net "
              "atama yaptığını gösterir; gerçek dünyada kesinlik veya "
              "nedensellik kanıtı değildir. En düşük atanma olasılığına "
        "sahip on il (tabloda `0.000` görünen olasılıklar üç "
        "ondalığa yuvarlanmıştır):", "",
              "| İl | Atanan küme | Küme 0 | Küme 1 | Küme 2 | En yüksek |",
              "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for row in low_confidence.itertuples(index=False):
        lines.append(f"| {row.il_adi} | {row.kume} | "
                     f"{row.olasilik_kume_0:.3f} | {row.olasilik_kume_1:.3f} | "
                     f"{row.olasilik_kume_2:.3f} | {row.atanma_olasiligi:.3f} |")
    lines += [
        "", f"0,80'in altında en yüksek üyelik olasılığı olan il sayısı: "
        f"{int((probabilities['atanma_olasiligi'] < 0.80).sum())}. "
        f"0,60'ın altında: "
        f"{int((probabilities['atanma_olasiligi'] < 0.60).sum())}. "
        "Tüm 81 ilin olasılıkları `uyelik_olasiliklari.csv` içindedir.", "",
        "## 8. Bileşen ortalamaları ve sınırlamalar", "",
        "Aşağıdaki değerler modelin ölçekli uzaydaki Gauss bileşen "
        "ortalamalarıdır; sert atanmış illerin basit aritmetik "
        "ortalamalarından farklı olabilir.", "",
        "| Küme | " + " | ".join(FEATURES) + " |",
        "| ---: | " + " | ".join("---:" for _ in FEATURES) + " |",
    ]
    for row in component_means.itertuples(index=False, name=None):
        lines.append("| " + str(row[0]) + " | "
                     + " | ".join(f"{value:.3f}" for value in row[1:]) + " |")
    lines += [
        "", "GMM olasılıkları seçilen üç bileşenli tam kovaryans modeline "
        "bağlıdır. 81 gözlem ve küçük bir küme varken olasılıklar "
        "fazla kesin görünebilir. K-Means ve DBSCAN ile farklı "
        "kümelerin oluşması algoritmaların varsayımlarından kaynaklanabilir; "
        "nihai karşılaştırma sonraki aşamada yapılacaktır. "
        "Bu aşamada PCA veya t-SNE uygulanmadı.", "",
    ]
    return "\n".join(lines)


def main() -> None:
    data = read_data()
    results = explore(data)
    original = read_original(data)
    assignments, probabilities, profiles, component_means, model, score = fit_final(
        data, original, results
    )
    OUTPUT.mkdir(parents=True, exist_ok=True)
    results.to_csv(OUTPUT / "bilesen_arastirmasi.csv", index=False, encoding="utf-8-sig")
    plot_criteria(results)
    plot_silhouette(results)
    (OUTPUT / "bilesen_arastirmasi_raporu.md").write_text(
        build_report(results), encoding="utf-8"
    )
    assignments.to_csv(OUTPUT / "iller_gmm.csv", index=False, encoding="utf-8-sig")
    probabilities.to_csv(OUTPUT / "uyelik_olasiliklari.csv", index=False,
                         encoding="utf-8-sig")
    profiles.to_csv(OUTPUT / "kume_profilleri_orijinal.csv", index=False,
                    encoding="utf-8-sig")
    component_means.to_csv(OUTPUT / "bilesen_ortalamalari_olcekli.csv", index=False,
                           encoding="utf-8-sig")
    joblib.dump(model, OUTPUT / "gmm_modeli.joblib")
    (OUTPUT / "gmm_nihai_raporu.md").write_text(
        build_final_report(assignments, probabilities, profiles,
                           component_means, score, results),
        encoding="utf-8",
    )
    print(f"GMM aşaması tamamlandı. Çıktılar: {OUTPUT}")
    print("PCA, t-SNE veya sonraki aşamalar çalıştırılmadı.")


if __name__ == "__main__":
    main()
