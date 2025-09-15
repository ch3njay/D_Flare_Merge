"""Cisco ASA 模型推論與視覺化。"""
from __future__ import annotations

import os
from typing import Dict, Iterable, Tuple

import joblib
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.ticker import MaxNLocator

FONT_CANDIDATES = [
    "C:/Windows/Fonts/msjh.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/usr/share/fonts/truetype/arphic/uming.ttc",
]


def _ensure_font() -> None:
    """設定繁體中文字型，避免圖表顯示亂碼。"""
    for candidate in FONT_CANDIDATES:
        if os.path.exists(candidate):
            font_name = FontProperties(fname=candidate).get_name()
            plt.rcParams["font.family"] = font_name
            plt.rcParams["axes.unicode_minus"] = False
            plt.rcParams["figure.facecolor"] = "#fcfcfc"
            break


def _generate_bar(ax, labels: Iterable[str], values: Iterable[int], colors: Iterable[str]) -> None:
    """繪製帶數值標記的長條圖。"""
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.bar(labels, values, color=list(colors), edgecolor="#333", width=0.6)
    for index, value in enumerate(values):
        ax.text(index, value + 0.05, str(value), ha="center", va="bottom", fontsize=15)


def dflare_binary_predict(
    input_csv: str,
    binary_model_path: str,
    output_csv: str,
    output_pie: str,
    output_bar: str,
    feat_cols: Iterable[str] | None = None,
) -> Tuple[Dict[str, object], pd.DataFrame]:
    """執行二元模型預測並輸出圖表。"""
    _ensure_font()
    dataframe = pd.read_csv(input_csv, encoding="utf-8")
    model = joblib.load(binary_model_path)

    if hasattr(model, "feature_names_in_"):
        columns = list(model.feature_names_in_)
    elif feat_cols is not None:
        columns = list(feat_cols)
    else:  # pragma: no cover - 非預期模型格式
        raise RuntimeError("二元模型未包含特徵欄位資訊")

    df_model = dataframe.reindex(columns=columns, fill_value=-1).fillna(-1).astype(int)
    dataframe["is_attack"] = model.predict(df_model)
    dataframe.to_csv(output_csv, index=False, encoding="utf-8")

    distribution = dataframe["is_attack"].value_counts().sort_index().reindex([0, 1], fill_value=0)
    labels = ["正常流量", "攻擊流量"]
    colors = ["#ff9800", "#888888"]

    plt.figure(figsize=(6, 6))
    values = [distribution.iloc[i] for i in range(len(distribution)) if distribution.iloc[i] > 0]
    label_subset = [labels[i] for i in range(len(distribution)) if distribution.iloc[i] > 0]
    color_subset = [colors[i] for i in range(len(distribution)) if distribution.iloc[i] > 0]
    if not values:
        plt.text(0.5, 0.5, "無資料", fontsize=20, ha="center", va="center")
        plt.axis("off")
    elif len(values) == 1:
        plt.pie([1], labels=[label_subset[0]], colors=[color_subset[0]], autopct="%1.1f%%")
    else:
        plt.pie(values, labels=label_subset, colors=color_subset, autopct="%1.1f%%", startangle=90)
    plt.title("攻擊與正常流量比例（二元）", fontsize=18, pad=20)
    plt.tight_layout()
    plt.savefig(output_pie, bbox_inches="tight")
    plt.close()

    plt.figure(figsize=(7, 5))
    ax = plt.gca()
    _generate_bar(ax, labels, distribution, colors)
    plt.xlabel("流量類型", fontsize=15, labelpad=10)
    plt.ylabel("數量", fontsize=15, labelpad=10)
    plt.title("攻擊與正常流量數量分布（二元）", fontsize=18, pad=20)
    plt.tight_layout()
    plt.savefig(output_bar, bbox_inches="tight")
    plt.close()

    return (
        {
            "output_csv": output_csv,
            "output_pie": output_pie,
            "output_bar": output_bar,
            "is_attack_distribution": distribution.to_dict(),
            "count_all": int(dataframe.shape[0]),
            "count_attack": int(distribution[1]),
            "count_normal": int(distribution[0]),
        },
        dataframe,
    )


def dflare_multiclass_predict(
    df_attack: pd.DataFrame,
    multiclass_model_path: str,
    output_csv: str,
    output_pie: str,
    output_bar: str,
    feat_cols: Iterable[str] | None = None,
) -> Dict[str, object]:
    """針對攻擊流量執行多元分級模型。"""
    _ensure_font()
    model = joblib.load(multiclass_model_path)
    if hasattr(model, "feature_names_in_"):
        columns = list(model.feature_names_in_)
    elif feat_cols is not None:
        columns = list(feat_cols)
    else:  # pragma: no cover
        raise RuntimeError("多元模型未包含特徵欄位資訊")

    df_model = df_attack.reindex(columns=columns, fill_value=-1).fillna(-1).astype(int)
    df_attack["Severity"] = model.predict(df_model)
    df_attack.to_csv(output_csv, index=False, encoding="utf-8")

    severity_map = {1: "危險", 2: "高", 3: "中", 4: "低"}
    show_levels = [1, 2, 3, 4]
    colors = ["#ea3b3b", "#ffb300", "#29b6f6", "#7bd684"]
    distribution = df_attack["Severity"].value_counts().sort_index().reindex(show_levels, fill_value=0)

    plt.figure(figsize=(6, 6))
    values = [distribution[level] for level in show_levels if distribution[level] > 0]
    label_subset = [severity_map[level] for level in show_levels if distribution[level] > 0]
    color_subset = [colors[show_levels.index(level)] for level in show_levels if distribution[level] > 0]
    if not values:
        plt.text(0.5, 0.5, "無攻擊流量", fontsize=20, ha="center", va="center")
        plt.axis("off")
    elif len(values) == 1:
        plt.pie([1], labels=[label_subset[0]], colors=[color_subset[0]], autopct="%1.1f%%")
    else:
        plt.pie(values, labels=label_subset, colors=color_subset, autopct="%1.1f%%", startangle=90)
    plt.title("Severity 分布（僅針對攻擊流量）", fontsize=18, pad=20)
    plt.tight_layout()
    plt.savefig(output_pie, bbox_inches="tight")
    plt.close()

    plt.figure(figsize=(7, 5))
    ax = plt.gca()
    _generate_bar(ax, [severity_map[level] for level in show_levels], distribution, colors)
    plt.xlabel("Severity 等級（4 為最低，1 為最高）", fontsize=15, labelpad=10)
    plt.ylabel("數量", fontsize=15, labelpad=10)
    plt.title("Severity 分布（僅針對攻擊流量）", fontsize=18, pad=20)
    plt.tight_layout()
    plt.savefig(output_bar, bbox_inches="tight")
    plt.close()

    return {
        "output_csv": output_csv,
        "output_pie": output_pie,
        "output_bar": output_bar,
        "severity_distribution": distribution.to_dict(),
        "count_all": int(df_attack.shape[0]),
        "message": "多元分級結果已產生",
    }
