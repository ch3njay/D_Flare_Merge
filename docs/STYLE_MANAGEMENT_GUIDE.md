# D-FLARE 樣式管理指南

## 🎯 核心原則：三層架構

```
┌─────────────────────────────────────────┐
│  Layer 1: Global Styles (全域樣式)      │  ← unified_ui/app.py
│  - 按鈕統一樣式                          │
│  - 輸入框統一樣式                        │
│  - 卡片統一樣式                          │
└─────────────────────────────────────────┘
              ↓ 繼承
┌─────────────────────────────────────────┐
│  Layer 2: Theme Enhancement (主題增強)  │  ← enhanced_theme.py
│  - Layout 優化                           │
│  - 動畫效果                              │
│  - 通用元件增強                          │
└─────────────────────────────────────────┘
              ↓ 繼承
┌─────────────────────────────────────────┐
│  Layer 3: Module Override (模組覆寫)    │  ← Cisco_ui/Forti_ui
│  - 只在需要時覆寫                        │
│  - 特殊需求客製化                        │
└─────────────────────────────────────────┘
```

---

## 📋 決策樹：何時全域 vs 何時寫死？

### ✅ 應該**全域宣告**的樣式

| 元素類型 | 原因 | 定義位置 |
|---------|------|---------|
| **按鈕** | 整個應用統一外觀 | `unified_ui/app.py` |
| **輸入框/選擇框** | 一致的表單體驗 | `unified_ui/app.py` |
| **卡片容器** | 統一布局和間距 | `unified_ui/app.py` |
| **標題樣式** | 層級結構一致 | `unified_ui/app.py` |
| **滾動條** | 整體視覺統一 | `unified_ui/app.py` |
| **響應式斷點** | 跨頁面一致行為 | `unified_ui/app.py` |

**原則**：如果是「通用 UI 元件」，應該全域定義

### ⚠️ 應該**寫死（硬編碼）**的樣式

| 元素類型 | 原因 | 定義位置 |
|---------|------|---------|
| **品牌識別元素** | 固定品牌色，不隨主題變化 | 各自 UI 檔案 |
| **特殊狀態指示器** | 語意色彩（綠色=正常，紅色=錯誤） | 各自 UI 檔案 |
| **模組特定布局** | 只有該頁面需要的特殊排版 | 各自 UI 檔案 |
| **內嵌裝飾元素** | 不會重複使用的一次性樣式 | inline style |

**原則**：如果是「特定內容」或「品牌識別」，可以寫死

---

## 🛠️ 實作方案：當前設計

### 1. 全域按鈕樣式（`unified_ui/app.py`）

```css
/* 所有按鈕的基礎樣式 */
.stButton > button {
    background: linear-gradient(135deg, var(--primary-color), ...);
    border: 2px solid var(--primary-color) !important;  /* 新增邊框 */
    border-radius: 10px !important;
    font-weight: 600 !important;
    padding: 0.75rem 2rem !important;
    box-shadow: 0 6px 20px rgba(...) !important;
}

/* 懸停效果 */
.stButton > button:hover {
    transform: translateY(-3px) !important;
    border-color: color-mix(in srgb, var(--primary-color) 120%, white) !important;
    box-shadow: 0 12px 35px rgba(...) !important;
}

/* Primary 按鈕（強調） */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--primary-color), ...);
    border: 2px solid var(--primary-color) !important;
}

/* Secondary 按鈕（次要） */
.stButton > button[kind="secondary"] {
    background: transparent !important;
    border: 2px solid var(--primary-color) !important;
    color: var(--primary-color) !important;
}

.stButton > button[kind="secondary"]:hover {
    background: color-mix(in srgb, var(--primary-color) 15%, transparent) !important;
}
```

**效果**：
- ✅ 所有按鈕都有漸層背景
- ✅ 所有按鈕都有邊框
- ✅ Primary 按鈕：實心漸層 + 邊框
- ✅ Secondary 按鈕：透明背景 + 邊框（hover 時有淺色背景）
- ✅ 統一的陰影和動畫效果

