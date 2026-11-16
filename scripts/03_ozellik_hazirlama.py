"""TÜİK 2024 il verilerinden beş özellikli ölçeklenmiş veri üretir.

Elle çalıştırma: python scripts/03_ozellik_hazirlama.py
Kaynak ve EDA dosyaları yalnız okunur. Çıktılar outputs/preprocessing/ altındadır.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "outputs" / "tuik_2024_81_il_birlesik.csv"
OUTPUT = ROOT / "outputs" / "preprocessing"
CSV_PATH = OUTPUT / "iller_olceklendirilmis.csv"
SCALER_PATH = OUTPUT / "iller_olceklendirilmis_scaler.joblib"
METADATA_PATH = OUTPUT / "donusum_bilgileri.json"
REPORT_PATH = OUTPUT / "ozellik_hazirlama_raporu.md"

IDENTIFIERS = ["il_kodu", "il_adi"]
FEATURES = [
    "kisi_basi_gsyh_tl",
    "issizlik_orani",
    "istihdam_orani",
    "ortalama_egitim_suresi",
    "nufus_yogunlugu",
]
SOURCE_COLUMNS = [
    "il_kodu",
    "il_adi",
    "kisi_basi_gsyh_tl",
    "isgucune_katilma_orani",
    "issizlik_orani",
    "istihdam_orani",
    "ortalama_egitim_suresi",
    "nufus_yogunlugu",
]


def read_source() -> pd.DataFrame:
    """Kaynağı değiştirmeden oku ve 81 il ile beş özelliği doğrula."""
    if not SOURCE.is_file():
        raise FileNotFoundError(f"Kaynak veri bulunamadı: {SOURCE}")
    data = pd.read_csv(SOURCE, encoding="utf-8-sig")
    if list(data.columns) != SOURCE_COLUMNS:
        raise ValueError(f"Beklenmeyen kaynak sütunları: {list(data.columns)}")
    if len(data) != 81:
        raise ValueError(f"81 il bekleniyordu, {len(data)} satır bulundu")
    if data.isna().any().any():
        raise ValueError("Kaynak veride eksik değer var")
    if data["il_kodu"].duplicated().any() or set(data["il_kodu"]) != set(range(1, 82)):
        raise ValueError("İl kodları benzersiz 1–81 kümesini oluşturmuyor")
    if data["il_adi"].duplicated().any() or data["il_adi"].astype(str).str.strip().eq("").any():
        raise ValueError("İl adları boş veya tekrar ediyor")
    for feature in FEATURES:
        if not pd.api.types.is_numeric_dtype(data[feature]):
            raise TypeError(f"Sayısal olmayan özellik: {feature}")
        if not np.isfinite(data[feature].to_numpy(dtype=float)).all():
            raise ValueError(f"Geçersiz sayısal değer: {feature}")
    print(f"Kaynak doğrulandı: {len(data)} il, {len(data.columns)} sütun; eksik veya tekrar kayıt yok.")
    return data


def prepare(data: pd.DataFrame) -> tuple[pd.DataFrame, StandardScaler]:
    """Yalnızca seçilen beş özelliğe StandardScaler uygula."""
    scaler = StandardScaler()
    scaled = scaler.fit_transform(data.loc[:, FEATURES].copy(deep=True))
    if scaled.shape != (81, 5) or not np.isfinite(scaled).all():
        raise ValueError("Ölçekleme sonucu eksik, sonsuz veya yanlış boyutta değer içeriyor")
    result = pd.concat(
        [data.loc[:, IDENTIFIERS].reset_index(drop=True),
         pd.DataFrame(scaled, columns=FEATURES)],
        axis=1,
    )
    if not result[IDENTIFIERS].equals(data[IDENTIFIERS].reset_index(drop=True)):
        raise ValueError("İl kodu, adı veya sırası değişti")
    print("Beş özellik StandardScaler ile ölçeklendirildi; 81 ilin sırası korundu.")
    return result, scaler


def build_report(result: pd.DataFrame, scaler: StandardScaler, source_hash: str) -> str:
    """Özellik seçimi kararını ve ilk beş ilin örneğini raporla."""
    lines = [
        "# Özellik seçimi ve ölçeklendirme notu", "",
        "2024 TÜİK verisindeki 81 il için beş özellik kullanıldı: "
        + ", ".join(f"`{name}`" for name in FEATURES) + ".", "",
        "İşgücüne katılma oranı, istihdam oranıyla EDA'da yüksek Pearson "
        "korelasyonu (0,9708) gösterdiği için çıkarıldı. Böylece işgücü "
        "boyutunun kümelemede gereğinden fazla ağırlık taşıması azaltılmaya çalışıldı. "
        "Bu karar, en iyi modelin seçildiği anlamına gelmez.", "",
        "Beş özelliğin tümüne `StandardScaler` uygulandı: her değerden o "
        "özelliğin 81 ildeki ortalaması çıkarıldı ve sonuç standart sapmaya "
        "bölündü. Keşifsel, denetimsiz kümeleme için ölçekleyici 81 ilin "
        "tamamına uyduruldu; train/test ayrımı yapılmadı. Negatif sonuçlar "
        "hata değildir, ortalamanın altındaki değerleri gösterir.", "",
        "Kaynak veriler değiştirilmedi. Çıktıda 81 il, benzersiz il kodları ve "
        "aynı il sırası doğrulandı; eksik veya geçersiz değer oluşmadı. "
        "`il_kodu` ve `il_adi` yalnız tanımlama içindir, modele girdi olarak verilmemelidir.", "",
        f"Kaynak: `{SOURCE.relative_to(ROOT).as_posix()}`. SHA-256: `{source_hash}`.",
        f"Ölçekleyici: `{SCALER_PATH.relative_to(ROOT).as_posix()}`. "
        "Özellik sırası ve parametreler `donusum_bilgileri.json` içindedir. "
        "Yeni veri için aynı sırayla kaydedilmiş ölçekleyicinin `transform` "
        "yöntemi kullanılmalıdır; yeniden `fit` yapılmamalıdır.", "",
        "## Parametreler", "",
        "| Özellik | Ortalama | Standart sapma |",
        "| --- | ---: | ---: |",
    ]
    for name, mean, scale in zip(FEATURES, scaler.mean_, scaler.scale_):
        lines.append(f"| {name} | {mean:.8g} | {scale:.8g} |")
    lines += ["", "## İlk beş il", "",
              "| " + " | ".join(result.columns) + " |",
              "| " + " | ".join("---" for _ in result.columns) + " |"]
    for row in result.head(5).itertuples(index=False, name=None):
        values = [f"{item:.4f}" if isinstance(item, (float, np.floating)) else str(item)
                  for item in row]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines) + "\n"


def main() -> None:
    data = read_source()
    source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    result, scaler = prepare(data)
    metadata = {
        "source_file": SOURCE.relative_to(ROOT).as_posix(),
        "source_sha256": source_hash,
        "output_file": CSV_PATH.relative_to(ROOT).as_posix(),
        "row_count": len(result),
        "feature_count": len(FEATURES),
        "feature_order": FEATURES,
        "identifier_columns_not_for_model": IDENTIFIERS,
        "excluded_feature": "isgucune_katilma_orani",
        "transform_order": ["StandardScaler"],
        "scaler_class": "StandardScaler",
        "scaler_parameters_by_feature_order": {
            "mean": scaler.mean_.tolist(),
            "scale": scaler.scale_.tolist(),
            "variance": scaler.var_.tolist(),
        },
        "versions": {
            "pandas": pd.__version__, "numpy": np.__version__,
            "scikit_learn": sklearn.__version__,
        },
    }
    OUTPUT.mkdir(parents=True, exist_ok=True)
    result.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")
    joblib.dump(scaler, SCALER_PATH)
    METADATA_PATH.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_PATH.write_text(build_report(result, scaler, source_hash), encoding="utf-8")
    print(f"Hazır: {CSV_PATH} ({len(result)} il, {len(FEATURES)} özellik)")
    print(f"Ölçekleyici ve karar notu kaydedildi: {OUTPUT}")
    print("İl kodu ve il adı modele girdi değildir. Kümeleme yapılmadı.")


if __name__ == "__main__":
    main()
