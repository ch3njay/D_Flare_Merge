# 🚨 嚴重問題發現報告

## 日期：2025-10-09
## 檢查層級：CRITICAL

---

## ❌ 問題 1：Severity 標籤邏輯**嚴重衝突**

### 位置
- 檔案 1：`Cisco_ui/etl_pipeline/log_mapping.py` (第 41-45 行)
- 檔案 2：`Cisco_ui/etl_pipeline/cisco_log_parser.py` (第 107-115 行)

### 衝突內容

#### log_mapping.py（**錯誤的邏輯** ❌）
```python
def _is_attack_severity(value: object) -> int:
    """根據 Severity 欄位推論是否屬於攻擊流量。"""
    try:
        return 1 if int(str(value).strip()) <= 4 else 0  # ❌ 錯誤！
    except Exception:
        return 0
```

**問題：使用 `<= 4` 會導致 Severity 0 被標記為攻擊！**

#### cisco_log_parser.py（**正確的邏輯** ✅）
```python
# Severity 1-4: is_attack=1 (緊急/警告/錯誤)
# Severity 5-7: is_attack=0 (通知/資訊/除錯)
# Severity 0: 忽略（硬體問題）
severity_int = int(result["severity"])
if severity_int >= 1 and severity_int <= 4:  # ✅ 正確
    result["is_attack"] = 1
elif severity_int >= 5:
    result["is_attack"] = 0
```

### 影響範圍
- ⚠️ **高度嚴重**：`log_mapping.py` 被 `etl_pipeliner.py` 的 `step2_preprocess_data()` 調用
- ⚠️ 會影響所有使用 ETL Pipeline 的資料處理流程
- ⚠️ 可能導致訓練資料標籤錯誤，進而影響模型準確性

### 驗證測試案例

| Severity Level | log_mapping.py 結果 | cisco_log_parser.py 結果 | 正確結果 |
|---------------|-------------------|------------------------|---------|
| 0 | ❌ is_attack=1 | ✅ 過濾（不處理）| 過濾 |
| 1 | ✅ is_attack=1 | ✅ is_attack=1 | is_attack=1 |
| 2 | ✅ is_attack=1 | ✅ is_attack=1 | is_attack=1 |
| 3 | ✅ is_attack=1 | ✅ is_attack=1 | is_attack=1 |
| 4 | ✅ is_attack=1 | ✅ is_attack=1 | is_attack=1 |
| 5 | ❌ is_attack=0 | ✅ is_attack=0 | is_attack=0 |
| 6 | ❌ is_attack=0 | ✅ is_attack=0 | is_attack=0 |
| 7 | ❌ is_attack=0 | ✅ is_attack=0 | is_attack=0 |

### 修正方案
```python
def _is_attack_severity(value: object) -> int:
    """根據 Severity 欄位推論是否屬於攻擊流量。
    
    Cisco ASA Severity Level 標準：
    - Level 0: Emergencies (硬體問題，應過濾)
    - Level 1-4: Alert/Critical/Error/Warning (is_attack=1)
    - Level 5-7: Notification/Informational/Debugging (is_attack=0)
    """
    try:
        severity_int = int(str(value).strip())
        if severity_int >= 1 and severity_int <= 4:
            return 1
        elif severity_int >= 5 and severity_int <= 7:
            return 0
        else:  # severity_int == 0 或其他異常值
            return 0  # 預設為正常，由後續流程過濾
    except Exception:
        return 0
```

---

## ❌ 問題 2：單獨版本 STEP1 與新版本的欄位不一致

### 位置
- 檔案：`單獨版本Dflare_Cisco-main/STEP1_v3.2_process_logs.py`

### 問題描述
該檔案使用 **Forti 的欄位結構**（crscore, crlevel, subtype 等），與新版 Cisco ASA 的欄位不符：

#### STEP1 使用的欄位（Forti 格式）
```python
'date','time','subtype',
'srcip','srcport','srcintf',
'dstip','dstport','dstintf',
'action','sentpkt','rcvdpkt',
'duration','service','devtype','level',
'crscore','crlevel','is_attack','raw_log'
```

#### 新版 Cisco ASA 應使用的欄位
```python
'datetime','syslogid','severity',
'source_ip','source_port','source_intf',
'dest_ip','dest_port','dest_intf',
'action','protocol','bytes','duration',
'is_attack','raw_log'
```

### 影響範圍
- ⚠️ **中度嚴重**：單獨版本無法處理標準 Cisco ASA 格式
- ⚠️ 使用者可能混淆兩個版本的用途
- ⚠️ 維護成本高（需要同步更新兩套程式碼）

### 建議方案
1. **短期**：在 STEP1 檔案頂端加上明確警告，說明適用範圍
2. **中期**：修改 STEP1 支援雙格式自動偵測（Forti vs Cisco）
3. **長期**：統一到 Cisco_ui 框架下，廢棄單獨版本

---

## ⚠️ 問題 3：欄位名稱大小寫不一致

### 位置
多個檔案使用不同的大小寫規則：