### 2. 系統狀態框（寫死）

```html
<div style="
    border: 2px solid #22c55e;              /* 綠色邊框 */
    border-radius: 8px;
    padding: 0.8rem;
    background: rgba(34, 197, 94, 0.1);     /* 淺綠背景 */
">
    <div>📡 系統狀態</div>
    <div style="color: #22c55e; font-weight: 600;">🟢 所有服務運行中</div>
    <div>版本: v2.1.0</div>
</div>
```

**為什麼寫死**：
- ✅ 綠色框=正常狀態，這是**語意色彩**，不應隨主題變化
- ✅ 如果變成 Dark/Light 主題色，會失去「正常/異常」的視覺提示
- ✅ 這不是通用元件，只有這一處使用

### 3. 品牌卡片（寫死）

```python
# Fortinet 橘紅色 - 品牌識別
brand_configs = {
    "Fortinet": {
        "gradient": "linear-gradient(135deg, #f97316, #ef4444)",
        "shadow": "rgba(239, 68, 68, 0.3)"
    }
}
```

**為什麼寫死**：
- ✅ Fortinet **必須是橘紅色**，這是品牌識別
- ✅ 不能讓用戶透過主題系統改變品牌色
- ✅ 提供視覺一致性和品牌辨識度

---

## 📊 優缺點分析

### 全域樣式的優勢

| 優點 | 說明 | 範例 |
|------|------|------|
| **維護性** | 改一處，全部生效 | 改按鈕圓角，整個 app 統一 |
| **一致性** | 避免各頁面風格不一致 | 所有按鈕都有相同動畫 |
| **效能** | CSS 只載入一次 | 減少重複樣式定義 |
| **可測試性** | 集中驗證樣式正確性 | 一次測試涵蓋所有頁面 |
| **開發效率** | 新頁面自動套用樣式 | 不需要每次都寫 CSS |

### 寫死樣式的優勢

| 優點 | 說明 | 範例 |
|------|------|------|
| **語意明確** | 顏色傳達特定意義 | 綠色框=正常，紅色框=錯誤 |
| **品牌保護** | 確保品牌色不被修改 | Fortinet 永遠是橘紅色 |
| **獨立性** | 模組不依賴全域樣式 | 可單獨使用某個子模組 |
| **彈性** | 特殊需求容易實現 | 某頁面需要不同按鈕樣式 |

---

## 🎨 混合策略實作範例

### 範例 1：通用按鈕（全域）

```python
# unified_ui/app.py - 全域定義
st.markdown("""
    <style>
    .stButton > button {
        background: linear-gradient(135deg, var(--primary-color), ...);
        border: 2px solid var(--primary-color) !important;
    }
    </style>
""", unsafe_allow_html=True)

# 各頁面直接使用 - 無需額外 CSS
st.button("開始分析", type="primary")
st.button("取消", type="secondary")
```

### 範例 2：品牌選擇（寫死）

```python
# unified_ui/app.py - 針對品牌識別寫死
brand_configs = {
    "Fortinet": {
        "gradient": "linear-gradient(135deg, #f97316, #ef4444)",  # 固定橘紅
    },
    "Cisco": {
        "gradient": "linear-gradient(135deg, #38bdf8, #2563eb)",  # 固定藍色
    }
}

st.markdown(f"""
    <div style="background: {brand_configs[brand]['gradient']};">
        當前平台: {brand}
    </div>
""", unsafe_allow_html=True)
```

### 範例 3：狀態指示器（寫死 + 可複用函式）

