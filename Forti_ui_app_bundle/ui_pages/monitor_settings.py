"""Fortinet 監控設定頁面 - 控制通知和視覺化功能。"""
import streamlit as st
from . import apply_dark_theme


def app() -> None:
    """監控設定頁面主函數。"""
    st.title("⚙️ 監控設定")
    apply_dark_theme()
    
    st.markdown("### 📱 通知設定")
    
    # 通知功能開關
    enable_notifications = st.checkbox(
        "啟用通知功能",
        value=st.session_state.get("enable_notifications", True),
        help="開啟後，資料夾監控檢測到符合條件的事件時會發送通知"
    )
    st.session_state.enable_notifications = enable_notifications
    
    if enable_notifications:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Discord 設定")
            discord_webhook = st.text_input(
                "Discord Webhook URL",
                value=st.session_state.get("discord_webhook", ""),
                type="password",
                placeholder="https://discord.com/api/webhooks/..."
            )
            st.session_state.discord_webhook = discord_webhook
            
            st.markdown("#### Gemini AI 設定")
            gemini_key = st.text_input(
                "Gemini API Key",
                value=st.session_state.get("gemini_key", ""),
                type="password",
                placeholder="請輸入您的 Gemini API Key"
            )
            st.session_state.gemini_key = gemini_key
        
        with col2:
            st.markdown("#### LINE 設定")
            line_token = st.text_input(
                "LINE Channel Access Token",
                value=st.session_state.get("line_token", ""),
                type="password",
                placeholder="請輸入 LINE 機器人 Token"
            )
            st.session_state.line_token = line_token
        
        st.markdown("#### 🎯 收斂設定")
        convergence_window = st.slider(
            "收斂時間窗口（分鐘）",
            min_value=1,
            max_value=60,
            value=st.session_state.get("convergence_window", 10),
            help="在此時間窗口內的相似事件會被收斂為一個通知"
        )
        st.session_state.convergence_window = convergence_window
        
        # 收斂欄位選擇
        convergence_fields = st.multiselect(
            "收斂欄位",
            options=["source", "destination", "protocol", "port"],
            default=st.session_state.get("convergence_fields", ["source", "destination"]),
            help="選擇用於事件收斂的欄位"
        )
        st.session_state.convergence_fields = convergence_fields
        
        # 更新收斂設定
        st.session_state.forti_convergence = {
            "window_minutes": convergence_window,
            "group_fields": convergence_fields
        }
    
    st.markdown("---")
    st.markdown("### 📊 視覺化設定")
    
    # 視覺化同步開關
    enable_visualization_sync = st.checkbox(
        "啟用視覺化自動同步",
        value=st.session_state.get("enable_visualization_sync", True),
        help="開啟後，資料夾監控處理檔案時會自動更新視覺化頁面"
    )
    st.session_state.enable_visualization_sync = enable_visualization_sync
    
    if enable_visualization_sync:
        st.info("✅ 視覺化將在檔案處理完成後自動更新")
    else:
        st.warning("⚠️ 需要手動重新整理視覺化頁面查看最新結果")
    
    st.markdown("---")
    st.markdown("### 📂 資料夾監控設定")
    
    # 監控敏感度設定
    monitor_sensitivity = st.select_slider(
        "監控敏感度",
        options=["低", "中", "高"],
        value=st.session_state.get("monitor_sensitivity", "中"),
        help="高敏感度會更頻繁地檢查檔案變更"
    )
    st.session_state.monitor_sensitivity = monitor_sensitivity
    
    # 檔案過濾設定
    st.markdown("#### 📄 檔案過濾")
    filter_etl_files = st.checkbox(
        "過濾 ETL 產生的檔案",
        value=st.session_state.get("filter_etl_files", True),
        help="避免處理由 ETL 流程產生的中間檔案"
    )
    st.session_state.filter_etl_files = filter_etl_files
    
    # 自動清理設定
    auto_cleanup = st.checkbox(
        "自動清理舊檔案",
        value=st.session_state.get("auto_cleanup", False),
        help="自動清理指定天數前的處理檔案"
    )
    st.session_state.auto_cleanup = auto_cleanup
    
    if auto_cleanup:
        cleanup_days = st.number_input(
            "保留天數",
            min_value=1,
            max_value=365,
            value=st.session_state.get("cleanup_days", 30),
            help="保留多少天內的檔案"
        )
        st.session_state.cleanup_days = cleanup_days
    
    st.markdown("---")
    st.markdown("### 💾 通知記錄設定")
    
    # 通知記錄保留設定
    notification_retention = st.number_input(
        "通知記錄保留天數",
        min_value=1,
        max_value=365,
        value=st.session_state.get("notification_retention", 30),
        help="通知記錄保留時間"
    )
    st.session_state.notification_retention = notification_retention
    
    # 去重設定
    dedupe_window = st.slider(
        "去重時間窗口（小時）",
        min_value=1,
        max_value=24,
        value=st.session_state.get("dedupe_window", 1),
        help="在此時間內的相同檔案不會重複發送通知"
    )
    st.session_state.dedupe_window = dedupe_window
    
    # 設定狀態顯示
    st.markdown("---")
    st.markdown("### 📊 目前設定狀態")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "通知功能",
            "啟用" if enable_notifications else "停用",
            delta="✅" if enable_notifications else "❌",
        )
    
    with col2:
        st.metric(
            "視覺化同步",
            "啟用" if enable_visualization_sync else "停用", 
            delta="🔄" if enable_visualization_sync else "⏹️",
        )
    
    with col3:
        notification_count = len([
            key for key in [discord_webhook, line_token, gemini_key] 
            if st.session_state.get(key.replace("_", "_"), "")
        ]) if enable_notifications else 0
        st.metric(
            "已設定通知管道",
            f"{notification_count}/3",
            delta="📱" if notification_count > 0 else "🔇",
        )
    
    # 測試按鈕
    if enable_notifications and notification_count > 0:
        st.markdown("### 🧪 測試通知")
        if st.button("發送測試通知", type="primary"):
            try:
                from ..notifier import send_discord, send_line_to_all
                
                test_message = "🧪 D-FLARE Fortinet 監控系統測試通知\n\n這是一個測試訊息，用於驗證通知設定是否正確。"
                
                success_count = 0
                if discord_webhook:
                    ok, _ = send_discord(discord_webhook, test_message)
                    if ok:
                        success_count += 1
                        st.success("✅ Discord 通知發送成功")
                    else:
                        st.error("❌ Discord 通知發送失敗")
                
                if line_token:
                    if send_line_to_all(line_token, test_message):
                        success_count += 1
                        st.success("✅ LINE 通知發送成功")
                    else:
                        st.error("❌ LINE 通知發送失敗")
                
                if success_count > 0:
                    st.balloons()
                    
            except Exception as e:
                st.error(f"測試通知時發生錯誤：{e}")
    
    # 重設按鈕
    st.markdown("---")
    if st.button("🔄 重設所有設定", type="secondary"):
        # 清除相關設定
        settings_to_clear = [
            "enable_notifications", "enable_visualization_sync",
            "discord_webhook", "line_token", "gemini_key",
            "convergence_window", "convergence_fields", "forti_convergence",
            "monitor_sensitivity", "filter_etl_files", "auto_cleanup", "cleanup_days",
            "notification_retention", "dedupe_window"
        ]
        
        for setting in settings_to_clear:
            if setting in st.session_state:
                del st.session_state[setting]
        
        st.success("✅ 設定已重設為預設值")
        st.rerun()