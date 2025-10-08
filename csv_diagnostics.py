"""
CSV 格式診斷工具
用於識別和修復常見的 CSV 格式問題
"""
import pandas as pd
import os
from typing import Dict, List, Tuple, Optional
import io


def diagnose_csv_file(file_path: str) -> Dict[str, any]:
    """
    診斷 CSV 文件的格式問題
    
    Args:
        file_path: CSV 文件路徑
        
    Returns:
        診斷報告字典
    """
    report = {
        "file_exists": os.path.exists(file_path),
        "file_size_mb": 0,
        "encoding_issues": False,
        "line_count": 0,
        "inconsistent_fields": [],
        "problematic_lines": [],
        "suggested_fixes": [],
        "load_success": False,
        "error_message": None
    }
    
    if not report["file_exists"]:
        report["error_message"] = f"文件不存在: {file_path}"
        return report
    
    # 獲取文件大小
    report["file_size_mb"] = os.path.getsize(file_path) / (1024 * 1024)
    
    try:
        # 檢查編碼問題
        with open(file_path, 'r', encoding='utf-8') as f:
            first_lines = [f.readline() for _ in range(10)]
        
        # 分析第一行（標題行）
        if first_lines and first_lines[0]:
            header_fields = len(first_lines[0].split(','))
            report["expected_fields"] = header_fields
            
            # 檢查每行的欄位數量
            for i, line in enumerate(first_lines[1:], 2):
                if line.strip():
                    field_count = len(line.split(','))
                    if field_count != header_fields:
                        report["inconsistent_fields"].append({
                            "line": i,
                            "expected": header_fields,
                            "found": field_count,
                            "content": line.strip()[:100] + "..." if len(line) > 100 else line.strip()
                        })
        
        # 嘗試用不同方法載入
        load_attempts = [
            ("標準載入", lambda: pd.read_csv(file_path)),
            ("容錯模式", lambda: pd.read_csv(
                file_path, 
                error_bad_lines=False, 
                warn_bad_lines=False,
                on_bad_lines='skip'
            )),
            ("Python引擎", lambda: pd.read_csv(
                file_path, 
                sep=None, 
                engine='python', 
                quoting=3
            ))
        ]
        
        for method_name, load_func in load_attempts:
            try:
                df = load_func()
                report["load_success"] = True
                report["successful_method"] = method_name
                report["loaded_shape"] = df.shape
                report["columns"] = list(df.columns)
                break
            except Exception as e:
                report["load_attempts"] = report.get("load_attempts", [])
                report["load_attempts"].append({
                    "method": method_name,
                    "error": str(e)
                })
        
    except Exception as e:
        report["error_message"] = str(e)
    
    # 生成修復建議
    if report["inconsistent_fields"]:
        report["suggested_fixes"].append("欄位數量不一致 - 建議檢查數據中是否包含未轉義的逗號")
    
    if not report["load_success"]:
        report["suggested_fixes"].extend([
            "嘗試檢查文件編碼（建議使用 UTF-8）",
            "檢查分隔符是否為逗號",
            "檢查是否有未正確引用的文本字段",
            "嘗試移除或修復有問題的行"
        ])
    
    return report


def fix_csv_file(input_path: str, output_path: str) -> bool:
    """
    嘗試修復 CSV 文件的格式問題
    
    Args:
        input_path: 輸入文件路徑
        output_path: 輸出文件路徑
        
    Returns:
        修復是否成功
    """
    try:
        # 使用最寬鬆的參數讀取
        df = pd.read_csv(
            input_path,
            sep=None,
            engine='python',
            quoting=3,
            skipinitialspace=True,
            error_bad_lines=False,
            warn_bad_lines=False
        )
        
        # 保存修復後的文件
        df.to_csv(output_path, index=False, quoting=1)  # 強制引用所有文本
        return True
        
    except Exception as e:
        print(f"修復失敗: {e}")
        return False


def print_diagnostic_report(report: Dict[str, any]) -> None:
    """打印診斷報告"""
    print("=" * 60)
    print("CSV 文件診斷報告")
    print("=" * 60)
    
    if not report["file_exists"]:
        print(f"❌ {report['error_message']}")
        return
    
    print(f"📁 文件大小: {report['file_size_mb']:.2f} MB")
    
    if report["load_success"]:
        print(f"✅ 載入成功 (使用: {report['successful_method']})")
        print(f"📊 數據形狀: {report['loaded_shape']}")
        print(f"📋 欄位數量: {len(report['columns'])}")
    else:
        print("❌ 載入失敗")
        if report.get("load_attempts"):
            for attempt in report["load_attempts"]:
                print(f"   {attempt['method']}: {attempt['error']}")
    
    if report["inconsistent_fields"]:
        print("\n⚠️ 發現欄位數量不一致的行:")
        for issue in report["inconsistent_fields"][:5]:  # 只顯示前5個問題
            print(f"   第{issue['line']}行: 預期{issue['expected']}個欄位，發現{issue['found']}個")
            print(f"   內容: {issue['content']}")
    
    if report["suggested_fixes"]:
        print("\n💡 修復建議:")
        for i, fix in enumerate(report["suggested_fixes"], 1):
            print(f"   {i}. {fix}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("用法: python csv_diagnostics.py <csv_file_path> [--fix output_path]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    # 診斷文件
    report = diagnose_csv_file(input_file)
    print_diagnostic_report(report)
    
    # 如果指定了修復選項
    if len(sys.argv) >= 4 and sys.argv[2] == "--fix":
        output_file = sys.argv[3]
        print(f"\n🔧 嘗試修復文件...")
        if fix_csv_file(input_file, output_file):
            print(f"✅ 修復成功! 輸出文件: {output_file}")
        else:
            print("❌ 修復失敗")