from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date, datetime
from typing import Optional
from app.database import get_db
from app.models import User, Group
from app.routers.auth import get_current_user_from_token
from app.ai_module.schemas import AIPredictionResponse
from app.ai_module.models import AttendancePredictor, BudgetPredictor, RiskAnalyzer

router = APIRouter(prefix="/ai", tags=["AI Прогнозирование"])

@router.get("/predictions/group/{group_id}", response_model=AIPredictionResponse)
async def get_ai_predictions(
    group_id: int,
    target_month: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """AI прогноз посещаемости и бюджета для группы"""
    # Проверка доступа
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")
    
    if current_user.role.value == "teacher":
        if group.teacher_id != current_user.id:
            raise HTTPException(status_code=403, detail="Нет доступа к этой группе")
    
    # Целевой месяц
    if not target_month:
        today = datetime.utcnow().date()
        if today.month == 12:
            target_month = date(today.year + 1, 1, 1)
        else:
            target_month = date(today.year, today.month + 1, 1)
    
    # Инициализация моделей
    attendance_predictor = AttendancePredictor()
    budget_predictor = BudgetPredictor(daily_rate=500.0)
    risk_analyzer = RiskAnalyzer()
    
    # Прогноз бюджета
    budget_data = budget_predictor.predict_monthly_revenue(
        group_id, db, target_month, attendance_predictor
    )
    
    # Формирование прогнозов
    predictions = []
    for pred in budget_data["predictions"]:
        predictions.append({
            "child_id": pred["child_id"],
            "child_name": pred["child_name"],
            "predicted_days": pred["predicted_days"],
            "confidence": pred["confidence"],
            "risk_level": pred["risk_level"],
            "patterns": pred["patterns"]
        })
    
    # Анализ рисков
    risk_alerts = risk_analyzer.identify_at_risk_children(
        group_id, db, attendance_predictor
    )
    
    return {
        "predictions": predictions,
        "budget_forecast": {
            "month": target_month,
            "total_predicted_revenue": budget_data["total_revenue"],
            "total_children": budget_data["total_children"],
            "average_attendance": budget_data["average_attendance"],
            "confidence": budget_data["confidence"],
            "breakdown": predictions
        },
        "risk_alerts": risk_alerts,
        "generated_at": datetime.utcnow().date(),
        "model_version": "1.0.0"
    }

@router.get("/predictions/child/{child_id}")
async def get_child_attendance_prediction(
    child_id: int,
    target_month: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """Прогноз посещаемости для конкретного ребенка"""
    from app.models import Child
    
    child = db.query(Child).filter(Child.id == child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Ребенок не найден")
    
    # Проверка доступа
    if current_user.role.value == "teacher":
        group = db.query(Group).filter(Group.id == child.group_id).first()
        if group and group.teacher_id != current_user.id:
            raise HTTPException(status_code=403, detail="Нет доступа")
    
    if not target_month:
        today = datetime.utcnow().date()
        if today.month == 12:
            target_month = date(today.year + 1, 1, 1)
        else:
            target_month = date(today.year, today.month + 1, 1)
    
    predictor = AttendancePredictor()
    prediction = predictor.predict_next_month(child_id, db, target_month)
    
    return {
        "child_id": child_id,
        "child_name": child.full_name,
        "target_month": target_month,
        **prediction
    }

@router.get("/risks/group/{group_id}")
async def get_group_risk_analysis(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """Анализ рисков для группы"""
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")
    
    if current_user.role.value == "teacher":
        if group.teacher_id != current_user.id:
            raise HTTPException(status_code=403, detail="Нет доступа")
    
    attendance_predictor = AttendancePredictor()
    risk_analyzer = RiskAnalyzer()
    
    alerts = risk_analyzer.identify_at_risk_children(
        group_id, db, attendance_predictor
    )
    
    return {
        "group_id": group_id,
        "group_name": group.name,
        "total_alerts": len(alerts),
        "alerts": alerts,
        "generated_at": datetime.utcnow().date()
    }