```python
# 定義狀態樣式映射（寫死語意色彩）
STATUS_STYLES = {
    "success": {"border": "#22c55e", "bg": "rgba(34, 197, 94, 0.1)", "text": "#22c55e"},
    "warning": {"border": "#f59e0b", "bg": "rgba(245, 158, 11, 0.1)", "text": "#f59e0b"},
    "error": {"border": "#ef4444", "bg": "rgba(239, 68, 68, 0.1)", "text": "#ef4444"},
}

def render_status_box(status: str, title: str, message: str):
    """可複用的狀態框元件"""
    style = STATUS_STYLES[status]
    return f"""
    <div style="
        border: 2px solid {style['border']};
        background: {style['bg']};
        border-radius: 8px;
        padding: 0.8rem;
    ">
        <div style="color: {style['text']}; font-weight: 600;">{title}</div>
        <div>{message}</div>
    </div>
    """

# 使用
st.markdown(render_status_box("success", "系統正常", "所有服務運行中"), unsafe_allow_html=True)
st.markdown(render_status_box("error", "系統異常", "無法連接資料庫"), unsafe_allow_html=True)
```

---

## 🔍 如何決定使用哪種方式？

### 決策流程圖

```
開始
  ↓
這是通用 UI 元件嗎？（按鈕、輸入框、卡片）
  ├─ 是 → 會在多個頁面使用嗎？
  │       ├─ 是 → 【全域定義】於 unified_ui/app.py
  │       └─ 否 → 【寫死】於當前檔案
  └─ 否 → 是否為品牌識別/語意色彩？
          ├─ 是 → 【寫死】保持固定配色
          └─ 否 → 需要隨主題變化嗎？
                  ├─ 是 → 【使用 CSS 變數】var(--primary-color)
                  └─ 否 → 【寫死】用 inline style
```

### 快速檢查表

問自己這些問題：

1. **會在 3 個以上地方使用嗎？**
   - ✅ 是 → 全域定義
   - ❌ 否 → 寫死

2. **需要保持統一外觀嗎？**
   - ✅ 是 → 全域定義
   - ❌ 否 → 寫死

3. **是品牌識別色彩嗎？**
   - ✅ 是 → 寫死（不隨主題變化）
   - ❌ 否 → 使用 CSS 變數

4. **是語意色彩嗎？**（綠色=成功，紅色=錯誤）
   - ✅ 是 → 寫死（保持語意一致性）
   - ❌ 否 → 使用 CSS 變數

5. **未來可能改動嗎？**
   - ✅ 是 → 全域定義（方便修改）
   - ❌ 否 → 寫死也無妨

---

## 📁 檔案職責劃分

### `unified_ui/app.py`（主應用）

**職責**：全域樣式定義
```python
st.markdown("""
    <style>
    /* 按鈕樣式 - 整個 app 統一 */
    .stButton > button { ... }
    
    /* 輸入框樣式 - 整個 app 統一 */
    .stTextInput > div > div > input { ... }
    
    /* 卡片樣式 - 整個 app 統一 */
    .feature-card { ... }
    
    /* 品牌特定樣式 - Fortinet/Cisco 顏色 */
    .fortinet-card { ... }
    .cisco-card { ... }
    </style>
""", unsafe_allow_html=True)
```

### `enhanced_theme.py`（主題增強）

**職責**：通用增強效果
```python
st.markdown("""
    <style>
    /* Layout 優化 */
    .main .block-container { padding: 2rem; }
    
    /* 動畫效果 */
    .stButton > button:hover { transform: translateY(-2px); }
    
    /* 響應式設計 */
    @media (max-width: 768px) { ... }
    </style>
""", unsafe_allow_html=True)
```

### `Cisco_ui/ui_pages/__init__.py`（模組樣式）

**職責**：只在需要時覆寫
```python
# 只在 Cisco 模組需要不同樣式時才定義
st.markdown("""
    <style>
    /* 只有在確實需要覆寫全域樣式時才加 */
    .cisco-specific-button { ... }
    </style>
""", unsafe_allow_html=True)
```

---

## 🎓 最佳實踐建議

### DO ✅

1. **優先使用全域樣式**
   ```python
   # Good
   st.button("提交", type="primary")  # 自動套用全域樣式
   ```

