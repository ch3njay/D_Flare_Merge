"""快速開始指南 - 處理自訂資料的目標欄位問題"""
import pandas as pd
import numpy as np

print("="*70)
print("🚀 D-FLARE 系統 - 自訂資料訓練快速指南")
print("="*70)

print("\n📋 情境：您有一份自行前處理的資料，想要進行模型訓練")
print("\n" + "-"*70)

# ==================== 情境 1：檢查您的資料 ====================
print("\n【步驟 1】先檢查您的資料結構")
print("-"*70)

print("""
💡 使用資料檢查工具：

    python data_inspector.py "您的資料檔案路徑.csv"

這會告訴您：
- 📊 資料的基本資訊（筆數、欄位數、記憶體用量）
- 📋 每個欄位的詳細分析（型別、唯一值、缺失值）
- 🎯 可能的目標欄位候選（系統推薦）
- 💡 具體的使用建議
""")

# ==================== 情境 2：資料有標準標籤 ====================
print("\n【情境 A】您的資料已經有標籤欄位")
print("-"*70)

# 建立範例資料
print("\n✨ 範例資料（包含 'label' 欄位）：")
example_data = {
    'src_ip_encoded': [1, 2, 3, 4, 5],
    'dst_port': [80, 443, 22, 8080, 3306],
    'bytes_sent': [1024, 2048, 512, 4096, 256],
    'label': [0, 1, 0, 1, 0]  # 這是您的標籤欄位
}
df_example = pd.DataFrame(example_data)
print(df_example.head())

print("""
📝 使用方式：

【方式 1】在 UI 中使用（推薦）：
1. 開啟 D-FLARE 訓練介面
2. 上傳您的 CSV 檔案
3. 在「🎯 目標欄位設定」選擇「自動偵測」
   - 系統會自動找到 'label' 欄位
4. 點擊「🚀 開始訓練」

【方式 2】在程式中使用：
""")

print("""
from Cisco_ui.training_pipeline.pipeline_main import CiscoTrainingPipeline

# 方式 2A：讓系統自動偵測
pipeline = CiscoTrainingPipeline(
    task_type="binary",
    target_column=None  # 自動偵測
)

# 方式 2B：明確指定欄位名稱
pipeline = CiscoTrainingPipeline(
    task_type="binary",
    target_column="label"  # 明確指定
)

# 執行訓練
results = pipeline.run("your_data.csv")
if results["success"]:
    print(f"✅ 訓練成功！最佳模型：{results['best_model']}")
""")

# ==================== 情境 3：資料沒有標籤 ====================
print("\n【情境 B】您的資料還沒有標籤欄位")
print("-"*70)

print("""
💡 您需要先建立標籤欄位。以下是常見的方法：

【方法 1】根據條件自動產生標籤：
""")

print("""
import pandas as pd

# 讀取您的資料
df = pd.read_csv("your_preprocessed_data.csv")

# 根據某些規則建立標籤
# 範例：假設 'action' 欄位包含 'deny' 表示攻擊
df['is_attack'] = df['action'].str.contains('deny|drop', case=False).astype(int)

# 或根據多個條件
def classify_attack(row):
    if row['severity'] == 'critical':
        return 1
    elif row['bytes'] > 10000 and row['port'] in [22, 23, 3389]:
        return 1
    return 0

df['is_attack'] = df.apply(classify_attack, axis=1)

# 儲存處理後的資料
df.to_csv("labeled_data.csv", index=False)
print(f"✅ 已新增標籤，攻擊筆數：{df['is_attack'].sum()}")
""")

print("""
【方法 2】手動標註部分資料（適合小量資料）：
""")

print("""
import pandas as pd

df = pd.read_csv("your_data.csv")

# 顯示前幾筆資料，手動新增標籤
df['is_attack'] = 0  # 預設為正常

# 根據您的判斷標註（可在 Excel 中編輯）
# 例如：將索引 10-50 的資料標記為攻擊
df.loc[10:50, 'is_attack'] = 1

df.to_csv("labeled_data.csv", index=False)
""")

# ==================== 情境 4：常見錯誤 ====================
print("\n【常見問題排解】")
print("-"*70)

print("""
❌ 錯誤 1：「找不到目標欄位」

解決方法：
1. 檢查您的 CSV 檔案是否包含標籤欄位
2. 使用 data_inspector.py 查看所有欄位
3. 在 UI 中使用「手動指定」功能

❌ 錯誤 2：「自動偵測選錯欄位」

解決方法：
1. 使用「手動指定」明確指定正確的欄位
2. 或將標籤欄位重新命名為標準名稱（is_attack 或 crlevel）

❌ 錯誤 3：「資料格式不正確」

解決方法：
1. 確保 CSV 檔案格式正確（UTF-8 編碼）
2. 檢查是否有特殊字元或編碼問題
3. 使用 data_inspector.py 檢查資料品質
""")

# ==================== 實用命令整理 ====================
print("\n【實用命令整理】")
print("-"*70)

print("""
1️⃣ 檢查資料結構：
   python data_inspector.py "資料檔案.csv"

2️⃣ 執行功能測試：
   python test_target_column_detection.py

3️⃣ 啟動 UI 介面：
   python launch_unified_dashboard.py

4️⃣ 查看詳細指南：
   - docs/TARGET_COLUMN_GUIDE.md（完整使用指南）
   - TARGET_COLUMN_SOLUTION_SUMMARY.md（技術實作總結）
""")

# ==================== 完整範例 ====================
print("\n【完整範例：從頭到尾】")
print("-"*70)

print("""
# 步驟 1：檢查資料
python data_inspector.py "preprocessed_data.csv"

# 步驟 2：如果資料沒有標籤，使用 Python 新增
import pandas as pd
df = pd.read_csv("preprocessed_data.csv")
df['is_attack'] = (df['action'] == 'deny').astype(int)
df.to_csv("labeled_data.csv", index=False)

# 步驟 3A：使用 UI 訓練（推薦）
# - 開啟 UI
# - 上傳 labeled_data.csv
# - 選擇「自動偵測」或「手動指定：is_attack」
# - 開始訓練

# 步驟 3B：或使用程式碼訓練
from Cisco_ui.training_pipeline.pipeline_main import CiscoTrainingPipeline

pipeline = CiscoTrainingPipeline(
    task_type="binary",
    target_column="is_attack"
)

results = pipeline.run("labeled_data.csv")
print(f"✅ 訓練完成！準確率：{results['best_accuracy']:.2%}")
""")

print("\n" + "="*70)
print("✅ 快速指南結束！如有問題請參考 docs/TARGET_COLUMN_GUIDE.md")
print("="*70)
