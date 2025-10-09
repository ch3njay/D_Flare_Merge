# D-FLARE 主題系統設計文檔

## 📋 概述

D-FLARE 統一控制台採用混合主題策略：
- **一般 UI 元素**：由 Streamlit 原生主題系統控制，支援 Light/Dark/Custom 切換
- **品牌識別元素**：使用固定品牌配色，保持視覺識別一致性

## 🎨 主題控制策略

### 1. Streamlit 原生主題控制（可切換）

透過 **Settings > Appearance** 切換，影響以下元素：

| UI 元素 | Light 模式 | Dark 模式 |
|---------|-----------|----------|
| 背景色 | ⚪ 淺色 | ⚫ 深色 (#0F1419) |
| 文字色 | ⚫ 深色 | ⚪ 淺色 (#E6E8EB) |
| 次要背景 | ⚪ 淺灰 | ⚫ 深灰 (#1A1F29) |
| 主色調 | 🟠 橘色 | 🟠 橘色 (#FF6B35) |
| 邊框色 | ⚫ 深灰 | ⚪ 淺灰 (#2D3748) |

**控制檔案**：`.streamlit/config.toml`

**影響範圍**：
- 側邊欄背景
- 主內容區背景
- 按鈕（使用 `var(--primary-color)`）
- 輸入框/選擇框
- 表格和圖表
- 一般文字和標題

### 2. 固定品牌配色（不隨主題變化）

為保持品牌識別，以下元素使用**硬編碼顏色**：

#### 🛡️ Fortinet 品牌元素

**英雄卡片漸層**：
```css
background: linear-gradient(135deg, #f97316, #ef4444);
box-shadow: 0 20px 40px -12px rgba(239, 68, 68, 0.45);
```

**側邊欄品牌選擇**：
```css
background: linear-gradient(135deg, #f97316, #ef4444);
box-shadow: 0 6px 20px rgba(239, 68, 68, 0.3);
```

**功能卡片頂部線條**：
```css
background: linear-gradient(90deg, #f97316, #ef4444, #dc2626, #fb923c);
```

**懸停光暈**：
```css
box-shadow: 0 20px 50px rgba(249, 115, 22, 0.4),
            0 0 40px rgba(239, 68, 68, 0.3);
```

#### 📡 Cisco 品牌元素

**英雄卡片漸層**：
```css
background: linear-gradient(135deg, #38bdf8, #2563eb);
box-shadow: 0 20px 40px -12px rgba(37, 99, 235, 0.45);
```

**側邊欄品牌選擇**：
```css
background: linear-gradient(135deg, #38bdf8, #2563eb);
box-shadow: 0 6px 20px rgba(37, 99, 235, 0.3);
```

**功能卡片頂部線條**：
```css
background: linear-gradient(90deg, #38bdf8, #3b82f6, #2563eb, #60a5fa);
```

**懸停光暈**：
```css
box-shadow: 0 20px 50px rgba(56, 189, 248, 0.4),
            0 0 40px rgba(59, 130, 246, 0.3);
```

## 🎯 設計理念

### 為什麼混合策略？

1. **品牌識別優先**：
   - Fortinet 必須是橘紅色
   - Cisco 必須是藍色
   - 這是品牌視覺識別的核心

2. **可讀性保證**：
   - 彩色背景上**必須使用白色文字**才有足夠對比度
   - 如果讓主題系統控制，Light 模式下會變成黑字配彩色背景 → 難以閱讀

3. **用戶體驗**：
   - 一般 UI 元素隨用戶偏好切換（Light/Dark）
   - 品牌元素保持固定，提供視覺錨點

## 📁 檔案結構

### 主題配置檔案

```
.streamlit/
  └── config.toml           # Streamlit 原生主題設定（可切換部分）

enhanced_theme.py          # 布局和動畫增強（不含顏色覆蓋）

unified_ui/
  └── app.py               # 包含品牌固定配色定義
      ├── BRAND_THEMES     # 英雄卡片品牌配色
      ├── brand_configs    # 側邊欄品牌選擇配色
      └── CSS styles       # 功能卡片品牌樣式
```

### 關鍵程式碼位置

**品牌英雄卡片配色**（`unified_ui/app.py` 第 95-118 行）：
```python
DEFAULT_THEME = {
    "start": "#6366f1",
    "end": "#8b5cf6",
    "shadow": "rgba(99, 102, 241, 0.45)",
    "icon": "🧭",
    "eyebrow": "Unified Threat Analytics",
}
BRAND_THEMES = {
    "Fortinet": {
        "start": "#f97316",
        "end": "#ef4444",
        "shadow": "rgba(239, 68, 68, 0.45)",
        "icon": "🛡️",
        "eyebrow": "Fortinet 安全平台",
    },
    "Cisco": {
        "start": "#38bdf8",
        "end": "#2563eb",
        "shadow": "rgba(37, 99, 235, 0.45)",
        "icon": "📡",
        "eyebrow": "Cisco 安全平台",
    },
}
```

**側邊欄品牌選擇配色**（`unified_ui/app.py` 第 1142-1157 行）：
```python
brand_configs = {
    "Fortinet": {
        "icon": "🛡️",
        "desc": "智慧威脅分析與 Fortinet 防火牆日誌處理平台",
        "gradient": "linear-gradient(135deg, #f97316, #ef4444)",
        "shadow": "rgba(239, 68, 68, 0.3)"
    },
    "Cisco": {
        "icon": "📡",
        "desc": "智慧威脅分析與 Cisco ASA 防火牆日誌處理平台",
        "gradient": "linear-gradient(135deg, #38bdf8, #2563eb)",
        "shadow": "rgba(37, 99, 235, 0.3)"
    }
}
```

**功能卡片品牌樣式**（`unified_ui/app.py` 第 208-277 行）：
```css
.feature-card::before {
    background: linear-gradient(90deg, #ec4899, #8b5cf6, #3b82f6, #06b6d4);
}

.fortinet-card::before {
    background: linear-gradient(90deg, #f97316, #ef4444, #dc2626, #fb923c);
}

.cisco-card::before {
    background: linear-gradient(90deg, #38bdf8, #3b82f6, #2563eb, #60a5fa);
}
```

## 🧪 測試指南

### 測試主題切換

1. 啟動應用程式：
   ```bash
   python launch_unified_dashboard.py
   ```

2. 開啟瀏覽器：http://localhost:8501

3. 測試 Light 模式：
   - 點擊 **⋮** > **Settings** > **Appearance** > **Light**
   - ✅ 背景應該變淺色
   - ✅ 文字應該變深色
   - ✅ **品牌卡片和側邊欄選擇保持彩色**（Fortinet 橘紅、Cisco 藍色）

4. 測試 Dark 模式：
   - 選擇 **Dark**
   - ✅ 背景應該變深色 (#0F1419)
   - ✅ 文字應該變淺色 (#E6E8EB)
   - ✅ **品牌卡片和側邊欄選擇保持彩色**

5. 測試 Custom 模式：
   - 選擇 **Custom**
   - ✅ 應該使用 `.streamlit/config.toml` 中的設定

### 視覺驗證檢查表

#### Fortinet 品牌
- [ ] 英雄卡片：橘紅漸層背景 + 白色文字
- [ ] 側邊欄選擇：橘紅漸層背景 + 白色文字
- [ ] 功能卡片：橘紅漸層頂部線條
- [ ] 懸停效果：橘紅色光暈陰影

#### Cisco 品牌
- [ ] 英雄卡片：青藍漸層背景 + 白色文字
- [ ] 側邊欄選擇：青藍漸層背景 + 白色文字
- [ ] 功能卡片：青藍漸層頂部線條
- [ ] 懸停效果：青藍色光暈陰影

#### 一般 UI（應隨主題變化）
- [ ] 主背景色
- [ ] 側邊欄背景色
- [ ] 文字顏色
- [ ] 按鈕基礎色（使用主題橘色 #FF6B35）
- [ ] 輸入框背景和邊框

## 🔧 修改指南

### 修改主題可切換部分

編輯 `.streamlit/config.toml`：
```toml
[theme]
primaryColor = "#FF6B35"        # 主色調（橘色）
backgroundColor = "#0F1419"     # 背景色
secondaryBackgroundColor = "#1A1F29"  # 次要背景
textColor = "#E6E8EB"           # 文字色
font = "sans serif"             # 字體
```

### 修改品牌固定配色

編輯 `unified_ui/app.py`：

1. **英雄卡片**：修改 `BRAND_THEMES` 字典（第 95-118 行）
2. **側邊欄選擇**：修改 `brand_configs` 字典（第 1142-1157 行）
3. **功能卡片**：修改 CSS 樣式（第 208-277 行）

⚠️ **注意**：品牌配色修改後，需要重新啟動應用程式才能生效。

## 📊 顏色參考

### Fortinet 品牌配色
- 主色：`#f97316` (橘色)
- 強調色：`#ef4444` (紅色)
- 深色：`#dc2626` (深紅)
- 淺色：`#fb923c` (淺橘)
- 陰影：`rgba(239, 68, 68, 0.3-0.45)`

### Cisco 品牌配色
- 主色：`#38bdf8` (青色)
- 強調色：`#3b82f6` (藍色)
- 深色：`#2563eb` (深藍)
- 淺色：`#60a5fa` (淺藍)
- 陰影：`rgba(37, 99, 235, 0.3-0.45)`

### 一般主題配色（可切換）
- 主色調：`#FF6B35` (D-FLARE 橘)
- Dark 背景：`#0F1419`
- Dark 次要背景：`#1A1F29`
- Dark 文字：`#E6E8EB`
- 邊框：`#2D3748`

## 🎓 最佳實踐

### DO ✅

1. **品牌識別元素**使用固定配色
2. **一般 UI 元素**使用 `var(--primary-color)` 等 CSS 變數
3. **彩色背景**上使用白色文字確保對比度
4. 使用 `color-mix()` 創建衍生顏色（如按鈕懸停效果）
5. 保持品牌配色在不同主題下的一致性

### DON'T ❌

1. 不要在品牌識別元素上使用 `var(--primary-color)`
2. 不要在一般 UI 元素上硬編碼顏色
3. 不要使用 `!important` 覆蓋主題系統（除非必要）
4. 不要在 Light 模式下使用深色背景配深色文字
5. 不要移除品牌英雄卡片的白色文字

## 📝 版本歷史

- **v2.1.0** (2025-10-09)：實作混合主題系統，支援 Light/Dark/Custom 切換，同時保持品牌識別
- **v2.0.0** (2025-10-09)：移除硬編碼顏色，遷移至 Streamlit 原生主題系統
- **v1.0.0** (初始版本)：完全硬編碼的深色主題

## 🤝 貢獻指南

修改主題系統時，請遵循以下原則：

1. **測試所有主題模式**：Light、Dark、Custom
2. **驗證品牌識別**：Fortinet 橘紅、Cisco 藍色必須保持
3. **檢查對比度**：確保文字在所有背景上可讀
4. **更新文檔**：修改配色時更新本文檔

---

**維護者**：D-FLARE 開發團隊  
**最後更新**：2025年10月9日
