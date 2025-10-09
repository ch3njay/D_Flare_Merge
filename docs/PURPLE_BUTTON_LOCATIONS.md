# 紫色按鈕修改位置清單

## 📍 主要修改位置

### 1️⃣ `unified_ui/app.py` - 第 295-403 行

這是**最主要的按鈕樣式定義**，控制所有一般按鈕的外觀。

```python
# 檔案：unified_ui/app.py
# 行數：295-403

/* === 按鈕樣式系統 v2.0 - 參考圖5漸層設計 === */

/* 通用按鈕基礎 - 飽和紫色漸層（參考圖5「停止監控」按鈕） */
.stButton > button,
button[kind="primary"],
button[kind="secondary"],
button[data-testid="baseButton-primary"],
button[data-testid="baseButton-secondary"] {
    /* 飽和紫色漸層 - 參考圖5 */
    background: linear-gradient(
        135deg,
        #8b5cf6 0%,      /* 👈 起始顏色 - 紫色 500 */
        #7c3aed 100%) !important;  /* 👈 結束顏色 - 紫色 600 */
    
    /* 紫色邊框 */
    border: 2px solid #8b5cf6 !important;  /* 👈 邊框顏色 */
    border-radius: 14px !important;
    font-weight: 600 !important;
    padding: 0.75rem 2rem !important;
    
    /* 柔和紫色光暈 */
    box-shadow: 
        0 0 20px rgba(139, 92, 246, 0.35),  /* 👈 光暈顏色和強度 */
        0 4px 12px rgba(0, 0, 0, 0.15),
        inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
    
    /* 白色文字 */
    color: white !important;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3) !important;
    
    transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1) !important;
    position: relative !important;
}

/* 按鈕懸停 - 增強光暈 */
.stButton > button:hover,
button[kind="primary"]:hover,
button[kind="secondary"]:hover,
button[data-testid="baseButton-primary"]:hover,
button[data-testid="baseButton-secondary"]:hover {
    transform: translateY(-3px) scale(1.03) !important;
    
    /* 更強紫色光暈 */
    box-shadow: 
        0 0 35px rgba(139, 92, 246, 0.55),  /* 👈 Hover 光暈強度 */
        0 8px 20px rgba(0, 0, 0, 0.2),
        inset 0 1px 0 rgba(255, 255, 255, 0.15) !important;
    
    /* 漸層變亮 */
    background: linear-gradient(
        135deg,
        #9d72f8 0%,      /* 👈 Hover 起始顏色 - 更亮的紫色 */
        #8b5cf6 100%) !important;  /* 👈 Hover 結束顏色 */
    
    filter: brightness(1.15) !important;
}
```

---

## 🎨 調整建議

### 選項 A：更飽和的紫色（鮮豔）
```css
/* 起始色 */
#8b5cf6 → #a78bfa  /* 紫色 400 - 更亮 */

/* 結束色 */
#7c3aed → #8b5cf6  /* 紫色 500 - 適中 */

/* 光暈 */
rgba(139, 92, 246, 0.35) → rgba(167, 139, 250, 0.45)
```

### 選項 B：深邃的紫色（沉穩）
```css
/* 起始色 */
#8b5cf6 → #7c3aed  /* 紫色 600 */

/* 結束色 */
#7c3aed → #6d28d9  /* 紫色 700 */

/* 光暈 */
rgba(139, 92, 246, 0.35) → rgba(124, 58, 237, 0.40)
```

### 選項 C：藍紫色（偏藍）
```css
/* 起始色 */
#8b5cf6 → #8b5cf6  /* 保持紫色 500 */

/* 結束色 */
#7c3aed → #6366f1  /* 靛藍色 500 - 偏藍 */

/* 光暈 */
rgba(139, 92, 246, 0.35) → rgba(99, 102, 241, 0.40)
```

### 選項 D：粉紫色（柔和）
```css
/* 起始色 */
#8b5cf6 → #c084fc  /* 紫色 400 - 更亮更粉 */

/* 結束色 */
#7c3aed → #a855f7  /* 紫色 500 - 粉紫 */

/* 光暈 */
rgba(139, 92, 246, 0.35) → rgba(192, 132, 252, 0.45)
```

---

## 📊 顏色對照表

