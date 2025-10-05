# -*- coding: utf-8 -*-
"""
D-Flare 專案依賴項目自動安裝腳本
====================================

此腳本會自動檢測並安裝 D-Flare 專案所需的所有外部依賴項目。

使用方法:
    python install_dependencies.py

作者: AI Assistant
日期: 2025年9月30日
"""

import subprocess
import sys
from typing import List, Tuple
import importlib


# ============================================================================
# 核心依賴項目清單
# ============================================================================

# 基礎 Web 框架與 UI
WEB_UI_PACKAGES = [
    "streamlit>=1.28.0",           # Streamlit 網頁應用框架
    "streamlit-autorefresh",       # Streamlit 自動重新整理元件（可選）
]

# 資料處理與科學計算
DATA_SCIENCE_PACKAGES = [
    "pandas>=1.5.0",              # 資料處理框架
    "numpy>=1.21.0",              # 數值計算庫
    "scipy>=1.9.0",               # 科學計算庫
]

# 機器學習核心套件
ML_CORE_PACKAGES = [
    "scikit-learn>=1.2.0",        # 機器學習核心庫
    "joblib>=1.2.0",              # 並行處理與模型序列化
]

# 進階機器學習套件
ML_ADVANCED_PACKAGES = [
    "xgboost>=1.6.0",             # XGBoost 梯度提升
    "lightgbm>=3.3.0",            # LightGBM 梯度提升
    "catboost>=1.1.0",            # CatBoost 梯度提升
    "optuna>=3.0.0",              # 超參數最佳化
]

# 資料視覺化
VISUALIZATION_PACKAGES = [
    "matplotlib>=3.6.0",          # 基礎繪圖庫
    "seaborn>=0.11.0",            # 統計視覺化
    "plotly>=5.11.0",             # 互動式視覺化
]

# 系統監控與進度顯示
SYSTEM_PACKAGES = [
    "tqdm>=4.64.0",               # 進度條
    "colorama>=0.4.5",            # 終端機色彩輸出
    "psutil>=5.9.0",              # 系統資源監控
    "watchdog>=2.1.0",            # 檔案系統監控
]

# 網路通訊與 API
NETWORK_PACKAGES = [
    "requests>=2.28.0",           # HTTP 請求庫
    "urllib3>=1.26.0",            # HTTP 客戶端
]

# 文字編碼檢測與壓縮
TEXT_COMPRESSION_PACKAGES = [
    "chardet>=4.0.0",             # 字元編碼檢測
]

# AI 與自然語言處理 (可選)
AI_PACKAGES = [
    "google-generativeai",        # Google Gemini API
    "openai",                     # OpenAI API (如果需要)
]

# GPU 加速 (可選)
GPU_PACKAGES = [
    "cupy-cuda11x",               # CUDA 11.x 版本的 CuPy
    # "cupy-cuda12x",             # CUDA 12.x 版本的 CuPy (替代選項)
]

# 開發工具 (可選)
DEV_PACKAGES = [
    "pytest>=7.0.0",             # 測試框架
    "black>=22.0.0",              # 程式碼格式化
    "flake8>=5.0.0",              # 程式碼風格檢查
    "mypy>=0.991",                # 型別檢查
]


# ============================================================================
# 安裝函式
# ============================================================================

def check_package_installed(package_name: str) -> bool:
    """檢查套件是否已安裝"""
    # 處理版本要求格式 (例如 "pandas>=1.5.0" -> "pandas")
    clean_name = package_name.split('>=')[0].split('==')[0].split('>')[0].split('<')[0]
    
    try:
        importlib.import_module(clean_name.replace('-', '_'))
        return True
    except ImportError:
        try:
            # 有些套件的導入名稱與安裝名稱不同
            name_mapping = {
                'scikit-learn': 'sklearn',
                'google-generativeai': 'google.generativeai',
                'streamlit-autorefresh': 'streamlit_autorefresh',
                'cupy-cuda11x': 'cupy',
                'cupy-cuda12x': 'cupy',
            }
            if clean_name in name_mapping:
                importlib.import_module(name_mapping[clean_name])
                return True
        except ImportError:
            pass
        return False


def install_package(package: str) -> Tuple[bool, str]:
    """安裝單一套件"""
    try:
        print(f"📦 安裝 {package}...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", package],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"✅ {package} 安裝成功")
        return True, ""
    except subprocess.CalledProcessError as e:
        error_msg = f"❌ {package} 安裝失敗: {e.stderr}"
        print(error_msg)
        return False, error_msg


