# training_pipeline/trainer.py
from __future__ import annotations

import numpy as np
import warnings
from typing import Dict, Any, Tuple

from sklearn.exceptions import ConvergenceWarning
try:
    from lightgbm.basic import LightGBMError
except Exception:  # pragma: no cover - LightGBM may be optional
    class LightGBMError(Exception):
        pass

# 靜音部分無關緊要的警告，保留你原有輸出風格
warnings.filterwarnings("ignore", category=ConvergenceWarning)


class Trainer:
    """
    訓練器：逐一訓練 models dict 內的模型。
    - 保留原有印出格式與語氣。
    - 全程不改你的互動方式與 CLI。
    """

    def __init__(self) -> None:
        pass

    # ===================== Public API =====================
    def train(self, models: Dict[str, Any], X, y) -> Dict[str, Any]:
        fitted = {}
        for name, est in models.items():
            print(f"🏋️  訓練模型：{name}")
            fitted[name] = self._fit_one(name, est, X, y)
        return fitted

    # ===================== Internal Helpers =====================
    def _fit_one(self, name: str, est, X, y):
        """
        - 統一先做資料健檢與清理（對所有模型一致）。
        """
        X_pre, y_clean = self._sanitize_xy(X, y)
        return self._fit_silent(est, X_pre, y_clean)

    def _fit_silent(self, est, X, y):
        # 維持 sklearn 風格，避免雜訊輸出
        try:
            est.fit(X, y)
            return est
        except LightGBMError:
            if hasattr(est, "set_params"):
                try:
                    print("⚠️  LightGBM GPU 失敗，改用 CPU 重新訓練。")
                    est.set_params(device_type="cpu")
                    est.fit(X, y)
                    return est
                except LightGBMError:
                    pass
            raise


    # ===================== Data Sanitation =====================
    def _sanitize_xy(self, X, y) -> Tuple[np.ndarray, np.ndarray]:
        """
        - 轉為 float32 / int64（視 y 而定）
        - 將 inf / -inf 轉為 nan，再以 0.0 填補
        - 刪除全常數欄（對 LGB/XGB 等是安全的；不影響你下游互動）
        - 保留輸出與互動風格，不額外打印
        """
        # 轉為 ndarray
        Xv = X.values if hasattr(X, "values") else X
        yv = y.values if hasattr(y, "values") else y

        Xv = np.asarray(Xv)
        yv = np.asarray(yv)

        # dtype 處理
        if Xv.dtype != np.float32:
            Xv = Xv.astype(np.float32, copy=False)

        # 無窮值 -> NaN -> 0
        Xv[~np.isfinite(Xv)] = np.nan
        # 若整列皆 NaN，LightGBM 會自行忽略；這裡統一填 0，避免分箱全空
        nan_mask = np.isnan(Xv)
        if nan_mask.any():
            Xv[nan_mask] = 0.0

        # 刪除全常數欄（防資訊洩漏；同時減少分裂異常）
        if Xv.ndim == 2:
            col_max = np.nanmax(Xv, axis=0)
            col_min = np.nanmin(Xv, axis=0)
            const_cols = (col_max == col_min)
            if const_cols.any():
                Xv = Xv[:, ~const_cols]

        # y 型別
        if not np.issubdtype(yv.dtype, np.integer):
            # 多數分類標籤可安全轉 int64
            try:
                yv = yv.astype(np.int64, copy=False)
            except Exception:
                # 若不可轉，保留原 dtype
                pass

        return Xv, yv
 