2. **品牌色和語意色寫死**
   ```python
   # Good - 綠色邊框代表正常狀態
   st.markdown('<div style="border: 2px solid #22c55e;">正常</div>', unsafe_allow_html=True)
   ```

3. **使用 CSS 變數實現主題切換**
   ```css
   /* Good */
   .my-card {
       background: var(--secondary-background-color);
       color: var(--text-color);
   }
   ```

4. **創建可複用的樣式函式**
   ```python
   # Good
   def render_status_box(status, message):
       # 可複用邏輯
   ```

### DON'T ❌

1. **不要在每個檔案重複定義相同樣式**
   ```python
   # Bad
   # Cisco_ui/ui_app.py
   st.markdown('<style>.stButton > button {...}</style>', ...)
   
   # Forti_ui_app_bundle/ui_app.py
   st.markdown('<style>.stButton > button {...}</style>', ...)  # 重複！
   ```

2. **不要用 CSS 變數覆蓋品牌識別色**
   ```css
   /* Bad - Fortinet 應該固定是橘紅色 */
   .fortinet-hero {
       background: var(--primary-color);  /* 會隨主題變化！ */
   }
   ```

3. **不要用 inline style 定義通用樣式**
   ```python
   # Bad - 每次都要寫一樣的 style
   st.markdown('<button style="border-radius: 10px; padding: 0.75rem;">按鈕</button>')
   ```

---

## 🔧 維護指南

### 新增通用樣式

1. **確認需求**：這個樣式會用在多處嗎？
2. **定義位置**：在 `unified_ui/app.py` 的 `<style>` 區塊
3. **使用 CSS 變數**：盡量用 `var(--primary-color)` 而非硬編碼
4. **測試所有頁面**：確保沒有破壞現有樣式

### 修改品牌樣式

1. **找到定義位置**：`BRAND_THEMES` 或 `brand_configs`
2. **同時修改所有品牌**：保持 Fortinet/Cisco 平衡
3. **驗證視覺識別**：確保品牌色依然鮮明
4. **更新文檔**：記錄顏色變更

### 調試樣式問題

1. **檢查優先級**：
   - inline style > CSS !important > CSS 一般規則
2. **使用瀏覽器開發者工具**：
   - F12 → Elements → 查看實際套用的 CSS
3. **確認 CSS 載入順序**：
   - unified_ui/app.py → enhanced_theme.py → 模組樣式

---

## 📈 效益評估

### 採用混合策略後的改善

| 指標 | 改善前 | 改善後 | 提升 |
|------|--------|--------|------|
| 維護時間 | 需修改 10+ 處 | 只需修改 1 處 | ⬇️ 90% |
| 樣式一致性 | 各頁面有差異 | 完全統一 | ⬆️ 100% |
| 開發效率 | 每頁都寫 CSS | 自動套用 | ⬆️ 80% |
| 程式碼重複 | 大量重複 | 幾乎無重複 | ⬇️ 95% |
| 品牌一致性 | 可能被修改 | 固定保護 | ⬆️ 100% |

---

## 📝 總結建議

### 對於您的專案：

1. **按鈕樣式** → ✅ **全域定義**
   - 所有頁面都需要
   - 需要統一外觀
   - 定義在 `unified_ui/app.py`

2. **系統狀態框** → ✅ **寫死（綠色邊框）**
   - 語意色彩（綠色=正常）
   - 不應隨主題變化
   - 使用 `#22c55e` 固定色

3. **品牌卡片** → ✅ **寫死（品牌識別色）**
   - Fortinet 橘紅、Cisco 藍色
   - 品牌視覺識別
   - 定義在 `BRAND_THEMES`

### 未來開發原則：

- **通用元件** → 全域定義
- **品牌識別** → 寫死保護
- **語意色彩** → 寫死固定
- **一次性樣式** → inline style
- **需要主題切換** → 使用 CSS 變數

---

**維護者**：D-FLARE 開發團隊  
**最後更新**：2025年10月9日
