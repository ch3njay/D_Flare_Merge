# Binary classification config  # 二元分類設定
CONFIG_BINARY = {  # 二元分類配置
    "TARGET_COLUMN": "is_attack",  # 目標欄位（標籤）：是否為攻擊
    "DROP_COLUMNS": [  # 要丟棄的欄位（不納入訓練）
        "idseq", "datetime", "srcip", "dstip",
        "crscore", "crlevel", "is_attack",
        "proto_port", "sub_action", "svc_action"
    ],  # 丟棄欄位清單結束
    "VALID_SIZE": 0.2,  # 驗證集比例
    "RANDOM_STATE": 100,  # 隨機種子（可重現性）
    "MODEL_PARAMS": {  # 模型參數集合
        "XGB": {  # XGBoost 參數
            "n_estimators": 114,  # 樹的數量
            "max_depth": 7,  # 樹的最大深度
            "learning_rate": 0.05194027577712326,  # 學習率
            "subsample": 0.6482232909747706,  # 行抽樣比例
            "colsample_bytree": 0.6125623581444746,  # 列抽樣比例（每棵樹）
            "tree_method": "hist",  # 建樹方法
            "device": "cpu",  # 計算設備（CPU/GPU）
            "eval_metric": "logloss"  # 評估指標：對數損失（logloss）
        },
        "LGB": {  # LightGBM 參數
            "max_depth": 12,  # 最大深度
            "learning_rate": 0.29348213117409244,  # 學習率
            "num_leaves": 108,  # 葉子節點數（影響複雜度）
            "min_child_samples": 1  # 葉節點最小樣本數
        },
        "CAT": {  # CatBoost 參數
            "depth": 6,  # 樹的深度
            "learning_rate": 0.23335235514899935,  # 學習率
            "iterations": 164,  # 迭代次數（樹的數量）
            "task_type": "CPU"  # 計算設備類型
        },
        "RF": {  # 隨機森林參數
            "n_estimators": 198,  # 樹的數量
            "max_depth": 11  # 最大深度
        },
        "ET": {  # 極端隨機樹（Extra Trees）參數
            "n_estimators": 192,  # 樹的數量
            "max_depth": 12  # 最大深度
        }
    },
    "ENSEMBLE_SETTINGS": {  # 集成模型設定
        "STACK_CV": 5,  # 堆疊時的交叉驗證折數
        "VOTING": "soft",  # 投票方式（soft/probability 加權）
        "THRESHOLD": 0.33,  # 二元分類的概率閾值
        "SEARCH": "none"  # 超參數搜尋方式（none/ grid/random 等）
    }
}

# Multiclass classification config  # 多類別分類設定
CONFIG_MULTICLASS = {  # 多類別配置
    "TARGET_COLUMN": "crlevel",  # 目標欄位：危險等級（多類別）
    "DROP_COLUMNS": [  # 要丟棄的欄位（不納入訓練）
        "idseq", "datetime", "srcip", "dstip",
        "crscore", "crlevel", "is_attack",
        "proto_port", "sub_action", "svc_action"
    ],  # 丟棄欄位清單結束
    "VALID_SIZE": 0.2,  # 驗證集比例
    "RANDOM_STATE": 100,  # 隨機種子（可重現性）
    "MODEL_PARAMS": {  # 模型參數集合
        "XGB": {  # XGBoost 參數（多類別）
            "n_estimators": 189,  # 樹的數量
            "max_depth": 8,  # 最大深度
            "learning_rate": 0.1898717379219999,  # 學習率
            "subsample": 0.6875100692343238,  # 行抽樣比例
            "colsample_bytree": 0.5147427892922118,  # 列抽樣比例
            "tree_method": "hist",  # 建樹方法
            "device": "cpu",  # 計算設備
            "eval_metric": "mlogloss"  # 評估指標：多類別對數損失
        },
        "LGB": {  # LightGBM 參數（多類別）
            "n_estimators": 360,  # 樹的數量
            "max_depth": -1,  # 最大深度（-1 表示不限制）
            "learning_rate": 0.06919566270449405,  # 學習率
            "num_leaves": 31,  # 葉子節點數
            "min_child_samples": 1  # 葉節點最小樣本數
        },
        "CAT": {  # CatBoost 參數（多類別）
            "depth": 10,  # 樹的深度
            "learning_rate": 0.0768152029814235,  # 學習率
            "iterations": 249,  # 迭代次數
            "task_type": "CPU"  # 計算設備類型
        },
        "RF": {  # 隨機森林參數（多類別）
            "n_estimators": 167,  # 樹的數量
            "max_depth": 10  # 最大深度
        },
        "ET": {  # 極端隨機樹參數（多類別）
            "n_estimators": 227,  # 樹的數量
            "max_depth": 12  # 最大深度
        }
    },
    "ENSEMBLE_SETTINGS": {  # 集成模型設定（多類別）
        "STACK_CV": 5,  # 堆疊交叉驗證折數
        "VOTING": "soft",  # 投票方式
        "THRESHOLD": 0.33,  # 多類別情況下可能未使用（保留）
        "SEARCH": "none"  # 超參數搜尋方式
    }
}
