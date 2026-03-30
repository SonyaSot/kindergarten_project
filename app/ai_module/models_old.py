import numpy as np
from datetime import datetime, timedelta, date
from typing import List, Dict, Tuple
from sqlalchemy.orm import Session
from app.models import Attendance, Child, Payment, AttendanceStatus

# модель для прогнозирования посещаемости
class AttendancePredictor:
        
    def __init__(self):
        self.seasonal_weights = {
            1: 0.7, 2: 0.75, 3: 0.8, 4: 0.85, 5: 0.82, 6: 0.7,
            7: 0.65, 8: 0.6, 9: 0.85, 10: 0.8, 11: 0.75, 12: 0.7,
        }
    
    #Расчет исторической посещаемости
    def calculate_historical_attendance(
        self, 
        child_id: int, 
        db: Session,
        months_back: int = 6
    ) -> Tuple[float, Dict]:
        
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=months_back * 30)
        
        records = db.query(Attendance).filter(
            Attendance.child_id == child_id,
            Attendance.date >= start_date,
            Attendance.date <= end_date
        ).all()
        
        if not records:
            return 0.8, {}
        
        total_days = len(records)
        present_days = sum(1 for r in records if r.status == AttendanceStatus.PRESENT)
        sick_days = sum(1 for r in records if r.status == AttendanceStatus.SICK)
        
        attendance_rate = present_days / total_days if total_days > 0 else 0.8
        
        patterns = {
            "attendance_rate": attendance_rate,
            "sick_rate": sick_days / total_days if total_days > 0 else 0,
            "total_records": total_days
        }
        
        return attendance_rate, patterns
    
    #Прогноз посещаемости на следующий месяц
    def predict_next_month(
        self,
        child_id: int,
        db: Session,
        target_month: date
    ) -> Dict:
        
        base_rate, patterns = self.calculate_historical_attendance(child_id, db)
        seasonal_factor = self.seasonal_weights.get(target_month.month, 0.8)
        predicted_rate = base_rate * 0.7 + seasonal_factor * 0.3
        
        import calendar
        working_days = calendar.monthrange(target_month.year, target_month.month)[1]
        working_days = int(working_days * 0.7)
        predicted_days = int(working_days * predicted_rate)
        
        if predicted_rate < 0.6:
            risk_level = "high"
        elif predicted_rate < 0.75:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        confidence = min(0.95, 0.5 + (patterns.get("total_records", 0) / 100))
        
        return {
            "predicted_days": max(1, predicted_days),
            "predicted_rate": round(predicted_rate, 2),
            "confidence": round(confidence, 2),
            "risk_level": risk_level,
            "patterns": patterns
        }

#Прогнозирование бюджета

class BudgetPredictor:
       
    def __init__(self, daily_rate: float = 500.0):
        self.daily_rate = daily_rate
    
    #Прогноз выручки за месяц
    def predict_monthly_revenue(
        self,
        group_id: int,
        db: Session,
        target_month: date,
        attendance_predictor: AttendancePredictor
    ) -> Dict:
        
        from app.models import Child
        
        children = db.query(Child).filter(
            Child.group_id == group_id,
            Child.is_active == True
        ).all()
        
        predictions = []
        total_revenue = 0.0
        
        for child in children:
            prediction = attendance_predictor.predict_next_month(
                child.id, db, target_month
            )
            predicted_amount = prediction["predicted_days"] * self.daily_rate
            total_revenue += predicted_amount
            
            predictions.append({
                "child_id": child.id,
                "child_name": child.full_name,
                "predicted_days": prediction["predicted_days"],
                "confidence": prediction["confidence"],
                "risk_level": prediction["risk_level"],
                "patterns": prediction["patterns"]
            })
        
        avg_attendance = sum(p["predicted_days"] for p in predictions) / len(children) if children else 0
        
        return {
            "total_revenue": round(total_revenue, 2),
            "total_children": len(children),
            "average_attendance": round(avg_attendance, 1),
            "predictions": predictions,
            "confidence": round(sum(p["confidence"] for p in predictions) / len(predictions), 2) if predictions else 0
        }
 
 #Анализ рисков
class RiskAnalyzer:
      
    def identify_at_risk_children(
        self,
        group_id: int,
        db: Session,
        attendance_predictor: AttendancePredictor
    ) -> List[Dict]:
        #Выявление детей в группе риска
        from app.models import Child
        
        children = db.query(Child).filter(
            Child.group_id == group_id,
            Child.is_active == True
        ).all()
        
        alerts = []
        
        for child in children:
            attendance_rate, patterns = attendance_predictor.calculate_historical_attendance(
                child.id, db
            )
            sick_rate = patterns.get("sick_rate", 0)
            
            if attendance_rate < 0.6:
                alerts.append({
                    "child_id": child.id,
                    "child_name": child.full_name,
                    "risk_type": "frequent_absence",
                    "risk_score": round(1 - attendance_rate, 2),
                    "recommendation": "Рекомендуется связаться с родителями для выяснения причин частых отсутствий",
                    "historical_data": {
                        "attendance_rate": attendance_rate,
                        "total_days": patterns.get("total_records", 0)
                    }
                })
            elif sick_rate > 0.3:
                alerts.append({
                    "child_id": child.id,
                    "child_name": child.full_name,
                    "risk_type": "illness_pattern",
                    "risk_score": round(sick_rate, 2),
                    "recommendation": "Частые заболевания. Рекомендуется консультация медицинского работника",
                    "historical_data": {
                        "sick_rate": sick_rate,
                        "total_days": patterns.get("total_records", 0)
                    }
                })
        
        return alerts