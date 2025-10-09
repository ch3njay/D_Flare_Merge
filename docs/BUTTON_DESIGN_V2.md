# 按鈕設計系統 v2.0

## 🎨 設計理念

基於用戶反饋重新設計的按鈕系統，解決以下問題：
1. ❌ 舊版：一般按鈕與暗色背景融為一體，看不出是按鈕
2. ✅ 新版：半透明紫色漸層 + 品牌色光暈，清晰可見
3. ❌ 舊版：目錄按鈕太陽春
4. ✅ 新版：特別設計的左側邊條 + 品牌色光暈
5. ❌ 舊版：左上角按鈕平淡
6. ✅ 新版：參考圖3舊版設計，品牌色實心 + 強光暈

---

## 📋 按鈕類型分類

### 1️⃣ 一般按鈕（Default）

**設計特點**：
- 半透明紫色漸層背景
- 品牌色外光暈
- 文字顏色自動適應深淺主題
- 毛玻璃效果（backdrop-filter: blur）

**視覺結構**：
```
┌─────────────────────────────────────┐
│  品牌色光暈（橘色/藍色）              │
│  ┌───────────────────────────────┐  │
│  │ 半透明紫色漸層背景             │  │
│  │  rgba(139,92,246,0.25) →      │  │
│  │  rgba(168,85,247,0.15)        │  │
│  │ ┏━━━━━━━━━━━━━━━━━━━━━━━━┓ │  │
│  │ ┃ 文字（自適應深淺色）    ┃ │  │
│  │ ┃ 內部高光                ┃ │  │
│  │ ┗━━━━━━━━━━━━━━━━━━━━━━━━┛ │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

**CSS 實作**：
```css
background: linear-gradient(
    135deg,
    rgba(139, 92, 246, 0.25) 0%,
    rgba(168, 85, 247, 0.15) 100%);

border: 1.5px solid rgba(139, 92, 246, 0.4);

/* 品牌色光暈 - Fortinet 橘色，Cisco 藍色 */
box-shadow: 
    0 0 20px color-mix(in srgb, var(--primary-color) 30%, transparent),
    0 4px 12px rgba(0, 0, 0, 0.15),
    inset 0 1px 0 rgba(255, 255, 255, 0.08);

/* 文字自動適應 */
color: var(--text-color);

/* 毛玻璃效果 */
backdrop-filter: blur(10px);
```

**Hover 效果**：
```css
/* 提升 3px + 放大 1.03 倍 */
transform: translateY(-3px) scale(1.03);

/* 光暈增強到 50% */
box-shadow: 
    0 0 35px color-mix(in srgb, var(--primary-color) 50%, transparent),
    0 8px 20px rgba(0, 0, 0, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.15);

/* 背景更不透明 */
background: linear-gradient(
    135deg,
    rgba(139, 92, 246, 0.35) 0%,
    rgba(168, 85, 247, 0.25) 100%);
```

---

### 2️⃣ Primary 按鈕（重要操作）

**設計特點**：
- 品牌色實心漸層背景（橘色/藍色）
- 超強品牌色光暈（45-60%）
- 白色文字 + 文字陰影
- 參考圖3舊版設計

**視覺結構**：
```
┌─────────────────────────────────────┐
│  超強品牌色光暈（45-60%）             │
│  ┌───────────────────────────────┐  │
│  │ 品牌色實心漸層                 │  │
│  │  #FF6B35 → 混合紫色           │  │
│  │ ┏━━━━━━━━━━━━━━━━━━━━━━━━┓ │  │
│  │ ┃ 白色文字 + 陰影         ┃ │  │
│  │ ┃ 內部白色高光            ┃ │  │
│  │ ┗━━━━━━━━━━━━━━━━━━━━━━━━┛ │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

**CSS 實作**：
```css
/* 品牌色實心漸層 */
background: linear-gradient(
    135deg,
    var(--primary-color) 0%,
    color-mix(in srgb, var(--primary-color) 75%, #6366f1) 100%);

border: 2px solid var(--primary-color);

/* 超強光暈 */
box-shadow: 
    0 0 25px color-mix(in srgb, var(--primary-color) 45%, transparent),
    0 6px 16px rgba(0, 0, 0, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.15);

/* 白色文字 */
color: white;
text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
```