| 欄位 | cisco_log_parser.py | log_mapping.py | utils.py (STANDARD_COLUMNS) |
|------|---------------------|----------------|---------------------------|
| 嚴重程度 | `severity` (小寫) | `Severity` (大寫) | `Severity` (大寫) |
| 來源 IP | `source_ip` (小寫+底線) | - | `SourceIP` (駝峰式) |
| 目的 IP | `dest_ip` (小寫+底線) | - | `DestinationIP` (駝峰式) |

### 影響範圍
- ⚠️ **中度嚴重**：可能導致欄位找不到或重複
- ⚠️ pandas 處理時需要額外的欄位名稱轉換邏輯

### 建議方案
統一使用**駝峰式大寫**（符合 STANDARD_COLUMNS 定義）：
```python
Severity, SourceIP, DestinationIP, SourcePort, DestinationPort
```

---

## ⚠️ 問題 4：crscore 與 crlevel 的誤用

### 位置
- `STEP1_v3.2_process_logs.py` 第 300-310 行

### 問題描述
```python
# 建立 is_attack 標籤
if "crscore" in df.columns:
    df["is_attack"] = (df["crscore"].astype(int) > 0).astype(int)
elif "crlevel" in df.columns:
    safe_vals = {"0", "unknown", "none", ""}
    df["is_attack"] = (~df["crlevel"].isin(safe_vals)).astype(int)
```

**問題**：Cisco ASA 不使用 crscore/crlevel，這是 Forti 的欄位！

### 影響範圍
- ⚠️ **中度嚴重**：使用 STEP1 處理 Cisco ASA 日誌會得到錯誤標籤
- ⚠️ 如果資料中沒有 crscore/crlevel，所有記錄的 is_attack 都會是 0

### 建議方案
```python
# 根據日誌格式自動偵測
if "severity" in df.columns:  # Cisco ASA
    df["is_attack"] = df["severity"].apply(
        lambda x: 1 if 1 <= int(x) <= 4 else 0
    )
elif "crscore" in df.columns:  # Forti
    df["is_attack"] = (df["crscore"].astype(int) > 0).astype(int)
elif "crlevel" in df.columns:  # Forti
    safe_vals = {"0", "unknown", "none", ""}
    df["is_attack"] = (~df["crlevel"].isin(safe_vals)).astype(int)
else:
    df["is_attack"] = 0
```

---

## ⚠️ 問題 5：特徵工程缺少 Severity 0 的過濾

### 位置
- `Cisco_ui/etl_pipeline/cisco_feature_engineering.py`

### 問題描述
特徵工程模組沒有檢查輸入資料是否已過濾 Severity 0，可能會對硬體問題日誌建立特徵。

### 影響範圍
- ⚠️ **低度嚴重**：可能產生無意義的特徵
- ⚠️ 增加資料雜訊

### 建議方案
在特徵工程開頭加入檢查：
```python
def create_cisco_features(df: pd.DataFrame) -> pd.DataFrame:
    """建立 Cisco ASA 專屬特徵。"""
    # 過濾 Severity 0
    if "Severity" in df.columns:
        original_count = len(df)
        df = df[df["Severity"] != 0].copy()
        filtered_count = original_count - len(df)
        if filtered_count > 0:
            print(f"⚠️ 已過濾 {filtered_count} 筆 Severity 0 記錄")
    
    # ... 繼續特徵工程
```

---

## 📊 優先級評估

| 問題 | 嚴重程度 | 影響範圍 | 修復優先級 |
|------|---------|---------|-----------|
| 問題 1：Severity 邏輯衝突 | 🔴 HIGH | 所有 ETL 流程 | **P0 - 立即修復** |
| 問題 2：STEP1 欄位不一致 | 🟡 MEDIUM | 單獨版本 | P1 - 優先修復 |
| 問題 3：大小寫不一致 | 🟡 MEDIUM | 資料處理 | P1 - 優先修復 |
| 問題 4：crscore/crlevel 誤用 | 🟡 MEDIUM | 單獨版本 | P1 - 優先修復 |
| 問題 5：Severity 0 未過濾 | 🟢 LOW | 特徵工程 | P2 - 後續改進 |

---

## 🔧 建議修復順序

### 第一階段（立即執行）
1. ✅ 修正 `log_mapping.py` 的 `_is_attack_severity()` 函式
2. ✅ 驗證修正後的邏輯（執行測試）

### 第二階段（優先執行）
3. ✅ 統一欄位名稱大小寫規則
4. ✅ 修正 STEP1 的標籤建立邏輯（支援 Cisco ASA）
5. ✅ 加入格式自動偵測機制

### 第三階段（後續改進）
6. ⭕ 在特徵工程加入 Severity 0 過濾
7. ⭕ 建立完整的端到端測試
8. ⭕ 統一文件和範例程式碼

---

## 📝 後續行動

- [ ] 建立自動化測試腳本，持續驗證 Severity 標籤邏輯
- [ ] 建立欄位名稱規範文件
- [ ] 為單獨版本和整合版本建立清晰的使用指南
- [ ] 定期執行交叉驗證，確保一致性

---

**報告建立時間**：2025-10-09  
**檢查人員**：GitHub Copilot  
**檢查範圍**：全系統嚴格驗證