def install_packages(packages: List[str], category_name: str, optional: bool = False) -> Tuple[List[str], List[str]]:
    """安裝一組套件"""
    print(f"\n{'='*50}")
    print(f"📋 {category_name}")
    print(f"{'='*50}")
    
    installed = []
    failed = []
    
    for package in packages:
        package_name = package.split('>=')[0].split('==')[0].split('>')[0].split('<')[0]
        
        if check_package_installed(package_name):
            print(f"✅ {package_name} 已安裝")
            installed.append(package)
            continue
            
        success, error = install_package(package)
        if success:
            installed.append(package)
        else:
            failed.append(package)
            if optional:
                print(f"⚠️  可選套件 {package} 安裝失敗，繼續安裝其他套件...")
            else:
                print(f"❌ 必要套件 {package} 安裝失敗！")
    
    return installed, failed


def upgrade_pip():
    """升級 pip 到最新版本"""
    print("🔄 升級 pip...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
            capture_output=True,
            text=True,
            check=True
        )
        print("✅ pip 升級成功")
    except subprocess.CalledProcessError:
        print("⚠️  pip 升級失敗，但不影響後續安裝")


def check_cuda_availability():
    """檢查 CUDA 是否可用"""
    try:
        result = subprocess.run(["nvidia-smi"], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False


def main():
    """主安裝流程"""
    print("🚀 D-Flare 專案依賴項目自動安裝開始")
    print(f"Python 版本: {sys.version}")
    print(f"安裝路徑: {sys.executable}")
    
    # 升級 pip
    upgrade_pip()
    
    all_installed = []
    all_failed = []
    
    # 安裝核心依賴項目
    categories = [
        (WEB_UI_PACKAGES, "Web UI 框架", False),
        (DATA_SCIENCE_PACKAGES, "資料科學套件", False),
        (ML_CORE_PACKAGES, "機器學習核心套件", False),
        (ML_ADVANCED_PACKAGES, "進階機器學習套件", False),
        (VISUALIZATION_PACKAGES, "資料視覺化套件", False),
        (SYSTEM_PACKAGES, "系統工具套件", False),
        (NETWORK_PACKAGES, "網路通訊套件", False),
        (TEXT_COMPRESSION_PACKAGES, "文字處理套件", False),
    ]
    
    # 可選依賴項目
    optional_categories = [
        (AI_PACKAGES, "AI 與自然語言處理 (可選)", True),
        (DEV_PACKAGES, "開發工具 (可選)", True),
    ]
    
    # 安裝核心依賴項目
    for packages, name, optional in categories:
        installed, failed = install_packages(packages, name, optional)
        all_installed.extend(installed)
        all_failed.extend(failed)
    
    # GPU 支援檢查與安裝
    print(f"\n{'='*50}")
    print("🔍 檢查 GPU 支援...")
    print(f"{'='*50}")
    
    if check_cuda_availability():
        print("✅ 檢測到 NVIDIA GPU，安裝 GPU 加速套件...")
        installed, failed = install_packages(GPU_PACKAGES, "GPU 加速套件 (CUDA)", True)
        all_installed.extend(installed)
        all_failed.extend(failed)
    else:
        print("ℹ️  未檢測到 NVIDIA GPU，跳過 GPU 加速套件安裝")
    
    # 安裝可選依賴項目
    for packages, name, optional in optional_categories:
        installed, failed = install_packages(packages, name, optional)
        all_installed.extend(installed)
        all_failed.extend(failed)
    
    # 安裝總結
    print(f"\n{'='*60}")
    print("📊 安裝總結")
    print(f"{'='*60}")
    print(f"✅ 成功安裝: {len(all_installed)} 個套件")
    print(f"❌ 安裝失敗: {len(all_failed)} 個套件")
    
    if all_installed:
        print(f"\n📦 成功安裝的套件:")
        for package in all_installed:
            print(f"  ✅ {package}")
    
    if all_failed:
        print(f"\n⚠️  安裝失敗的套件:")
        for package in all_failed:
            print(f"  ❌ {package}")
        print(f"\n💡 提示: 失敗的套件可以稍後手動安裝：")
        for package in all_failed:
            print(f"  pip install {package}")
    
    # 驗證核心套件
    print(f"\n🔍 驗證核心套件...")
    core_packages = ["streamlit", "pandas", "numpy", "sklearn"]
    missing_core = []
    
    for package in core_packages:
        if not check_package_installed(package):
            missing_core.append(package)
    
    if missing_core:
        print(f"❌ 核心套件缺失: {', '.join(missing_core)}")
        print("⚠️  專案可能無法正常運行，請檢查安裝狀況")
        return False
    else:
        print("✅ 所有核心套件驗證通過！")
    
    print(f"\n🎉 安裝完成！現在可以執行 D-Flare 專案了")
    print("💡 執行指令: python launch_unified_dashboard.py")
    
    return len(all_failed) == 0


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n\n⚠️  安裝被使用者中斷")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 安裝過程中發生錯誤: {e}")
        sys.exit(1)