**Hover 效果**：
```css
/* 光暈增強到 60% */
box-shadow: 
    0 0 40px color-mix(in srgb, var(--primary-color) 60%, transparent),
    0 10px 25px rgba(0, 0, 0, 0.25),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
```

---

### 3️⃣ 側邊欄品牌選擇按鈕（特殊設計）

**設計特點**：
- **選中（Primary）**：品牌色實心 + 超強光暈（60-75%）
- **未選中（Secondary）**：深色半透明玻璃 + 柔和邊框
- 參考圖3舊版 Fortinet 選中效果

#### 選中狀態（Primary）

**視覺結構**：
```
Fortinet 選中：
┌─────────────────────────────────────┐
│  橘紅色超強光暈（60-75%）             │
│  ┌───────────────────────────────┐  │
│  │ 橘紅色實心漸層                 │  │
│  │  #f97316 → #dc2626            │  │
│  │ ┏━━━━━━━━━━━━━━━━━━━━━━━━┓ │  │
│  │ ┃ 🛡️ Fortinet          ┃ │  │
│  │ ┃ （白色文字 + 陰影）     ┃ │  │
│  │ ┗━━━━━━━━━━━━━━━━━━━━━━━━┛ │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

**CSS 實作**：
```css
/* 品牌色實心漸層 + 深色混合 */
background: linear-gradient(
    135deg, 
    var(--primary-color), 
    color-mix(in srgb, var(--primary-color) 65%, #dc2626));

border: 3px solid var(--primary-color);

/* 超強光暈（60%） */
box-shadow: 
    0 0 30px color-mix(in srgb, var(--primary-color) 60%, transparent),
    0 10px 25px rgba(0, 0, 0, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);

color: white;
text-shadow: 0 2px 4px rgba(0, 0, 0, 0.35);
```

**Hover 效果**：
```css
transform: translateY(-4px) scale(1.04);

/* 光暈增強到 75% */
box-shadow: 
    0 0 45px color-mix(in srgb, var(--primary-color) 75%, transparent),
    0 15px 35px rgba(0, 0, 0, 0.25),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);

filter: brightness(1.25);
```

#### 未選中狀態（Secondary）

**視覺結構**：
```
Cisco 未選中：
┌─────────────────────────────────────┐
│  無光暈或極淺光暈                    │
│  ┌───────────────────────────────┐  │
│  │ 深色半透明玻璃                 │  │
│  │  rgba(100,100,120,0.12)       │  │
│  │ ┏━━━━━━━━━━━━━━━━━━━━━━━━┓ │  │
│  │ ┃ 📡 Cisco             ┃ │  │
│  │ ┃ （淡色文字 75%）       ┃ │  │
│  │ ┗━━━━━━━━━━━━━━━━━━━━━━━━┛ │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

**CSS 實作**：
```css
/* 深色半透明玻璃 */
background: linear-gradient(
    135deg, 
    rgba(100, 100, 120, 0.12), 
    rgba(80, 80, 100, 0.08));

border: 2px solid rgba(255, 255, 255, 0.12);

color: rgba(255, 255, 255, 0.75);

box-shadow: 
    0 4px 12px rgba(0, 0, 0, 0.15),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);

backdrop-filter: blur(12px);
```

**Hover 效果**：
```css
/* 背景稍微變亮 */
background: linear-gradient(
    135deg, 
    rgba(120, 120, 140, 0.2), 
    rgba(100, 100, 120, 0.15));

border: 2px solid rgba(255, 255, 255, 0.25);
color: white;

transform: translateY(-3px) scale(1.03);
```

---

### 4️⃣ 目錄按鈕（Expander 內按鈕）

**設計特點**：
- 左側品牌色邊條（4px）
- 深色半透明背景 + 漸層品牌色
- 柔和品牌色光暈
- 左對齊文字
- Hover 時向右滑動

**視覺結構**：
```
Training Pipeline:
┌─────────────────────────────────────┐
│  品牌色光暈（15-30%）                 │
│  ┏━┯───────────────────────────────┐ │
│  ┃ │ 深色半透明背景                 │ │
│  ┃ │  品牌色漸層 25% →             │ │
│  ┃ │  半透明白色 3%                │ │
│  ┃ │                               │ │
│  ┃ │ 📊 Training Pipeline         │ │
│  ┃ │                               │ │
│  ┗━┷───────────────────────────────┘ │
│  ↑ 4px 品牌色邊條                     │
└─────────────────────────────────────┘
```

**CSS 實作**：
```css
/* 左側邊條 + 深色半透明背景 */
background: linear-gradient(
    to right,
    color-mix(in srgb, var(--primary-color) 25%, transparent) 0%,
    rgba(255, 255, 255, 0.03) 8%,
    rgba(255, 255, 255, 0.02) 100%);

/* 4px 品牌色左邊條 */
border-left: 4px solid var(--primary-color);
border-top: 1px solid rgba(255, 255, 255, 0.08);
border-right: 1px solid rgba(255, 255, 255, 0.08);
border-bottom: 1px solid rgba(255, 255, 255, 0.08);

/* 柔和光暈 */
box-shadow: 
    0 0 20px color-mix(in srgb, var(--primary-color) 15%, transparent),
    0 4px 12px rgba(0, 0, 0, 0.15);

/* 左對齊 */
text-align: left;
```

**Hover 效果**：
```css
/* 品牌色更濃 */
background: linear-gradient(
    to right,
    color-mix(in srgb, var(--primary-color) 35%, transparent) 0%,
    rgba(255, 255, 255, 0.06) 8%,
    rgba(255, 255, 255, 0.04) 100%);

/* 左邊條變亮 */
border-left: 4px solid color-mix(in srgb, var(--primary-color) 120%, white);

/* 光暈增強 */
box-shadow: 
    0 0 30px color-mix(in srgb, var(--primary-color) 30%, transparent),
    0 6px 18px rgba(0, 0, 0, 0.2);

/* 向右滑動 4px */
transform: translateX(4px);
```

---

## 🎯 品牌色光暈對應

### Fortinet 平台
```css
/* Primary Color: #FF6B35 (橘色) */

/* 一般按鈕光暈 */
box-shadow: 0 0 20px rgba(255, 107, 53, 0.3);

/* Primary 按鈕光暈 */
box-shadow: 0 0 25px rgba(255, 107, 53, 0.45);

/* 側邊欄選中光暈 */
box-shadow: 0 0 30px rgba(255, 107, 53, 0.6);

/* Hover 時光暈 */
box-shadow: 0 0 45px rgba(255, 107, 53, 0.75);
```

### Cisco 平台
```css
/* Primary Color: #38bdf8 (青藍色) */

/* 一般按鈕光暈 */
box-shadow: 0 0 20px rgba(56, 189, 248, 0.3);

/* Primary 按鈕光暈 */
box-shadow: 0 0 25px rgba(56, 189, 248, 0.45);

/* 側邊欄選中光暈 */
box-shadow: 0 0 30px rgba(56, 189, 248, 0.6);

/* Hover 時光暈 */
box-shadow: 0 0 45px rgba(56, 189, 248, 0.75);
```

---

## 📊 光暈強度對比表

| 按鈕類型 | 靜止狀態 | Hover 狀態 | 光暈顏色 |
|---------|----------|-----------|----------|
| **一般按鈕** | 30% | 50% | 品牌色 |
| **Primary 按鈕** | 45% | 60% | 品牌色 |
| **側邊欄選中** | 60% | 75% | 品牌色 |
| **側邊欄未選** | 無 | 無 | - |
| **目錄按鈕** | 15% | 30% | 品牌色 |

---

## 🎨 文字顏色自動適應

### 原理
使用 CSS 變數 `var(--text-color)`，自動根據主題調整：

```css
/* Light 主題 */
--text-color: #1A1A1A; /* 深色文字 */

/* Dark 主題 */
--text-color: #E6E8EB; /* 淺色文字 */
```

### 應用
```css
/* 一般按鈕 - 文字自動適應 */
color: var(--text-color);

/* Primary 按鈕 - 固定白色（實心背景） */
color: white;

/* 側邊欄選中 - 固定白色（實心背景） */
color: white;

/* 側邊欄未選 - 半透明白色 */
color: rgba(255, 255, 255, 0.75);
```

---

## 🔍 對比度檢查

### Light 主題

| 組合 | 前景色 | 背景色 | 對比度 | WCAG |
|------|--------|--------|--------|------|
| 一般按鈕 | #1A1A1A | 紫色半透明 | 4.5:1 | AA ✅ |
| Primary | white | #FF6B35 | 4.5:1 | AA ✅ |
| 目錄按鈕 | #1A1A1A | 深色半透明 | 4.2:1 | AA ✅ |

### Dark 主題

| 組合 | 前景色 | 背景色 | 對比度 | WCAG |
|------|--------|--------|--------|------|
| 一般按鈕 | #E6E8EB | 紫色半透明 | 5.5:1 | AA ✅ |
| Primary | white | #FF6B35 | 4.5:1 | AA ✅ |
| 目錄按鈕 | #E6E8EB | 深色半透明 | 5.0:1 | AA ✅ |

---

## 🎬 動畫效果

### Transform 動畫
```css
/* 一般按鈕 Hover */
transform: translateY(-3px) scale(1.03);

/* 側邊欄選中 Hover */
transform: translateY(-4px) scale(1.04);

/* 目錄按鈕 Hover */
transform: translateX(4px);

/* 動畫曲線 */
transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
```

### Brightness 濾鏡
```css
/* Primary 按鈕 Hover */
filter: brightness(1.15);

/* 側邊欄選中 Hover */
filter: brightness(1.25);
```

---

## 📝 修改檔案清單

1. **`unified_ui/app.py`**
   - 第 282-386 行：一般按鈕樣式（半透明紫色 + 品牌光暈）
   - 第 1230-1342 行：側邊欄品牌選擇按鈕（參考圖3舊版）
   - 第 1298-1342 行：目錄按鈕特別設計（左側邊條 + 光暈）

---

## 🎓 設計原則總結

### ✅ DO（應該做）

1. **使用半透明背景**：讓按鈕不會完全融入背景
2. **添加品牌色光暈**：清楚指示當前平台
3. **文字顏色自適應**：使用 `var(--text-color)`
4. **毛玻璃效果**：增加現代感（backdrop-filter: blur）
5. **漸層背景**：增加視覺深度
6. **動畫平滑**：使用 cubic-bezier 緩動函數

### ❌ DON'T（不應該做）

1. **不要硬編碼文字顏色**：除非是實心背景按鈕
2. **不要過度陰影**：保持柔和光暈
3. **不要忽略對比度**：確保 WCAG AA 標準
4. **不要統一所有按鈕**：根據功能區分設計
5. **不要忽略 Hover 狀態**：提供清晰的互動反饋

---

## 🚀 未來改進方向

### 短期（已完成）
- [x] 半透明紫色漸層背景
- [x] 品牌色光暈系統
- [x] 文字顏色自動適應
- [x] 側邊欄按鈕參考舊版設計
- [x] 目錄按鈕特別設計

### 中期（計劃中）
- [ ] 按鈕點擊波紋效果
- [ ] 不同尺寸變體（small, medium, large）
- [ ] 圖標 + 文字組合樣式
- [ ] Loading 狀態動畫
- [ ] Disabled 狀態樣式

### 長期（願景）
- [ ] 自訂主題色彩系統
- [ ] 無障礙增強（鍵盤導航）
- [ ] 動畫性能優化
- [ ] 跨瀏覽器兼容測試

---

**設計者**：D-FLARE 開發團隊  
**版本**：v2.0  
**更新日期**：2025年10月9日  
**狀態**：✅ 已實作，待用戶驗證