| 名稱 | Hex 代碼 | RGB | 說明 |
|------|----------|-----|------|
| **紫色 400** | `#a78bfa` | rgb(167, 139, 250) | 亮紫色 |
| **紫色 500** | `#8b5cf6` | rgb(139, 92, 246) | **當前使用** |
| **紫色 600** | `#7c3aed` | rgb(124, 58, 237) | **當前使用** |
| **紫色 700** | `#6d28d9` | rgb(109, 40, 217) | 深紫色 |
| **靛藍 500** | `#6366f1` | rgb(99, 102, 241) | 藍紫色 |

---

## 🔧 如何修改

### 步驟 1：打開文件
```
檔案路徑：
c:\Users\U02020\Desktop\專案\D-FLARE系統\D_Flare_Merge-master\unified_ui\app.py
```

### 步驟 2：找到行號
按 `Ctrl + G` 輸入 `295` 跳轉到按鈕樣式區域

### 步驟 3：修改顏色
找到以下幾處並修改：

1. **第 306-308 行**：背景漸層起始/結束色
   ```css
   background: linear-gradient(
       135deg,
       #8b5cf6 0%,      /* 改這裡 */
       #7c3aed 100%)    /* 改這裡 */
   ```

2. **第 311 行**：邊框顏色
   ```css
   border: 2px solid #8b5cf6 !important;  /* 改這裡 */
   ```

3. **第 317 行**：光暈顏色
   ```css
   box-shadow: 
       0 0 20px rgba(139, 92, 246, 0.35),  /* 改這裡 */
   ```

4. **第 337 行**：Hover 光暈顏色
   ```css
   box-shadow: 
       0 0 35px rgba(139, 92, 246, 0.55),  /* 改這裡 */
   ```

5. **第 343-345 行**：Hover 背景漸層
   ```css
   background: linear-gradient(
       135deg,
       #9d72f8 0%,      /* 改這裡 */
       #8b5cf6 100%)    /* 改這裡 */
   ```

### 步驟 4：儲存並重新整理
1. 按 `Ctrl + S` 儲存
2. 在瀏覽器按 `F5` 重新整理
3. 查看效果

---

## 🎨 視覺效果預覽

### 當前設計（圖5風格）
```
┌──────────────────────────────────┐
│ 紫色光暈 35%                      │
│ ┌─────────────────────────────┐  │
│ │ #8b5cf6 → #7c3aed          │  │
│ │  ⬜ 停止監控               │  │
│ │  （白色文字）               │  │
│ └─────────────────────────────┘  │
└──────────────────────────────────┘
```

### 建議調整方向
1. **更亮**：使用紫色 400 (#a78bfa)
2. **更深**：使用紫色 700 (#6d28d9)
3. **偏藍**：混入靛藍 500 (#6366f1)
4. **柔和**：增加光暈透明度

---

## ⚠️ 注意事項

1. **對比度檢查**：
   - 白色文字在紫色背景上的對比度應 ≥ 4.5:1（WCAG AA）
   - 使用工具檢查：https://webaim.org/resources/contrastchecker/

2. **光暈強度**：
   - 太強：視覺疲勞
   - 太弱：按鈕不明顯
   - 建議範圍：0.3 - 0.5

3. **漸層方向**：
   - 當前：135deg（左上到右下）
   - 可選：90deg（左到右）、180deg（上到下）

4. **品牌一致性**：
   - Primary 按鈕使用品牌色（橘色/藍色）
   - 一般按鈕使用紫色
   - 確保整體和諧

---

## 🧪 測試檢查清單

修改後請測試：

- [ ] 按鈕在 Dark 主題下清晰可見
- [ ] 按鈕在 Light 主題下清晰可見（如果支援）
- [ ] Hover 效果流暢自然
- [ ] 文字對比度足夠（使用對比度檢查工具）
- [ ] 與品牌色（橘色/藍色）區分明顯
- [ ] 整體視覺和諧不突兀

---

## 📝 其他相關位置

### 2️⃣ `enhanced_theme.py` - 第 40-66 行
如果修改 `unified_ui/app.py`，也建議同步修改這裡以保持一致性。

```python
# 檔案：enhanced_theme.py
# 行數：40-66

# 這裡有相同的按鈕樣式定義
# 建議保持與 unified_ui/app.py 一致
```

---

**修改者**：使用者人工調整  
**文檔建立日期**：2025年10月9日  
**版本**：v2.0  
**狀態**：⏳ 待人工調整
