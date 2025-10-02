#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Discord 連線診斷與修復工具
========================

此工具用於診斷和修復 D-Flare 專案中的 Discord 連線問題。

使用方法:
    python discord_connection_fix.py

功能:
- 測試網路連線
- 驗證 Discord webhook URL  
- 診斷連線問題
- 提供修復建議

作者: AI Assistant
日期: 2025年10月1日
"""

import json
import socket
import ssl
import sys
import time
import urllib.parse
from typing import Dict, List, Optional, Tuple

try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
except ImportError:
    print("❌ 缺少 requests 套件，請執行: pip install requests")
    sys.exit(1)


class DiscordConnectionTester:
    """Discord 連線測試器"""
    
    def __init__(self):
        self.session = None
        self.setup_session()
    
    def setup_session(self):
        """設定 requests session 以改善連線可靠性"""
        self.session = requests.Session()
        
        # 設定重試策略
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # 設定 headers
        self.session.headers.update({
            'User-Agent': 'D-FLARE/1.0 Discord Connection Tester',
            'Accept': 'application/json',
            'Connection': 'keep-alive'
        })
    
    def test_internet_connection(self) -> Tuple[bool, str]:
        """測試基本網路連線"""
        print("🔍 測試網路連線...")
        
        test_urls = [
            "https://www.google.com",
            "https://1.1.1.1", 
            "https://8.8.8.8"
        ]
        
        for url in test_urls:
            try:
                response = self.session.get(url, timeout=5)
                if response.status_code == 200:
                    print(f"✅ 網路連線正常 ({url})")
                    return True, "網路連線正常"
            except Exception as e:
                print(f"❌ {url} 連線失敗: {e}")
                continue
        
        return False, "網路連線異常"
    
    def test_dns_resolution(self, hostname: str = "discord.com") -> Tuple[bool, str]:
        """測試 DNS 解析"""
        print(f"🔍 測試 DNS 解析 ({hostname})...")
        
        try:
            ip = socket.gethostbyname(hostname)
            print(f"✅ DNS 解析成功: {hostname} -> {ip}")
            return True, f"DNS 正常: {ip}"
        except socket.gaierror as e:
            print(f"❌ DNS 解析失敗: {e}")
            return False, f"DNS 解析失敗: {e}"
    
    def test_discord_api(self) -> Tuple[bool, str]:
        """測試 Discord API 連線"""
        print("🔍 測試 Discord API 連線...")
        
        try:
            response = self.session.get(
                "https://discord.com/api/v10/gateway",
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ Discord API 連線正常")
                return True, "Discord API 可用"
            else:
                print(f"❌ Discord API 回應異常: {response.status_code}")
                return False, f"Discord API 狀態碼: {response.status_code}"
                
        except Exception as e:
            print(f"❌ Discord API 連線失敗: {e}")
            return False, f"Discord API 連線失敗: {e}"
    
    def validate_webhook_url(self, webhook_url: str) -> Tuple[bool, str]:
        """驗證 webhook URL 格式"""
        print("🔍 驗證 webhook URL...")
        
        if not webhook_url or not webhook_url.strip():
            return False, "Webhook URL 為空"
        
        # 檢查 URL 格式
        try:
            parsed = urllib.parse.urlparse(webhook_url)
            if not parsed.scheme or not parsed.netloc:
                return False, "URL 格式不正確"
            
            if "discord.com" not in parsed.netloc and "discordapp.com" not in parsed.netloc:
                return False, "不是有效的 Discord webhook URL"
            
            if "/api/webhooks/" not in parsed.path:
                return False, "URL 路徑不正確，應包含 /api/webhooks/"
                
            print("✅ Webhook URL 格式正確")
            return True, "URL 格式正確"
            
        except Exception as e:
            return False, f"URL 解析失敗: {e}"
    
    def test_webhook_connection(self, webhook_url: str) -> Tuple[bool, str]:
        """測試 webhook 連線"""
        print("🔍 測試 webhook 連線...")
        
        # 先驗證 URL
        valid, msg = self.validate_webhook_url(webhook_url)
        if not valid:
            return False, msg
        
        try:
            # 發送測試訊息
            test_message = "🔧 D-FLARE 連線測試 - 請忽略此訊息"
            
            response = self.session.post(
                webhook_url,
                json={"content": test_message},
                timeout=(10, 30)
            )
            
            if response.status_code == 204:
                print("✅ Webhook 測試成功")
                return True, "Webhook 連線正常"
            elif response.status_code == 429:
                return False, "請求頻率過高，請稍後再試"
            elif response.status_code == 404:
                return False, "Webhook 不存在或已被刪除"
            elif response.status_code == 401:
                return False, "Webhook 權限不足"
            else:
                return False, f"Webhook 測試失敗，狀態碼: {response.status_code}"
                
        except requests.exceptions.ConnectionError as e:
            return False, f"連線被重置或中斷: {e}"
        except requests.exceptions.Timeout as e:
            return False, f"連線超時: {e}"
        except Exception as e:
            return False, f"Webhook 測試失敗: {e}"
    
    def diagnose_connection_issues(self) -> Dict[str, str]:
        """診斷常見連線問題"""
        print("\n🔧 診斷連線問題...")
        
        issues = {}
        
        # 檢查網路連線
        net_ok, net_msg = self.test_internet_connection()
        if not net_ok:
            issues["網路連線"] = net_msg
        
        # 檢查 DNS
        dns_ok, dns_msg = self.test_dns_resolution()
        if not dns_ok:
            issues["DNS 解析"] = dns_msg
        
        # 檢查 Discord API
        api_ok, api_msg = self.test_discord_api()
        if not api_ok:
            issues["Discord API"] = api_msg
        
        return issues
    
    def get_fix_suggestions(self, issues: Dict[str, str]) -> List[str]:
        """根據問題提供修復建議"""
        suggestions = []
        
        if "網路連線" in issues:
            suggestions.extend([
                "📶 檢查網路連線是否正常",
                "🔄 重新啟動網路連線",
                "🛜 檢查 WiFi 或有線網路設定"
            ])
        
        if "DNS 解析" in issues:
            suggestions.extend([
                "🌐 更換 DNS 伺服器 (如 8.8.8.8 或 1.1.1.1)",
                "🔄 清除 DNS 快取: ipconfig /flushdns (Windows)",
                "⚙️ 檢查路由器 DNS 設定"
            ])
        
        if "Discord API" in issues:
            suggestions.extend([
                "🚫 檢查防火牆是否阻擋 Discord",
                "🌐 檢查代理伺服器設定",
                "⏰ Discord 可能暫時維護，請稍後再試"
            ])
        
        # 通用建議
        suggestions.extend([
            "🔄 重新啟動應用程式",
            "⏳ 等待數分鐘後重試",
            "🔒 檢查是否有企業防火牆或網路限制",
            "📞 聯繫網路管理員確認 Discord 存取權限"
        ])
        
        return suggestions


def test_webhook_url():
    """互動式測試 webhook URL"""
    print("=" * 60)
    print("🔧 Discord Webhook 連線測試工具")
    print("=" * 60)
    
    tester = DiscordConnectionTester()
    
    # 基本診斷
    issues = tester.diagnose_connection_issues()
    
    if issues:
        print(f"\n❌ 發現 {len(issues)} 個連線問題:")
        for problem, detail in issues.items():
            print(f"  • {problem}: {detail}")
        
        print("\n💡 建議的修復步驟:")
        suggestions = tester.get_fix_suggestions(issues)
        for i, suggestion in enumerate(suggestions, 1):
            print(f"  {i}. {suggestion}")
    else:
        print("\n✅ 基本網路診斷通過")
    
    # 測試 webhook
    print(f"\n{'-' * 40}")
    webhook_url = input("請輸入 Discord Webhook URL (或按 Enter 跳過): ").strip()
    
    if webhook_url:
        print(f"\n🔍 測試 Webhook: {webhook_url[:50]}...")
        success, message = tester.test_webhook_connection(webhook_url)
        
        if success:
            print(f"✅ {message}")
            print("🎉 Discord 連線測試完成！您的 webhook 工作正常。")
        else:
            print(f"❌ {message}")
            print("\n💡 Webhook 修復建議:")
            print("  1. 🔍 檢查 webhook URL 是否正確")
            print("  2. 🔑 確認 webhook 權限設定")
            print("  3. 📋 在 Discord 伺服器重新生成 webhook")
            print("  4. ⏰ 等待 1-2 分鐘後重試")
    
    print(f"\n{'-' * 60}")
    print("測試完成！")


def create_improved_discord_config():
    """創建改善的 Discord 設定範例"""
    config = {
        "discord_settings": {
            "webhook_url": "",
            "retry_attempts": 3,
            "timeout_seconds": 30,
            "rate_limit_delay": 1,
            "message_max_length": 2000,
            "connection_pool_size": 10
        },
        "fallback_options": {
            "enable_fallback": True,
            "fallback_methods": ["file_log", "console_output"],
            "log_file_path": "discord_errors.log"
        }
    }
    
    with open("discord_config_improved.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print("✅ 已創建改善的 Discord 設定檔: discord_config_improved.json")


if __name__ == "__main__":
    try:
        test_webhook_url()
        
        print(f"\n📝 是否創建改善的設定檔? (y/N): ", end="")
        choice = input().strip().lower()
        
        if choice in ['y', 'yes', '是']:
            create_improved_discord_config()
        
    except KeyboardInterrupt:
        print(f"\n\n⚠️  測試被中斷")
    except Exception as e:
        print(f"\n❌ 測試過程發生錯誤: {e}")
        print("請檢查網路連線後重試")