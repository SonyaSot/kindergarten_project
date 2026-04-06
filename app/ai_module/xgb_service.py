"""
app/ai_module/xgb_service.py - ИИ прогноз посещаемости на XGBoost
ИСПРАВЛЕННАЯ ВЕРСИЯ: конвертация numpy типов для совместимости с FastAPI
"""

import pandas as pd
import numpy as np
import xgboost as xgb
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from app.models import Attendance, Child, AttendanceStatus
import os

MODEL_PATH = "app/ai_module/xgb_model.json"

class XGBPredictor:
    def __init__(self, db: Session):
        self.db = db
        self.model = None
    
    def prepare_data(self) -> pd.DataFrame:
        """Подготовить данные: один пример = один день для одной группы"""
        records = self.db.query(Attendance).join(Child).filter(
            Attendance.date >= date.today() - timedelta(days=365),
            Attendance.status != AttendanceStatus.NOT_MARKED
        ).all()
        
        from collections import defaultdict
        grouped = defaultdict(lambda: {"present": 0, "total": 0})
        
        for r in records:
            key = (r.date, r.child.group_id)
            grouped[key]["total"] += 1
            if r.status == AttendanceStatus.PRESENT:
                grouped[key]["present"] += 1
        
        data = []
        for (date_, group_id), counts in grouped.items():
            if counts["total"] == 0:
                continue
            rate = counts["present"] / counts["total"]
            features = {
                "weekday": int(date_.weekday()),
                "month": int(date_.month),
                "is_monday": 1 if date_.weekday() == 0 else 0,
                "is_friday": 1 if date_.weekday() == 4 else 0,
                "is_winter": 1 if date_.month in [12, 1, 2] else 0,
                "is_weekend": 1 if date_.weekday() >= 5 else 0,
                "group_id": int(group_id),
                "target": float(rate)
            }
            data.append(features)
        
        return pd.DataFrame(data)
    
    def train_model(self) -> bool:
        """Обучить модель"""
        print("Обучение модели XGBoost")
        df = self.prepare_data()
        
        if len(df) < 10:
            print("⚠️ Недостаточно данных")
            return False
        
        X = df.drop("target", axis=1)
        y = df["target"]
        
        self.model = xgb.XGBRegressor(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.1,
            random_state=42
        )
        
        self.model.fit(X, y)
        
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        self.model.save_model(MODEL_PATH)
        print("Модель сохранена")
        return True
    
    def load_model(self) -> bool:
        """Загрузить модель"""
        if os.path.exists(MODEL_PATH):
            self.model = xgb.XGBRegressor()
            self.model.load_model(MODEL_PATH)
            return True
        return False
    
    def predict_group(self, group_id: int, target_date: date = None) -> dict:
        """Прогноз для группы"""
        if target_date is None:
            target_date = date.today() + timedelta(days=1)
        
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
        
        features = {
            "weekday": int(target_date.weekday()),
            "month": int(target_date.month),
            "is_monday": 1 if target_date.weekday() == 0 else 0,
            "is_friday": 1 if target_date.weekday() == 4 else 0,
            "is_winter": 1 if target_date.month in [12, 1, 2] else 0,
            "is_weekend": 1 if target_date.weekday() >= 5 else 0,
            "group_id": int(group_id)
        }
        
        X_pred = pd.DataFrame([features])
        
        # Предсказываем и конвертируем numpy.float32 → float
        predicted_rate = float(self.model.predict(X_pred)[0])
        
        # Ограничиваем диапазон
        predicted_rate = max(0.0, min(1.0, predicted_rate))
        
        # Считаем ожидаемое количество детей (конвертируем в int)
        expected_count = int(round(predicted_rate * total_children))
        rate_percent = round(float(predicted_rate * 100), 2)
        
        # Определяем уровень риска
        if rate_percent >= 85:
            risk = "low"
        elif rate_percent >= 70:
            risk = "medium"
        else:
            risk = "high"
        
        # ВОЗВРАЩАЕМ ТОЛЬКО PYTHON-ТИПЫ (не numpy!)
        return {
            "group_id": int(group_id),
            "prediction_date": str(target_date.isoformat()),
            "expected_attendance": int(expected_count),
            "total_children": int(total_children),
            "attendance_rate": float(rate_percent),
            "risk_level": str(risk),
            "model_type": str("XGBoost Regressor")
        }