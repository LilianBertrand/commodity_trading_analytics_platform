from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split


def build_features(history: pd.DataFrame) -> pd.DataFrame:
    df = history.copy().dropna().reset_index(drop=True)
    df["ret_1d"] = df["price"].pct_change()
    df["ret_5d"] = df["price"].pct_change(5)
    df["vol_20d"] = df["ret_1d"].rolling(20).std() * np.sqrt(252)
    df["ma_20"] = df["price"].rolling(20).mean()
    df["ma_60"] = df["price"].rolling(60).mean()
    df["ma_gap"] = df["ma_20"] / df["ma_60"] - 1
    df["target_up_next_day"] = (df["price"].shift(-1) > df["price"]).astype(int)
    return df.dropna()


def train_direction_model(history: pd.DataFrame) -> dict:
    df = build_features(history)
    features = ["ret_1d", "ret_5d", "vol_20d", "ma_gap"]
    if len(df) < 80:
        return {"available": False, "message": "Not enough observations for ML model."}
    X = df[features]
    y = df["target_up_next_day"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.30, shuffle=False)
    model = RandomForestClassifier(n_estimators=100, max_depth=4, random_state=42)
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    accuracy = accuracy_score(y_test, preds)
    latest_proba_up = model.predict_proba(X.tail(1))[0][1]
    return {"available": True, "model": model, "accuracy": accuracy, "latest_proba_up": latest_proba_up, "features": features}


def anomaly_detection(history: pd.DataFrame) -> pd.DataFrame:
    df = build_features(history)
    features = ["ret_1d", "ret_5d", "vol_20d", "ma_gap"]
    if len(df) < 80:
        df["anomaly_score"] = np.nan
        df["is_anomaly"] = False
        return df
    model = IsolationForest(contamination=0.05, random_state=42)
    df["anomaly_raw"] = model.fit_predict(df[features])
    df["anomaly_score"] = model.decision_function(df[features])
    df["is_anomaly"] = df["anomaly_raw"] == -1
    return df
