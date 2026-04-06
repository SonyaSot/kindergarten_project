import pandas as pd
import numpy as np
import xgboost as xgb
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from app.models import Payment, Child
import os

MODEL_PATH_RATE = "app/ai_module/payment_model_rate.json"
MODEL_PATH_AMOUNT = "app/ai_module/payment_model_amount.json"

def to_python(obj):
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: to_python(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [to_python(v) for v in obj]
    return obj

class PaymentPredictor:
    def __init__(self, db: Session):
        self.db = db
        self.model_rate = None
        self.model_amount = None
    
    def prepare_data(self) -> pd.DataFrame:
        """Подготовить данные для обучения"""
        # ✅ ИСПРАВЛЕНО: Payment.month (не date!)
        payments = self.db.query(Payment).filter(
            Payment.month >= date.today() - timedelta(days=365)
        ).all()
        
        if not payments:
            return pd.DataFrame()
        
        from collections import defaultdict
        grouped = defaultdict(lambda: {"paid": 0, "total": 0, "amount": 0})
        
        for p in payments:
            child = self.db.query(Child).filter(Child.id == p.child_id).first()
            if not child:
                continue
            
            # ✅ ИСПРАВЛЕНО: p.month (не p.date!)
            key = (p.month.year, p.month.month, child.group_id)
            grouped[key]["total"] += 1
            grouped[key]["paid"] += 1 if p.status == "paid" else 0
            grouped[key]["amount"] += p.paid_amount if p.paid_amount else 0
        
        data = []
        for (year, month, group_id), counts in grouped.items():
            if counts["total"] == 0:
                continue
            
            payment_rate = counts["paid"] / counts["total"]
            total_amount = counts["amount"]
            
            features = {
                "month": int(month),
                "is_winter": 1 if month in [12, 1, 2] else 0,
                "is_spring": 1 if month in [3, 4, 5] else 0,
                "is_summer": 1 if month in [6, 7, 8] else 0,
                "is_autumn": 1 if month in [9, 10, 11] else 0,
                "is_start_of_year": 1 if month == 1 else 0,
                "group_id": int(group_id),
                "target_rate": float(payment_rate),
                "target_amount": float(total_amount)
            }
            data.append(features)
        
        return pd.DataFrame(data) if data else pd.DataFrame()
    
    def train_model(self) -> bool:
        print("🔄 Обучение модели прогноза оплат...")
        df = self.prepare_data()
        
        if len(df) < 5:
            print("⚠️ Недостаточно данных")
            return False
        
        X = df.drop(["target_rate", "target_amount"], axis=1)
        y_rate = df["target_rate"]
        y_amount = df["target_amount"]
        
        self.model_rate = xgb.XGBRegressor(n_estimators=50, max_depth=3, learning_rate=0.1, random_state=42)
        self.model_rate.fit(X, y_rate)
        
        self.model_amount = xgb.XGBRegressor(n_estimators=50, max_depth=3, learning_rate=0.1, random_state=42)
        self.model_amount.fit(X, y_amount)
        
        os.makedirs(os.path.dirname(MODEL_PATH_RATE), exist_ok=True)
        self.model_rate.save_model(MODEL_PATH_RATE)
        self.model_amount.save_model(MODEL_PATH_AMOUNT)
        
        print("✅ Модель сохранена")
        return True
    
    def load_model(self) -> bool:
        if os.path.exists(MODEL_PATH_RATE) and os.path.exists(MODEL_PATH_AMOUNT):
            self.model_rate = xgb.XGBRegressor()
            self.model_rate.load_model(MODEL_PATH_RATE)
            self.model_amount = xgb.XGBRegressor()
            self.model_amount.load_model(MODEL_PATH_AMOUNT)
            return True
        return False
    
    def predict_payment(self, group_id: int, target_month: date = None) -> dict:
        if target_month is None:
            target_month = date.today().replace(day=1)
            if target_month.month == 12:
                target_month = target_month.replace(year=target_month.year + 1, month=1)
            else:
                target_month = target_month.replace(month=target_month.month + 1)
        
        if not self.load_model():
            self.train_model()
            if not self.load_model():
                return {"error": "Не удалось загрузить модель"}
        
        children = self.db.query(Child).filter(
            Child.group_id == group_id,
            Child.is_active == True
        ).all()
        total_children = len(children)
        
        if total_children == 0:
            return {"error": "Нет активных детей"}
        
        avg_fee_per_child = 5000
        
        features = {
            "month": int(target_month.month),
            "is_winter": 1 if target_month.month in [12, 1, 2] else 0,
            "is_spring": 1 if target_month.month in [3, 4, 5] else 0,
            "is_summer": 1 if target_month.month in [6, 7, 8] else 0,
            "is_autumn": 1 if target_month.month in [9, 10, 11] else 0,
            "is_start_of_year": 1 if target_month.month == 1 else 0,
            "group_id": int(group_id)
        }
        
        X_pred = pd.DataFrame([features])
        
        predicted_rate = float(self.model_rate.predict(X_pred)[0].item())
        predicted_rate = max(0.0, min(1.0, predicted_rate))
        
        expected_paid_children = int(round(predicted_rate * total_children))
        expected_total = float(predicted_rate * total_children * avg_fee_per_child)
        
        if predicted_rate >= 0.9:
            risk = "low"
        elif predicted_rate >= 0.7:
            risk = "medium"
        else:
            risk = "high"
        
        result = {
            "group_id": int(group_id),
            "prediction_month": int(target_month.month),
            "prediction_year": int(target_month.year),
            "total_children": int(total_children),
            "expected_paid_children": int(expected_paid_children),
            "payment_rate": round(float(predicted_rate * 100), 2),
            "expected_total_amount": round(float(expected_total), 2),
            "average_fee_per_child": int(avg_fee_per_child),
            "risk_level": str(risk),
            "model_type": "XGBoost Regressor"
        }
        
        return to_python(result)