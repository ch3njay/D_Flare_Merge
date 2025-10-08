
        else:
            # 未知格式，嘗試各種方法
            print("⚠️ 未知格式，嘗試各種載入方法...")
            return self._load_with_fallback_methods(file_path)