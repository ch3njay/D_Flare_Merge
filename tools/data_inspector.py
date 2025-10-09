"""資料檢查工具 - 協助使用者分析資料結構並識別可能的目標欄位"""
import pandas as pd
import sys
from typing import List, Dict, Any


class DataInspector:
    """資料檢查與分析工具"""
    
    def __init__(self, csv_path: str):
        """
        初始化資料檢查器
        
        Args:
            csv_path: CSV 檔案路徑
        """
        self.csv_path = csv_path
        self.df = None
        
    def load_and_inspect(self) -> Dict[str, Any]:
        """載入並檢查資料"""
        print(f"📂 載入資料：{self.csv_path}")
        
        try:
            self.df = pd.read_csv(self.csv_path, encoding='utf-8-sig')
        except Exception as e:
            print(f"❌ UTF-8 編碼失敗，嘗試其他編碼...")
            try:
                self.df = pd.read_csv(self.csv_path, encoding='cp950')
            except Exception as e2:
                print(f"❌ 讀取失敗：{e2}")
                return {"success": False, "error": str(e2)}
        
        print(f"✅ 成功載入 {len(self.df)} 筆資料，{len(self.df.columns)} 個欄位\n")
        
        # 執行完整分析
        analysis = {
            "success": True,
            "basic_info": self._get_basic_info(),
            "column_analysis": self._analyze_columns(),
            "target_candidates": self._find_target_candidates(),
            "recommendations": self._generate_recommendations()
        }
        
        return analysis
    
    def _get_basic_info(self) -> Dict[str, Any]:
        """取得基本資料資訊"""
        return {
            "rows": len(self.df),
            "columns": len(self.df.columns),
            "column_names": list(self.df.columns),
            "memory_usage": f"{self.df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB"
        }
    
    def _analyze_columns(self) -> List[Dict[str, Any]]:
        """分析每個欄位的特性"""
        column_info = []
        
        for col in self.df.columns:
            info = {
                "name": col,
                "dtype": str(self.df[col].dtype),
                "unique_count": self.df[col].nunique(),
                "null_count": self.df[col].isnull().sum(),
                "null_percentage": f"{self.df[col].isnull().sum() / len(self.df) * 100:.2f}%"
            }
            
            # 如果是數值型，提供統計資訊
            if pd.api.types.is_numeric_dtype(self.df[col]):
                info["min"] = self.df[col].min()
                info["max"] = self.df[col].max()
                info["mean"] = f"{self.df[col].mean():.2f}"
                info["is_numeric"] = True
            else:
                info["is_numeric"] = False
                # 顯示前幾個唯一值（如果不太多）
                if info["unique_count"] <= 10:
                    info["sample_values"] = list(self.df[col].unique()[:5])
            
            column_info.append(info)
        
        return column_info
    
    def _find_target_candidates(self) -> List[Dict[str, Any]]:
        """尋找可能的目標欄位候選"""
        candidates = []
        
        # 常見標籤欄位名稱
        common_names = [
            'label', 'target', 'class', 'y', 'attack_type', 'is_attack',
            'category', 'classification', 'type', 'severity', 'crlevel',
            'priority', 'risk_level', 'threat_level', 'status'
        ]
        
        for col in self.df.columns:
            reasons = []
            score = 0
            
            # 1. 檢查名稱是否匹配常見標籤名稱
            if col.lower() in common_names:
                reasons.append(f"欄位名稱 '{col}' 是常見的標籤欄位名稱")
                score += 50
            
            # 2. 檢查是否為數值型且唯一值較少
            if pd.api.types.is_numeric_dtype(self.df[col]):
                unique_count = self.df[col].nunique()
                total_count = len(self.df)
                unique_ratio = unique_count / total_count
                
                if unique_count < 20:
                    reasons.append(f"唯一值數量少（{unique_count} 個）")
                    score += 30
                
                if unique_ratio < 0.01:
                    reasons.append(f"唯一值比例低（{unique_ratio*100:.4f}%）")
                    score += 20
                
                # 檢查是否為二元分類（只有 0/1 或類似值）
                unique_values = set(self.df[col].dropna().unique())
                if unique_values.issubset({0, 1}) or unique_values.issubset({'0', '1'}):
                    reasons.append("看起來是二元分類（0/1）")
                    score += 40
            
            # 3. 如果分數足夠高，加入候選清單
            if score >= 30:
                value_counts = self.df[col].value_counts().to_dict()
                candidates.append({
                    "column": col,
                    "score": score,
                    "reasons": reasons,
                    "unique_count": self.df[col].nunique(),
                    "value_distribution": value_counts
                })
        
        # 按分數排序
        candidates.sort(key=lambda x: x["score"], reverse=True)
        
        return candidates
    
    def _generate_recommendations(self) -> List[str]:
        """產生建議"""
        recommendations = []
        
        candidates = self._find_target_candidates()
        
        if candidates:
            top_candidate = candidates[0]
            recommendations.append(
                f"✅ 建議使用 '{top_candidate['column']}' 作為目標欄位 "
                f"(信心分數: {top_candidate['score']}/100)"
            )
            recommendations.append(
                f"   原因：{'; '.join(top_candidate['reasons'])}"
            )
            
            # 如果有多個候選
            if len(candidates) > 1:
                recommendations.append("\n其他可能的目標欄位：")
                for cand in candidates[1:3]:  # 顯示前 2 個替代選項
                    recommendations.append(
                        f"  - {cand['column']} (分數: {cand['score']}/100)"
                    )
        else:
            recommendations.append(
                "❌ 未找到明顯的目標欄位候選"
            )
            recommendations.append(
                "💡 您可能需要：\n"
                "   1. 手動新增標籤欄位（例如 'is_attack' 或 'label'）\n"
                "   2. 使用現有欄位進行轉換（例如根據某些條件建立標籤）\n"
                "   3. 使用無監督學習方法（異常偵測等）"
            )
        
        # 檢查資料品質問題
        null_columns = [col for col in self.df.columns 
                       if self.df[col].isnull().sum() > len(self.df) * 0.5]
        if null_columns:
            recommendations.append(
                f"\n⚠️ 以下欄位缺失值超過 50%，建議移除：\n   "
                f"{', '.join(null_columns)}"
            )
        
        return recommendations
    
    def print_report(self, analysis: Dict[str, Any]):
        """印出完整的分析報告"""
        if not analysis["success"]:
            print(f"❌ 分析失敗：{analysis['error']}")
            return
        
        print("\n" + "="*60)
        print("📊 資料分析報告")
        print("="*60)
        
        # 基本資訊
        info = analysis["basic_info"]
        print(f"\n📈 基本資訊：")
        print(f"  - 資料筆數：{info['rows']:,}")
        print(f"  - 欄位數量：{info['columns']}")
        print(f"  - 記憶體用量：{info['memory_usage']}")
        
        # 欄位分析
        print(f"\n📋 欄位詳細分析：")
        print(f"{'欄位名稱':<30} {'型別':<10} {'唯一值':<10} {'缺失值':<10}")
        print("-" * 60)
        for col_info in analysis["column_analysis"]:
            print(f"{col_info['name']:<30} "
                  f"{col_info['dtype']:<10} "
                  f"{col_info['unique_count']:<10} "
                  f"{col_info['null_percentage']:<10}")
        
        # 目標欄位候選
        print(f"\n🎯 可能的目標欄位候選：")
        candidates = analysis["target_candidates"]
        if candidates:
            for i, cand in enumerate(candidates[:3], 1):
                print(f"\n{i}. {cand['column']} (信心分數: {cand['score']}/100)")
                print(f"   原因：")
                for reason in cand['reasons']:
                    print(f"     - {reason}")
                print(f"   唯一值數量：{cand['unique_count']}")
                print(f"   值分佈：{cand['value_distribution']}")
        else:
            print("  ❌ 未找到明顯的目標欄位候選")
        
        # 建議
        print(f"\n💡 建議：")
        for rec in analysis["recommendations"]:
            print(f"  {rec}")
        
        print("\n" + "="*60)
        
    def export_report(self, analysis: Dict[str, Any], output_path: str = None):
        """匯出分析報告為 JSON"""
        if output_path is None:
            output_path = self.csv_path.replace('.csv', '_analysis.json')
        
        import json
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
        
        print(f"📄 分析報告已匯出至：{output_path}")


def main():
    """主程式"""
    if len(sys.argv) < 2:
        print("使用方式：python data_inspector.py <csv_file_path>")
        print("範例：python data_inspector.py C:\\Users\\U02020\\AppData\\Local\\Temp\\preprocessed_data.csv")
        return
    
    csv_path = sys.argv[1]
    
    inspector = DataInspector(csv_path)
    analysis = inspector.load_and_inspect()
    inspector.print_report(analysis)
    
    # 詢問是否匯出報告
    export = input("\n是否要匯出分析報告為 JSON？(y/n): ")
    if export.lower() == 'y':
        inspector.export_report(analysis)


if __name__ == "__main__":
    main()
