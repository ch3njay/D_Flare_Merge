#!/usr/bin/env python3
"""
完整測試套件執行器 - 運行所有測試並生成詳細報告
"""
import sys
import unittest
import warnings
import time
import json
from pathlib import Path
from io import StringIO
from datetime import datetime

# 添加項目根目錄到路徑
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestResultCollector:
    """測試結果收集器"""
    
    def __init__(self):
        self.results = {
            'start_time': None,
            'end_time': None,
            'duration': 0,
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'error_tests': 0,
            'skipped_tests': 0,
            'test_suites': {},
            'failures': [],
            'errors': [],
            'summary': {}
        }
    
    def add_test_result(self, suite_name, result):
        """添加測試結果"""
        self.results['test_suites'][suite_name] = {
            'tests_run': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'skipped': len(getattr(result, 'skipped', [])),
            'success_rate': 0
        }
        
        if result.testsRun > 0:
            success_count = (result.testsRun - len(result.failures) - 
                           len(result.errors) - len(getattr(result, 'skipped', [])))
            self.results['test_suites'][suite_name]['success_rate'] = (
                success_count / result.testsRun * 100
            )
        
        # 收集失敗和錯誤詳情
        for test, traceback in result.failures:
            self.results['failures'].append({
                'suite': suite_name,
                'test': str(test),
                'traceback': traceback
            })
        
        for test, traceback in result.errors:
            self.results['errors'].append({
                'suite': suite_name,
                'test': str(test),
                'traceback': traceback
            })
    
    def finalize(self):
        """完成結果統計"""
        self.results['end_time'] = datetime.now()
        if self.results['start_time']:
            duration = self.results['end_time'] - self.results['start_time']
            self.results['duration'] = duration.total_seconds()
        
        # 計算總統計
        for suite_results in self.results['test_suites'].values():
            self.results['total_tests'] += suite_results['tests_run']
            self.results['failed_tests'] += suite_results['failures']
            self.results['error_tests'] += suite_results['errors']
            self.results['skipped_tests'] += suite_results['skipped']
        
        self.results['passed_tests'] = (
            self.results['total_tests'] - 
            self.results['failed_tests'] - 
            self.results['error_tests'] - 
            self.results['skipped_tests']
        )
        
        # 生成摘要
        if self.results['total_tests'] > 0:
            success_rate = (self.results['passed_tests'] / 
                          self.results['total_tests'] * 100)
        else:
            success_rate = 0
        
        self.results['summary'] = {
            'overall_success_rate': success_rate,
            'status': 'PASSED' if success_rate >= 80 else 'FAILED',
            'recommendation': self._get_recommendation(success_rate)
        }
    
    def _get_recommendation(self, success_rate):
        """獲取建議"""
        if success_rate >= 95:
            return "系統狀態優秀，所有功能正常運行"
        elif success_rate >= 80:
            return "系統狀態良好，建議檢查失敗的測試案例"
        elif success_rate >= 60:
            return "系統存在問題，需要修復失敗的測試案例"
        else:
            return "系統存在嚴重問題，需要立即修復"


def run_test_suite(test_module_name, suite_name):
    """運行單個測試套件"""
    print(f"\n{'='*60}")
    print(f"運行測試套件: {suite_name}")
    print(f"{'='*60}")
    
    try:
        # 動態導入測試模組
        test_module = __import__(test_module_name)
        
        # 創建測試套件
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(test_module)
        
        # 運行測試
        stream = StringIO()
        runner = unittest.TextTestRunner(
            stream=stream, 
            verbosity=2, 
            buffer=True
        )
        
        result = runner.run(suite)
        
        # 輸出結果
        output = stream.getvalue()
        print(output)
        
        return result
        
    except ImportError as e:
        print(f"❌ 無法導入測試模組 {test_module_name}: {e}")
        return None
    except Exception as e:
        print(f"❌ 運行測試套件時發生錯誤: {e}")
        return None


