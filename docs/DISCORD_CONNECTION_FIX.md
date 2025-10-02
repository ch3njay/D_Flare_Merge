# Discord 連線問題快速修復指南

## 🚨 問題症狀

您遇到的錯誤訊息：
```
Failed to send: ('Connection aborted.', ConnectionResetError(10054, '遠端主機已強制關閉一個現存的連線。', None, 10054, None))
```

這表示與 Discord 的連線被強制中斷。

## 🔧 快速修復步驟

### 1. 立即檢查 (1 分鐘)

```bash
# 執行連線診斷工具
python discord_connection_fix.py

# 或使用批次檔 (Windows)
fix_discord_connection.bat
```

### 2. 常見原因與解決方案

#### A. 網路連線問題
- **症狀**: 無法連接任何網站
- **解決**: 
  - 檢查網路連線
  - 重新啟動路由器/數據機
  - 更換網路 (手機熱點測試)

#### B. Discord 伺服器問題  
- **症狀**: 其他網站正常，只有 Discord 有問題
- **解決**:
  - 檢查 [Discord 狀態頁面](https://discordstatus.com/)
  - 等待 5-10 分鐘後重試
  - 使用不同時間重新測試

#### C. 防火牆/代理問題
- **症狀**: 企業網路環境下發生
- **解決**:
  - 暫時關閉防火牆測試
  - 檢查代理伺服器設定
  - 聯繫 IT 管理員開放 Discord 存取

#### D. Webhook URL 問題
- **症狀**: URL 無效或權限不足
- **解決**:
  - 重新生成 Discord webhook
  - 檢查 webhook 權限設定
  - 確認頻道存在且可存取

### 3. 程式碼層級修復 (已改善)

我已經改善了 `notifier.py` 中的 Discord 發送函式，增加了：

- ✅ 自動重試機制 (最多 3 次)
- ✅ 指數退避重試間隔  
- ✅ 更好的錯誤處理
- ✅ 連線超時設定
- ✅ Rate limiting 處理
- ✅ 更詳細的錯誤訊息

### 4. 手動測試步驟

1. **基本網路測試**:
   ```bash
   ping google.com
   ping discord.com
   ```

2. **DNS 測試**:
   ```bash
   nslookup discord.com
   ```

3. **Webhook 測試**:
   - 在瀏覽器開啟 `https://discord.com`
   - 檢查是否可正常存取

## 🔧 程式碼修復說明

### 改善前 (容易失敗):
```python
response = requests.post(webhook_url, json={"content": message}, timeout=20)
```

### 改善後 (更可靠):
```python
# 自動重試 3 次，處理連線重置錯誤
for attempt in range(max_retries):
    try:
        response = session.post(
            webhook_url, 
            json={"content": message[:2000]},
            timeout=(10, 30),  # 連線超時, 讀取超時
            allow_redirects=True
        )
        # ... 處理回應和錯誤
    except requests.exceptions.ConnectionError:
        # 自動重試，指數退避
        time.sleep(min(2 ** attempt, 5))
```

## 📋 檢查清單

在回報問題前，請確認：

- [ ] 網路連線正常 (可開啟其他網站)
- [ ] Discord 官方服務正常
- [ ] Webhook URL 格式正確
- [ ] 已執行連線診斷工具
- [ ] 已重新啟動應用程式
- [ ] 防火牆未阻擋連線

## 🆘 如果仍無法解決

1. **收集錯誤資訊**:
   - 完整錯誤訊息
   - 網路環境 (家用/企業/學校)
   - 作業系統版本
   - 是否使用代理或 VPN

2. **嘗試替代方案**:
   - 使用手機熱點測試
   - 更換不同時段測試  
   - 聯繫網路管理員
   - 考慮使用其他通知方式 (email, file log)

## 📞 支援聯繫

如果問題持續存在，請提供：
- 診斷工具輸出結果
- 完整錯誤訊息
- 網路環境描述
- 嘗試過的解決方案

---

**提示**: 大多數連線問題都是暫時性的，等待 5-10 分鐘通常就能自動恢復。