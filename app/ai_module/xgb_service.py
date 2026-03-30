"""
app/ai_module/xgb_service.py - ИИ прогноз посещаемости на XGBoost
Без кэширования - просто и надёжно
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
        """Подготовить данные для обучения"""
        records = self.db.query(Attendance).join(Child).filter(
            Attendance.date >= date.today() - timedelta(days=365),
            Attendance.status != AttendanceStatus.NOT_MARKED
        ).all()
        
        data = []
        for r in records:
            features = {
                "weekday": r.date.weekday(),
                "month": r.date.month,
                "is_monday": 1 if r.date.weekday() == 0 else 0,
                "is_friday": 1 if r.date.weekday() == 4 else 0,
                "is_winter": 1 if r.date.month in [12, 1, 2] else 0,
                "child_age": self._calculate_age(r.child.date_of_birth, r.date),
                "group_id": r.child.group_id,
                "target": 1 if r.status == AttendanceStatus.PRESENT else 0
            }
            data.append(features)
        
        return pd.DataFrame(data)
    
    def _calculate_age(self, dob: date, at_date: date) -> int:
        return at_date.year - dob.year - ((at_date.month, at_date.day) < (dob.month, dob.day))
    
    def train_model(self) -> bool:
        """Обучить модель"""
        print("Обучение модели XGBoost")
        df = self.prepare_data()
        
        if len(df) < 10:
            print("⚠️ Недостаточно данных")
            return False
        
        X = df.drop("target", axis=1)
        y = df["target"]
        
        self.model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.1,
            random_state=42,
            eval_metric='logloss'
        )
        
        self.model.fit(X, y)
        
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        self.model.save_model(MODEL_PATH)
        print(f" Модель сохранена")
        return True
    
    def load_model(self) -> bool:
        """Загрузить модель"""
        if os.path.exists(MODEL_PATH):
            self.model = xgb.XGBClassifier()
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
        
        if not children:
            return {"error": "Нет активных детей"}
        
        X_pred = []
        for child in children:
            features = {
                "weekday": target_date.weekday(),
                "month": target_date.month,
                "is_monday": 1 if target_date.weekday() == 0 else 0,
                "is_friday": 1 if target_date.weekday() == 4 else 0,
                "is_winter": 1 if target_date.month in [12, 1, 2] else 0,
                "child_age": self._calculate_age(child.date_of_birth, target_date),
                "group_id": child.group_id
            }
            X_pred.append(features)
        
        X_df = pd.DataFrame(X_pred)
        predictions = self.model.predict(X_df)
        
        expected_count = int(sum(predictions))
        total = len(children)
        rate = (expected_count / total * 100) if total > 0 else 0
        
        risk = "low" if rate >= 85 else "medium" if rate >= 70 else "high"
        
        return {
            "group_id": group_id,
            "prediction_date": target_date.isoformat(),
            "expected_attendance": expected_count,
            "total_children": total,
            "attendance_rate": round(rate, 2),
            "risk_level": risk,
            "model_type": "XGBoost Classifier"
        }