from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date, timedelta  # ← ДОБАВЛЕНО: timedelta

from app.database import get_db
from app.models import User, UserRole  # ← ДОБАВЛЕНО: UserRole
from app.routers.auth import get_current_user_from_token
from app.ai_module.xgb_service import XGBPredictor
from app.ai_module.payment_predictor import PaymentPredictor

router = APIRouter(prefix="/ai", tags=["AI Прогнозы"])

@router.get("/predictions/group/{group_id}")
async def predict_group_attendance(
    group_id: int = Path(..., description="ID группы"),
    target_date: Optional[date] = Query(None, description="Дата прогноза"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """Прогноз посещаемости на основе XGBoost"""
    if target_date is None:
        target_date = date.today() + timedelta(days=1)
    
    predictor = XGBPredictor(db)
    return predictor.predict_group(group_id, target_date)

@router.post("/train")
async def train_model_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """Переобучить модель ИИ. Доступно только администраторам."""
    
    # ИСПРАВЛЕНО: сравниваем с UserRole.ADMIN
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Только администраторы могут обучать модель")
    
    predictor = XGBPredictor(db)
    success = predictor.train_model()
    
    if success:
        return {"message": "Модель успешно переобучена"}
    else:
        raise HTTPException(status_code=500, detail="Недостаточно данных для обучения")

@router.post("/payments/train")
async def train_payment_prediction_model(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """Переобучить модель AI прогноза оплат. Только для админов."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Только администраторы могут обучать модель")
    
    predictor = PaymentPredictor(db)
    success = predictor.train_model()
    
    if success:
        return {"message": "Модель прогноза оплат успешно обучена"}
    else:
        raise HTTPException(status_code=500, detail="Недостаточно данных для обучения")

@router.get("/payments/predict/group/{group_id}")
async def predict_group_payments(
    group_id: int = Path(..., description="ID группы"),
    target_month: Optional[date] = Query(None, description="Месяц прогноза"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """AI прогноз поступлений оплат для группы."""
    if current_user.role.value not in ["admin", "accountant"]:
        raise HTTPException(status_code=403, detail="Только администратор или бухгалтер")
    
    predictor = PaymentPredictor(db)
    return predictor.predict_payment(group_id, target_month)