def generate_html_report(results, output_file):
    """生成HTML格式的測試報告"""
    html_content = f"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>D-FLARE 測試報告</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
               margin: 0; padding: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; 
                     background: white; padding: 30px; border-radius: 10px; 
                     box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
                   gap: 20px; margin-bottom: 30px; }}
        .stat-card {{ background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; }}
        .stat-number {{ font-size: 2em; font-weight: bold; margin-bottom: 5px; }}
        .passed {{ color: #28a745; }}
        .failed {{ color: #dc3545; }}
        .error {{ color: #fd7e14; }}
        .skipped {{ color: #6c757d; }}
        .suite-results {{ margin-top: 30px; }}
        .suite {{ margin-bottom: 20px; padding: 15px; border-left: 4px solid #007bff; background: #f8f9fa; }}
        .suite-name {{ font-size: 1.2em; font-weight: bold; margin-bottom: 10px; }}
        .progress-bar {{ background: #e9ecef; height: 20px; border-radius: 10px; overflow: hidden; }}
        .progress-fill {{ height: 100%; background: #28a745; transition: width 0.3s ease; }}
        .details {{ margin-top: 20px; }}
        .failure, .error {{ margin: 10px 0; padding: 10px; background: #f8d7da; border-radius: 5px; }}
        .timestamp {{ color: #6c757d; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ D-FLARE 檔案調動後全面測試報告</h1>
            <p class="timestamp">測試時間: {results['start_time'].strftime('%Y-%m-%d %H:%M:%S')} - {results['end_time'].strftime('%H:%M:%S')}</p>
            <p>測試持續時間: {results['duration']:.2f} 秒</p>
        </div>
        
        <div class="summary">
            <div class="stat-card">
                <div class="stat-number">{results['total_tests']}</div>
                <div>總測試數</div>
            </div>
            <div class="stat-card">
                <div class="stat-number passed">{results['passed_tests']}</div>
                <div>通過測試</div>
            </div>
            <div class="stat-card">
                <div class="stat-number failed">{results['failed_tests']}</div>
                <div>失敗測試</div>
            </div>
            <div class="stat-card">
                <div class="stat-number error">{results['error_tests']}</div>
                <div>錯誤測試</div>
            </div>
        </div>
        
        <div style="text-align: center; margin: 20px 0;">
            <h2 style="color: {'#28a745' if results['summary']['status'] == 'PASSED' else '#dc3545'};">
                整體狀態: {results['summary']['status']}
            </h2>
            <p><strong>成功率: {results['summary']['overall_success_rate']:.1f}%</strong></p>
            <p>{results['summary']['recommendation']}</p>
        </div>
        
        <div class="suite-results">
            <h3>各測試套件詳細結果</h3>
"""
    
    for suite_name, suite_result in results['test_suites'].items():
        success_rate = suite_result['success_rate']
        html_content += f"""
            <div class="suite">
                <div class="suite-name">{suite_name}</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {success_rate}%;"></div>
                </div>
                <p>成功率: {success_rate:.1f}% ({suite_result['tests_run']} 測試, {suite_result['failures']} 失敗, {suite_result['errors']} 錯誤)</p>
            </div>
        """
    
    if results['failures'] or results['errors']:
        html_content += """
            <div class="details">
                <h3>失敗和錯誤詳情</h3>
        """
        
        for failure in results['failures']:
            html_content += f"""
                <div class="failure">
                    <strong>失敗: {failure['suite']} - {failure['test']}</strong>
                    <pre>{failure['traceback'][:500]}...</pre>
                </div>
            """
        
        for error in results['errors']:
            html_content += f"""
                <div class="error">
                    <strong>錯誤: {error['suite']} - {error['test']}</strong>
                    <pre>{error['traceback'][:500]}...</pre>
                </div>
            """
        
        html_content += "</div>"
    
    html_content += """
        </div>
    </div>
</body>
</html>
    """
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)


def main():
    """主測試執行函數"""
    print("🚀 開始執行 D-FLARE 檔案調動後的全面測試套件")
    print("="*80)
    
    # 抑制警告訊息
    warnings.filterwarnings("ignore")
    
    # 初始化結果收集器
    collector = TestResultCollector()
    collector.results['start_time'] = datetime.now()
    
    # 定義測試套件
    test_suites = [
        ('test_module_imports_comprehensive', '模組導入測試'),
        ('test_dependency_relations', '依賴關係測試'),
        ('test_functionality_comprehensive', '功能完整性測試'),
        ('test_startup_flow', '啟動流程測試'),
        ('test_integration_comprehensive', '整合測試')
    ]
    
    # 執行所有測試套件
    for test_module, suite_name in test_suites:
        result = run_test_suite(test_module, suite_name)
        if result:
            collector.add_test_result(suite_name, result)
    
    # 完成統計
    collector.finalize()
    
    # 輸出最終報告
    print("\n" + "="*80)
    print("📊 最終測試報告")
    print("="*80)
    
    print(f"總測試數: {collector.results['total_tests']}")
    print(f"✅ 通過: {collector.results['passed_tests']}")
    print(f"❌ 失敗: {collector.results['failed_tests']}")
    print(f"🔥 錯誤: {collector.results['error_tests']}")
    print(f"⏭️  跳過: {collector.results['skipped_tests']}")
    print(f"📈 成功率: {collector.results['summary']['overall_success_rate']:.1f}%")
    print(f"⏱️  總耗時: {collector.results['duration']:.2f} 秒")
    
    print(f"\n🎯 整體狀態: {collector.results['summary']['status']}")
    print(f"💡 建議: {collector.results['summary']['recommendation']}")
    
    # 生成詳細報告檔案
    reports_dir = PROJECT_ROOT / "tests" / "reports"
    reports_dir.mkdir(exist_ok=True)
    
    # JSON報告
    json_report_file = reports_dir / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(json_report_file, 'w', encoding='utf-8') as f:
        json.dump(collector.results, f, ensure_ascii=False, indent=2, default=str)
    
    # HTML報告
    html_report_file = reports_dir / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    generate_html_report(collector.results, html_report_file)
    
    print(f"\n📄 詳細報告已生成:")
    print(f"  JSON: {json_report_file}")
    print(f"  HTML: {html_report_file}")
    
    # 返回適當的退出碼
    return 0 if collector.results['summary']['status'] == 'PASSED' else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)