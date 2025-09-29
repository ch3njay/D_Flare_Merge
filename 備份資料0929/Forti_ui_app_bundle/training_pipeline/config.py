# Binary classification config
CONFIG_BINARY = {
    "TARGET_COLUMN": "is_attack",
    "DROP_COLUMNS": [
        "idseq", "datetime", "srcip", "dstip",
        "crscore", "crlevel", "is_attack",
        "proto_port", "sub_action", "svc_action"
    ],
    "VALID_SIZE": 0.2,
    "RANDOM_STATE": 100,
    "MODEL_PARAMS": {
        "XGB": {
            "n_estimators": 114,
            "max_depth": 7,
            "learning_rate": 0.05194027577712326,
            "subsample": 0.6482232909747706,
            "colsample_bytree": 0.6125623581444746,
            "tree_method": "hist",

            "device": "cpu",

            "eval_metric": "logloss"
        },
        "LGB": {
            "max_depth": 12,
            "learning_rate": 0.29348213117409244,
            "num_leaves": 108,
            "min_child_samples": 1

        },
        "CAT": {
            "depth": 6,
            "learning_rate": 0.23335235514899935,
            "iterations": 164,
            "task_type": "GPU",
            "devices": "0"
        },
        "RF": {
            "n_estimators": 198,
            "max_depth": 11
        },
        "ET": {
            "n_estimators": 192,
            "max_depth": 12
        }
    },
    "ENSEMBLE_SETTINGS": {
        "STACK_CV": 5,
        "VOTING": "soft",
        "THRESHOLD": 0.33,
        "SEARCH": "none"
    }
}

# Multiclass classification config
CONFIG_MULTICLASS = {
    "TARGET_COLUMN": "crlevel",
    "DROP_COLUMNS": [
        "idseq", "datetime", "srcip", "dstip",
        "crscore", "crlevel", "is_attack",
        "proto_port", "sub_action", "svc_action"
    ],
    "VALID_SIZE": 0.2,
    "RANDOM_STATE": 100,
    "MODEL_PARAMS": {
        "XGB": {
            "n_estimators": 189,
            "max_depth": 8,
            "learning_rate": 0.1898717379219999,
            "subsample": 0.6875100692343238,
            "colsample_bytree": 0.5147427892922118,
            "tree_method": "hist",
            "device": "cpu",

            "eval_metric": "mlogloss"
        },
        "LGB": {
            "n_estimators": 360,
            "max_depth": -1,
            "learning_rate": 0.06919566270449405,
            "num_leaves": 31,
            "min_child_samples": 1

        },
        "CAT": {
            "depth": 10,
            "learning_rate": 0.0768152029814235,
            "iterations": 249,
            "task_type": "GPU",
            "devices": "0"
        },
        "RF": {
            "n_estimators": 167,
            "max_depth": 10
        },
        "ET": {
            "n_estimators": 227,
            "max_depth": 12
        }
    },
    "ENSEMBLE_SETTINGS": {
        "STACK_CV": 5,
        "VOTING": "soft",
        "THRESHOLD": 0.33,
        "SEARCH": "none"
    }
}
